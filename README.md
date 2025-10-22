# YouTube Automation Tool

A FastAPI-based video processing service that creates YouTube-ready videos by combining images with audio files. Features asynchronous processing with task management and multiple quality presets.

## 🚀 Features

- **Multiple Quality Presets**: Test, Medium, and Best quality options
- **Asynchronous Processing**: Non-blocking video generation with task tracking
- **File Upload Support**: Direct file upload via multipart/form-data
- **Task Management**: JSON-based persistent task tracking
- **n8n Integration**: Perfect for workflow automation
- **Synchronous & Asynchronous Endpoints**: Both immediate and background processing options

## 📋 Requirements

- Python 3.8+
- FFmpeg installed on your system
- FastAPI
- uvicorn (for running the server)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd youtube-automation-tool
   ```

2. **Install dependencies**
   ```bash
   pip install fastapi uvicorn
   ```

3. **Install FFmpeg**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

4. **Run the server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 🎯 API Endpoints

### Async Endpoints (Recommended)

#### 1. Test Quality Video
```http
POST /async_test_quality_video
```
- **Purpose**: Fast testing with minimal quality
- **Settings**: 480p, 15 FPS, ultrafast encoding
- **Use case**: Quick testing and development

#### 2. Medium Quality Video
```http
POST /async_medium_quality_video
```
- **Purpose**: Regular YouTube uploads
- **Settings**: 720p, 30 FPS, balanced quality
- **Use case**: Standard YouTube content

#### 3. Best Quality Video
```http
POST /async_best_quality_video
```
- **Purpose**: Premium YouTube content
- **Settings**: 1080p, 60 FPS, maximum quality
- **Use case**: Professional YouTube uploads

### Synchronous Endpoints (Immediate Response)

#### 1. Test Quality Video (Sync)
```http
POST /test_quality_video
```

#### 2. Medium Quality Video (Sync)
```http
POST /medium_quality_video
```

#### 3. Best Quality Video (Sync)
```http
POST /best_quality_video
```

### Input Method

#### File Upload (multipart/form-data)
```bash
curl -X POST "http://localhost:8000/async_test_quality_video" \
  -F "image=@/path/to/image.jpg" \
  -F "audio=@/path/to/audio.mp3"
```

### Task Management

#### Check Task Status
```http
GET /status/{task_id}
```

**Response:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "completed",
  "file_path": "/tmp/abc123_output.mp4",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

#### Download Video
```http
GET /download/{task_id}
```

## 🔄 Task Status Flow

1. **`queued`** - Task created, waiting to start
2. **`in_progress`** - Video processing in progress
3. **`completed`** - Video ready for download
4. **`failed`** - Error occurred (check error field)

## 📊 Quality Presets Comparison

| Preset | Resolution | FPS | CRF | Audio Bitrate | Use Case |
|--------|------------|-----|-----|---------------|----------|
| Test | 480p | 15 | 28 | 128k | Fast testing |
| Medium | 720p | 30 | 23 | 192k | Regular YouTube |
| Best | 1080p | 60 | 18 | 320k | Premium content |

## 🤖 n8n Integration

### Workflow Pattern
```
1. HTTP Request → POST /async_test_quality_video
   ↓ (get task_id)
2. Wait 30 seconds
3. HTTP Request → GET /status/{task_id}
   ↓ (check status)
4. IF status != "completed" → Go to step 2
5. IF status == "completed" → HTTP Request → GET /download/{task_id}
```

### n8n HTTP Request Configuration

#### File Upload Mode
```json
{
  "method": "POST",
  "url": "http://localhost:8000/async_test_quality_video",
  "contentType": "multipart-form-data",
  "bodyParameters": {
    "image": [file],
    "audio": [file]
  }
}
```

#### Synchronous Endpoint Example
```json
{
  "method": "POST",
  "url": "http://localhost:8000/test_quality_video",
  "contentType": "multipart-form-data",
  "bodyParameters": {
    "image": [file],
    "audio": [file]
  }
}
```

## 📁 File Structure

```
youtube-automation-tool/
├── main.py              # FastAPI application
├── tasks.json           # Task persistence (auto-created)
├── README.md            # This file
└── __pycache__/         # Python cache
```

## 🛡️ Error Handling

- **Missing files**: 400 Bad Request  
- **Task not found**: 404 Not Found
- **Task not completed**: 400 Bad Request
- **Video file not found**: 404 Not Found
- **Processing timeouts**: Task marked as failed
- **FFmpeg errors**: Detailed error messages

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Custom task file location (default: tasks.json)
# The TASKS_FILE variable is hardcoded in main.py as "tasks.json"
```

### FFmpeg Settings
The tool uses optimized FFmpeg settings for each quality preset:
- **Test**: `ultrafast` preset for speed
- **Medium**: `medium` preset for balance
- **Best**: `slow` preset for quality

## 📈 Performance

- **Test Quality**: ~30 seconds for 5-minute audio
- **Medium Quality**: ~2-3 minutes for 5-minute audio  
- **Best Quality**: ~5-10 minutes for 5-minute audio

*Times may vary based on hardware and file sizes*

## 🚨 Troubleshooting

### Common Issues

1. **FFmpeg not found**
   ```bash
   # Install FFmpeg
   sudo apt install ffmpeg  # Ubuntu/Debian
   brew install ffmpeg     # macOS
   ```

2. **Permission denied on /tmp**
   ```bash
   # Check /tmp permissions
   ls -la /tmp
   ```

3. **Large file timeouts**
   - Increase n8n timeout settings
   - Use async endpoints for long processing

### Logs
Check server logs for detailed error information:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review server logs
3. Open an issue on GitHub

---

**Made with ❤️ for YouTube creators**
