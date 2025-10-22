from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import subprocess
import os
import uuid

app = FastAPI()

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