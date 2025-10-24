from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import subprocess
import os
import uuid
import json
import asyncio
import re
import base64
import requests
from datetime import datetime
from typing import Dict, Optional, List

app = FastAPI()

# JSON file for task persistence
TASKS_FILE = "tasks.json"

def load_tasks() -> Dict:
    """Load tasks from JSON file"""
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

def save_tasks(tasks: Dict):
    """Save tasks to JSON file"""
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
    except Exception as e:
        print(f"Error saving tasks: {e}")

def update_task_status(task_id: str, status: str, error: str = None, file_path: str = None):
    """Update task status in JSON file"""
    tasks = load_tasks()
    
    if task_id not in tasks:
        tasks[task_id] = {
            "created_at": datetime.now().isoformat(),
            "status": "queued"
        }
    
    # Only update fields that have values
    update_data = {
        "status": status,
        "updated_at": datetime.now().isoformat()
    }
    
    if error is not None:
        update_data["error"] = error
    
    if file_path is not None:
        update_data["file_path"] = file_path
    
    tasks[task_id].update(update_data)
    save_tasks(tasks)

async def process_video_background(task_id: str, image_path: str, audio_path: str, video_path: str, quality_settings: Dict):
    """Process video in background and update task status"""
    try:
        # Update status to in_progress
        update_task_status(task_id, "in_progress")
        
        # Run FFmpeg in a separate thread
        def run_ffmpeg():
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", image_path,
                "-i", audio_path,
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-preset", quality_settings["preset"],
                "-crf", str(quality_settings["crf"]),
                "-c:a", "aac",
                "-b:a", quality_settings["audio_bitrate"],
                "-shortest",
                "-vf", quality_settings["video_filter"],
                video_path
            ]
            
            return subprocess.run(
                cmd, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
        # Run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_ffmpeg)
        
        # Update status to completed with file path
        update_task_status(task_id, "completed", file_path=video_path)
        
    except subprocess.TimeoutExpired:
        update_task_status(task_id, "failed", error="Processing timeout)")
    except subprocess.CalledProcessError as e:
        update_task_status(task_id, "failed", error=f"FFmpeg error: {e.stderr.decode()}")
    except Exception as e:
        update_task_status(task_id, "failed", error=f"Unexpected error: {str(e)}")
    finally:
        # Cleanup input files
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except:
            pass

def split_script_into_chunks(script: str, max_chars: int = 10000) -> List[str]:
    """Split script into chunks based on the n8n workflow logic"""
    # Split by paragraphs (double newline)
    paragraphs = [p for p in script.split('\n\n') if p.strip()]
    
    chunks = []
    current_chunk = ''
    
    for para in paragraphs:
        trimmed_para = para.strip()
        test_chunk = current_chunk + '\n\n' + trimmed_para if current_chunk else trimmed_para
        
        # If adding this paragraph exceeds limit and we have content, save current chunk
        if len(test_chunk) > max_chars and len(current_chunk) > 0:
            chunks.append(current_chunk.strip())
            current_chunk = trimmed_para
        # If single paragraph exceeds limit, split by sentences
        elif len(trimmed_para) > max_chars and len(current_chunk) == 0:
            sentences = re.findall(r'[^.!?]+[.!?]+', trimmed_para) or [trimmed_para]
            sentence_chunk = ''
            
            for sentence in sentences:
                test_sentence = sentence_chunk + ' ' + sentence if sentence_chunk else sentence
                
                if len(test_sentence) > max_chars and len(sentence_chunk) > 0:
                    chunks.append(sentence_chunk.strip())
                    sentence_chunk = sentence
                else:
                    sentence_chunk = test_sentence
            current_chunk = sentence_chunk
        else:
            current_chunk = test_chunk
    
    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

async def generate_audio_with_gemini(text: str, api_key: str) -> bytes:
    """Generate audio using Gemini TTS API"""
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": text
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["audio"],
            "temperature": 1,
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": "Zephyr"
                    }
                }
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    result = response.json()
    audio_data = result["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    
    return base64.b64decode(audio_data)

async def merge_audio_files(audio_files: List[bytes], output_path: str):
    """Merge multiple audio files into one"""
    # Save individual PCM files
    pcm_files = []
    for i, audio_data in enumerate(audio_files):
        pcm_path = f"/tmp/audio_chunk_{i}.pcm"
        with open(pcm_path, "wb") as f:
            f.write(audio_data)
        pcm_files.append(pcm_path)
    
    # Create a temporary concatenated PCM file
    temp_pcm_path = f"/tmp/temp_concatenated.pcm"
    with open(temp_pcm_path, "wb") as outfile:
        for pcm_file in pcm_files:
            with open(pcm_file, "rb") as infile:
                outfile.write(infile.read())
    
    # Convert PCM to WAV using FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-f", "s16le",
        "-ar", "24000",
        "-ac", "1",
        "-i", temp_pcm_path,
        output_path
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Cleanup PCM files
    for pcm_file in pcm_files:
        try:
            os.remove(pcm_file)
        except:
            pass
    try:
        os.remove(temp_pcm_path)
    except:
        pass

async def process_script_to_video_background(
    task_id: str, 
    script: str, 
    image_path: str, 
    api_key: str,
    quality_settings: Dict
):
    """Process script to video in background"""
    merged_audio_path = None
    try:
        # Update status to in_progress
        update_task_status(task_id, "in_progress")
        
        # Step 1: Split script into chunks
        chunks = split_script_into_chunks(script)
        
        # Step 2: Generate audio for each chunk
        audio_files = []
        for chunk in chunks:
            audio_data = await generate_audio_with_gemini(chunk, api_key)
            audio_files.append(audio_data)
        
        # Step 3: Merge all audio files
        merged_audio_path = f"/tmp/{task_id}_merged_audio.wav"
        await merge_audio_files(audio_files, merged_audio_path)
        
        # Step 4: Create video with image and merged audio
        video_path = f"/tmp/{task_id}_output.mp4"
        
        def run_ffmpeg():
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", image_path,
                "-i", merged_audio_path,
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-preset", quality_settings["preset"],
                "-crf", str(quality_settings["crf"]),
                "-c:a", "aac",
                "-b:a", quality_settings["audio_bitrate"],
                "-shortest",
                "-vf", quality_settings["video_filter"],
                video_path
            ]
            
            return subprocess.run(
                cmd, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_ffmpeg)
        
        # Update status to completed with file path
        update_task_status(task_id, "completed", file_path=video_path)
        
    except Exception as e:
        update_task_status(task_id, "failed", error=f"Processing error: {str(e)}")
    finally:
        # Cleanup input files
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
            if merged_audio_path and os.path.exists(merged_audio_path):
                os.remove(merged_audio_path)
        except:
            pass

