#!/usr/bin/env python3
"""
Test script for the new async_script_to_video endpoint
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on different port
API_KEY = "your-gemini-api-key-here"  # Replace with actual API key

def test_script_to_video():
    """Test the script to video endpoint"""
    
    # Sample script
    script = """
    Welcome to our YouTube channel! Today we're going to explore the fascinating world of artificial intelligence and machine learning.
    
    AI has revolutionized many industries, from healthcare to finance, and continues to shape our future in remarkable ways.
    
    Let's dive deep into understanding how these technologies work and their potential impact on society.
    """
    
    # Test data
    test_data = {
        "script": script,
        "api_key": API_KEY,
        "quality": "medium"
    }
    
    # Sample image file (you'll need to provide an actual image file)
    files = {
        "image": ("test_image.png", open("test_image.png", "rb"), "image/png")
    }
    
    try:
        # Make the request
        response = requests.post(
            f"{BASE_URL}/async_script_to_video",
            data=test_data,
            files=files
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            print(f"Task ID: {result['task_id']}")
            print(f"Status: {result['status']}")
            print(f"Check URL: {result['check_url']}")
            print(f"Download URL: {result['download_url']}")
            print(f"Quality: {result['quality']}")
            
            # Poll for completion
            task_id = result['task_id']
            check_url = f"{BASE_URL}/status/{task_id}"
            
            print("\n🔄 Polling for completion...")
            while True:
                status_response = requests.get(check_url)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"Current status: {status_data['status']}")
                    
                    if status_data['status'] == 'completed':
                        print("✅ Video processing completed!")
                        download_url = f"{BASE_URL}/download/{task_id}"
                        print(f"Download URL: {download_url}")
                        break
                    elif status_data['status'] == 'failed':
                        print("❌ Video processing failed!")
                        if 'error' in status_data:
                            print(f"Error: {status_data['error']}")
                        break
                    
                    # Wait before next check
                    import time
                    time.sleep(5)
                else:
                    print(f"❌ Error checking status: {status_response.status_code}")
                    break
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Close file if opened
        if 'files' in locals():
            files['image'][1].close()

if __name__ == "__main__":
    print("🧪 Testing async_script_to_video endpoint")
    print("=" * 50)
    test_script_to_video()
