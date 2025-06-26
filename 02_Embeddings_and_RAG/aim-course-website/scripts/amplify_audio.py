#!/usr/bin/env python3
"""
Amplify audio volume by 2x using ffmpeg
"""

import subprocess
import os
from pathlib import Path

def amplify_audio(input_file, output_file, volume_multiplier=2.0):
    """Amplify audio volume using ffmpeg"""
    try:
        # Check if ffmpeg is available
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        
        # Amplify the audio
        cmd = [
            "ffmpeg", "-y",  # Overwrite output
            "-i", input_file,
            "-filter:a", f"volume={volume_multiplier}",
            output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Audio amplified by {volume_multiplier}x and saved to: {output_file}")
            return True
        else:
            print(f"Error amplifying audio: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError:
        print("ffmpeg not found. Falling back to web-based solution...")
        # For web environments, we'll handle volume client-side
        return False

if __name__ == "__main__":
    input_path = "../static/audio/assignment2_walkthrough.mp3"
    output_path = "../static/audio/assignment2_walkthrough_amplified.mp3"
    
    if amplify_audio(input_path, output_path):
        # Replace original with amplified version
        os.rename(output_path, input_path)
        print("✓ Original audio replaced with amplified version")
    else:
        print("⚠️ Could not amplify audio server-side. Will handle volume client-side.")