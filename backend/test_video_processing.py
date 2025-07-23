#!/usr/bin/env python3
"""
Test video processing capabilities
"""
import subprocess
import sys

def test_ffmpeg():
    """Test if ffmpeg is available"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ FFmpeg is installed")
            version_line = result.stdout.split('\n')[0]
            print(f"  Version: {version_line}")
            return True
        else:
            print("✗ FFmpeg is not installed")
            return False
    except FileNotFoundError:
        print("✗ FFmpeg is not installed")
        return False

def test_ffprobe():
    """Test if ffprobe is available"""
    try:
        result = subprocess.run(['ffprobe', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ FFprobe is installed")
            return True
        else:
            print("✗ FFprobe is not installed")
            return False
    except FileNotFoundError:
        print("✗ FFprobe is not installed")
        return False

def test_ffmpeg_python():
    """Test if ffmpeg-python module is available"""
    try:
        import ffmpeg
        print("✓ ffmpeg-python module is installed")
        return True
    except ImportError:
        print("✗ ffmpeg-python module is not installed")
        return False

def test_moviepy():
    """Test if moviepy is available"""
    try:
        from moviepy.editor import VideoFileClip
        print("✓ moviepy module is installed")
        return True
    except ImportError:
        print("✗ moviepy module is not installed")
        return False

def main():
    print("Testing video processing capabilities...")
    print("-" * 50)
    
    ffmpeg_ok = test_ffmpeg()
    ffprobe_ok = test_ffprobe()
    ffmpeg_python_ok = test_ffmpeg_python()
    moviepy_ok = test_moviepy()
    
    print("-" * 50)
    
    if ffmpeg_ok and ffprobe_ok and ffmpeg_python_ok:
        print("✓ All required components for ffmpeg-based processing are available")
    elif moviepy_ok:
        print("⚠ FFmpeg not fully available, but moviepy is installed as fallback")
    else:
        print("✗ No video processing capability available!")
        print("\nTo fix:")
        print("1. Install system ffmpeg: apt-get install ffmpeg")
        print("2. Install Python packages: pip install ffmpeg-python moviepy")
        sys.exit(1)

if __name__ == "__main__":
    main() 