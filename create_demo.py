#!/usr/bin/env python3
"""
Create demo screenshots/GIFs for MemScreen promotion
"""

import subprocess
import time
import os
from datetime import datetime

def run_command(cmd):
    """Run shell command"""
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def capture_demo_screenshots():
    """Capture screenshots of key features"""

    print("🎬 Creating MemScreen Demo Assets")
    print("=" * 50)

    # Instructions for manual capture
    instructions = """
    📸 Demo Screenshot Guide:

    1. Start MemScreen: python start_kivy.py

    2. Capture these screens (using Cmd+Shift+4):

       SCREEN 1 - Recording Tab:
       - Show the recording preview
       - Status: "Ready"
       - Duration: 60s, Interval: 2.0s
       - Save as: demo_recording.png

    SCREEN 2 - Videos Timeline (MOST IMPORTANT!):
       - Show timeline with 3-5 video markers
       - Purple dots on timeline
       - "Timeline - Click a dot to play" title
       - Save as: demo_timeline.png

    SCREEN 3 - Video Player:
       - Show a video playing
       - Progress bar with position
       - Orange play indicator on timeline
       - Save as: demo_player.png

    SCREEN 4 - AI Chat:
       - Show a conversation
       - User question + AI response
       - Save as: demo_chat.png

    3. Optimize screenshots:
       - Size: 1200x800px
       - Format: PNG
       - File size: <500KB each

    4. Create GIF (optional):
       Use ffmpeg or online tool:
       - Duration: 15-20 seconds
       - Show: Timeline click → Video plays → AI asks about it
       - Size: 1200x800, <5MB

    Recommended tools:
    - macOS: Built-in screenshot (Cmd+Shift+4)
    - GIF: https://www.gifski.com/ or https://ezgif.com/
    - Optimization: https://squoosh.app/
    """

    print(instructions)

    # Create demo assets directory
    demo_dir = "assets/demo"
    os.makedirs(demo_dir, exist_ok=True)
    print(f"\n✅ Created directory: {demo_dir}/")
    print("Save your screenshots there!")

    # Create a simple demo script template
    demo_script = """# MemScreen Demo Script

## Timeline Feature Demo (15-20 seconds)

1. **Open Videos tab** (2s)
   - Show "Found X recordings"

2. **Scroll timeline** (3s)
   - Show purple markers on timeline
   - Highlight the timeline navigation

3. **Click a marker** (2s)
   - Click on a purple dot

4. **Video plays** (5s)
   - Show playback
   - Orange indicator moves on timeline

5. **Back to chat** (3s)
   - Switch to AI Chat
   - Ask: "What did I work on yesterday?"

## AI Chat Demo (10-15 seconds)

1. **Type question** (3s)
   - "Show me the code I wrote yesterday"

2. **AI responds** (5s)
   - Show relevant video/memory

3. **Play result** (5s)
   - Click to view

## Screen Recording Demo (10 seconds)

1. **Start recording** (3s)
   - Click Start Recording

2. **Show progress** (5s)
   - Frame count increasing
   - Time elapsed

3. **Stop & save** (2s)
   - Auto-save message
"""

    with open(f"{demo_dir}/demo_script.md", "w") as f:
        f.write(demo_script)

    print(f"✅ Created demo script: {demo_dir}/demo_script.md")
    print("\n📝 Next steps:")
    print("1. Follow the screenshot guide above")
    print("2. Save images to assets/demo/")
    print("3. Run: python add_demo_to_readme.py")

def create_readme_update_script():
    """Create script to update README with demo images"""

    script = '''#!/usr/bin/env python3
"""
Update README with demo images
"""

README_UPDATE = '''
## 🎬 Demo

### Timeline Navigation

<img src="assets/demo/demo_timeline.png" width="800"/>

### AI-Powered Search

<img src="assets/demo/demo_chat.png" width="800"/>

### Screen Recording

<img src="assets/demo/demo_recording.png" width="800"/>

### Video Playback

<img src="assets/demo/demo_player.png" width="800"/>
'''

# Add this section after "Interface Preview" section in README
print("Add the following to README.md:")
print(README_UPDATE)
'''

    with open("add_demo_to_readme.py", "w") as f:
        f.write(script)

    print("✅ Created README update script: add_demo_to_readme.py")

if __name__ == "__main__":
    capture_demo_screenshots()
    create_readme_update_script()
    print("\n" + "="*50)
    print("🎉 Demo setup complete!")
    print("Follow the instructions above to create your demo assets")