# Async endpoints with task management
@app.post("/async_test_quality_video")
async def async_test_quality_video(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...), 
    audio: UploadFile = File(...)
):
    """Creates a low-quality video asynchronously for fast testing"""
    task_id = str(uuid.uuid4())
    
    # Save uploads
    image_path = f"/tmp/{task_id}_{image.filename}"
    audio_path = f"/tmp/{task_id}_{audio.filename}"
    video_path = f"/tmp/{task_id}_output.mp4"
    
    with open(image_path, "wb") as f:
        f.write(await image.read())
    with open(audio_path, "wb") as f:
        f.write(await audio.read())
    
    # Initialize task as queued
    update_task_status(task_id, "queued")
    
    # Quality settings for test quality
    quality_settings = {
        "preset": "ultrafast",
        "crf": 28,
        "audio_bitrate": "128k",
        "video_filter": "scale=-2:480,fps=15"
    }
    
    # Start background processing
    background_tasks.add_task(
        process_video_background, 
        task_id, image_path, audio_path, video_path, quality_settings
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "check_url": f"/status/{task_id}",
        "download_url": f"/download/{task_id}"
    }

@app.post("/async_medium_quality_video")
async def async_medium_quality_video(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...), 
    audio: UploadFile = File(...)
):
    """Creates a medium-quality video asynchronously for YouTube"""
    task_id = str(uuid.uuid4())
    
    # Save uploads
    image_path = f"/tmp/{task_id}_{image.filename}"
    audio_path = f"/tmp/{task_id}_{audio.filename}"
    video_path = f"/tmp/{task_id}_output.mp4"
    
    with open(image_path, "wb") as f:
        f.write(await image.read())
    with open(audio_path, "wb") as f:
        f.write(await audio.read())
    
    # Initialize task as queued
    update_task_status(task_id, "queued")
    
    # Quality settings for medium quality
    quality_settings = {
        "preset": "medium",
        "crf": 23,
        "audio_bitrate": "192k",
        "video_filter": "scale=-2:720,fps=30"
    }
    
    # Start background processing
    background_tasks.add_task(
        process_video_background, 
        task_id, image_path, audio_path, video_path, quality_settings
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "check_url": f"/status/{task_id}",
        "download_url": f"/download/{task_id}"
    }

