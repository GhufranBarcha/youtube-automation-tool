# Script to Video Endpoint

## Overview
The new `/async_script_to_video` endpoint processes a complete script-to-video workflow internally, eliminating the need for external n8n workflows.

## Features
- **Script Splitting**: Automatically splits long scripts into manageable chunks (max 10,000 characters)
- **Gemini TTS Integration**: Generates high-quality audio using Google's Gemini TTS API
- **Audio Merging**: Combines multiple audio chunks into a single file
- **Video Creation**: Creates final video with image and merged audio
- **Async Processing**: Non-blocking background processing with status polling
- **Quality Options**: Three quality levels (test, medium, best)

## Endpoint Details

### POST `/async_script_to_video`

**Parameters:**
- `script` (string): The complete script text
- `image` (file): Image file for the video
- `api_key` (string): Gemini API key for TTS
- `quality` (string, optional): Quality level - "test", "medium", or "best" (default: "medium")

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "queued",
  "check_url": "/status/{task_id}",
  "download_url": "/download/{task_id}",
  "quality": "medium"
}
```

## Quality Settings

| Quality | Preset | CRF | Audio Bitrate | Video Filter |
|---------|--------|-----|---------------|--------------|
| test    | ultrafast | 28 | 128k | 480p, 15fps |
| medium  | medium    | 23 | 192k | 720p, 30fps |
| best    | slow      | 18 | 320k | 1440p, 30fps |

## Usage Example

```python
import requests

# Prepare the request
script = "Your complete script text here..."
api_key = "your-gemini-api-key"

files = {
    "image": ("image.png", open("image.png", "rb"), "image/png")
}

data = {
    "script": script,
    "api_key": api_key,
    "quality": "medium"
}

# Make the request
response = requests.post(
    "http://localhost:8000/async_script_to_video",
    data=data,
    files=files
)

result = response.json()
task_id = result["task_id"]

# Poll for completion
while True:
    status_response = requests.get(f"http://localhost:8000/status/{task_id}")
    status_data = status_response.json()
    
    if status_data["status"] == "completed":
        # Download the video
        download_response = requests.get(f"http://localhost:8000/download/{task_id}")
        with open("output_video.mp4", "wb") as f:
            f.write(download_response.content)
        break
    elif status_data["status"] == "failed":
        print(f"Processing failed: {status_data.get('error', 'Unknown error')}")
        break
    
    time.sleep(5)  # Wait 5 seconds before next check
```

## Process Flow

1. **Script Splitting**: The script is split into chunks based on paragraph boundaries and character limits
2. **Audio Generation**: Each chunk is sent to Gemini TTS API to generate audio
3. **Audio Merging**: All audio chunks are merged into a single WAV file
4. **Video Creation**: FFmpeg combines the image and merged audio into the final video
5. **Cleanup**: Temporary files are removed after processing

## Error Handling

The endpoint includes comprehensive error handling:
- API key validation
- Script processing errors
- Audio generation failures
- Video creation errors
- Automatic cleanup of temporary files

## Dependencies

- FastAPI
- FFmpeg (for video processing)
- requests (for Gemini API calls)
- asyncio (for async processing)

## Notes

- The endpoint uses the same task management system as other async endpoints
- All processing happens in the background
- Status can be checked using the existing `/status/{task_id}` endpoint
- Videos can be downloaded using the existing `/download/{task_id}` endpoint
- Temporary files are automatically cleaned up after processing
