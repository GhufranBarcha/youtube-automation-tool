from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import subprocess
import os
import uuid
import json
import asyncio
from datetime import datetime
from typing import Dict, Optional

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
        "preset": "slow",
        "crf": 18,
        "audio_bitrate": "320k",
        "video_filter": "scale=-2:1080,fps=60"
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

# Keep original synchronous endpoints for backward compatibility
@app.post("/test_quality_video")
async def test_quality_video(image: UploadFile = File(...), audio: UploadFile = File(...)):
    """
    Creates a low-quality video for fast testing purposes.
    Uses minimal settings for quick processing.
    """
    uid = str(uuid.uuid4())
    image_path = f"/tmp/{uid}_{image.filename}"
    audio_path = f"/tmp/{uid}_{audio.filename}"
    video_path = f"/tmp/{uid}_output.mp4"

    # Save uploads
    with open(image_path, "wb") as f:
        f.write(await image.read())
    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    # FFmpeg command for test quality (fast, low quality)
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "ultrafast",     # fastest encoding
        "-crf", "28",               # lower quality, smaller file
        "-c:a", "aac",
        "-b:a", "128k",            # lower audio bitrate
        "-shortest",
        "-vf", "scale=-2:480,fps=15",  # 480p, 15 FPS for speed
        video_path
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr.decode()}

    # Return the generated video file directly
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename="test_video.mp4"
    )


@app.post("/medium_quality_video")
async def medium_quality_video(image: UploadFile = File(...), audio: UploadFile = File(...)):
    """
    Creates a medium-quality video optimized for YouTube uploads.
    Balanced quality and file size for regular YouTube content.
    """
    uid = str(uuid.uuid4())
    image_path = f"/tmp/{uid}_{image.filename}"
    audio_path = f"/tmp/{uid}_{audio.filename}"
    video_path = f"/tmp/{uid}_output.mp4"

    # Save uploads
    with open(image_path, "wb") as f:
        f.write(await image.read())
    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    # FFmpeg command for medium quality (YouTube optimized)
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-preset", "medium",       # balanced encoding speed/quality
        "-crf", "23",              # good quality (YouTube recommended range)
        "-c:a", "aac",
        "-b:a", "192k",           # good audio quality
        "-shortest",
        "-vf", "scale=-2:720,fps=30",  # 720p HD, 30 FPS
        video_path
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr.decode()}

    # Return the generated video file directly
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename="medium_quality_video.mp4"
    )

@app.post("/best_quality_video")
async def best_quality_video(image: UploadFile = File(...), audio: UploadFile = File(...)):
    """
    Creates the highest quality video for premium YouTube content.
    Uses maximum quality settings for professional uploads.
    """
    uid = str(uuid.uuid4())
    image_path = f"/tmp/{uid}_{image.filename}"
    audio_path = f"/tmp/{uid}_{audio.filename}"
    video_path = f"/tmp/{uid}_output.mp4"

    # Save uploads
    with open(image_path, "wb") as f:
        f.write(await image.read())
    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    # FFmpeg command for best quality (premium YouTube content)
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-preset", "slow",         # best compression and quality
        "-crf", "18",              # visually lossless quality
        "-c:a", "aac",
        "-b:a", "320k",           # maximum audio quality
        "-shortest",
        "-vf", "scale=-2:1080,fps=60",  # Full HD, 60 FPS for smooth playback
        video_path
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr.decode()}

    # Return the generated video file directly
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename="best_quality_video.mp4"
    )