@app.post("/async_best_quality_video")
async def async_best_quality_video(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...), 
    audio: UploadFile = File(...)
):
    """Creates the highest quality video asynchronously for premium YouTube content"""
    task_id = str(uuid.uuid4())
    
    # Save uploads
    image_path = f"/tmp/{task_id}_{image.filename}"
    audio_path = f"/tmp/{task_id}_{audio.filename}"
    video_path = f"/tmp/{task_id}_output.mp4"
    
    with open(image_path, "wb") as f:
        f.write(await image.read())
    with open(audio_path, "wb") as f:
        f.write(await audio.read())
    
    # Initialize task as queued
    update_task_status(task_id, "queued")
    
    # Quality settings for best quality
    quality_settings = {
        "preset": "slow",            # better quality per bitrate
        "crf": 18,                   # near-lossless
        "audio_bitrate": "320k",
        "video_filter": "scale=-2:1440,fps=30"
    }

    
    # Start background processing
    background_tasks.add_task(
        process_video_background, 
        task_id, image_path, audio_path, video_path, quality_settings
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "check_url": f"/status/{task_id}",
        "download_url": f"/download/{task_id}"
    }

@app.post("/async_script_to_video")
async def async_script_to_video(
    background_tasks: BackgroundTasks,
    script: str,
    image: UploadFile = File(...),
    api_key: str = None,
    quality: str = "medium"
):
    """
    Creates a video from a script and image using Gemini TTS.
    Processes the entire workflow: script splitting, audio generation, merging, and video creation.
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=400, detail="API key is required for Gemini TTS")
    
    task_id = str(uuid.uuid4())
    
    # Save image upload
    image_path = f"/tmp/{task_id}_{image.filename}"
    with open(image_path, "wb") as f:
        f.write(await image.read())
    
    # Initialize task as queued
    update_task_status(task_id, "queued")
    
    # Quality settings based on quality parameter
    quality_settings_map = {
        "test": {
            "preset": "ultrafast",
            "crf": 28,
            "audio_bitrate": "128k",
            "video_filter": "scale=-2:480,fps=15"
        },
        "medium": {
            "preset": "medium",
            "crf": 23,
            "audio_bitrate": "192k",
            "video_filter": "scale=-2:720,fps=30"
        },
        "best": {
            "preset": "slow",
            "crf": 18,
            "audio_bitrate": "320k",
            "video_filter": "scale=-2:1440,fps=30"
        }
    }
    
    quality_settings = quality_settings_map.get(quality, quality_settings_map["medium"])
    
    # Start background processing
    background_tasks.add_task(
        process_script_to_video_background, 
        task_id, script, image_path, api_key, quality_settings
    )
    
    return {
        "task_id": task_id,
        "status": "queued",
        "check_url": f"/status/{task_id}",
        "download_url": f"/download/{task_id}",
        "quality": quality
    }

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Check the status of a task"""
    tasks = load_tasks()
    
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    # Build response with only fields that have values
    response = {
        "task_id": task_id,
        "status": task["status"],
        "created_at": task["created_at"],
        "updated_at": task["updated_at"]
    }
    
    # Only include error if it exists
    if "error" in task and task["error"] is not None:
        response["error"] = task["error"]
    
    # Only include file_path if it exists
    if "file_path" in task and task["file_path"] is not None:
        response["file_path"] = task["file_path"]
    
    return response

@app.get("/download/{task_id}")
async def download_video(task_id: str):
    """Download the generated video file"""
    tasks = load_tasks()
    
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Task not completed. Current status: {task['status']}"
        )
    
    file_path = task.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=f"video_{task_id}.mp4"
    )
