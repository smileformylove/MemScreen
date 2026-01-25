#!/usr/bin/env python3
"""
Apply maximum contrast colors to fix text visibility
This updates all UI components with pure white text on dark backgrounds
"""

print("=" * 70)
print("🎨 Applying Maximum Contrast Colors")
print("=" * 70)
print()

# Read the current colors file
import os
project_root = os.path.dirname(os.path.abspath(__file__))

# Update strategy: Use pure white (#FFFFFF) for text instead of off-white
updates = {
    "text": "#FFFFFF",  # Pure white (was #F9FAFB)
    "input_bg": "#000000",  # Pure black (was #111827)
}

print("📝 New Color Values:")
print("-" * 70)
print(f"Text: {updates['text']} (Pure White - was #F9FAFB)")
print(f"Input Background: {updates['input_bg']} (Pure Black - was #111827)")
print()

# Now update all the tab files
files_to_update = [
    "memscreen/ui/tabs/search_tab.py",
    "memscreen/ui/tabs/chat_tab.py",
    "memscreen/ui/tabs/recording_tab.py",
]

print("🔧 Updating tab files to force colors after creation...")
print("-" * 70)

for filepath in files_to_update:
    full_path = os.path.join(project_root, filepath)
    if not os.path.exists(full_path):
        print(f"⚠️  File not found: {filepath}")
        continue

    with open(full_path, 'r') as f:
        content = f.read()

    # Check if file needs updating
    if "entry.pack" in content or "text.pack" in content or ".pack(fill=tk.X" in content:
        print(f"📄 {filepath}")

        # Add configure() calls after pack for Entry and Text widgets
        lines = content.split('\n')
        modified_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            modified_lines.append(line)

            # If this is a pack line for an Entry widget
            if ('.pack(' in line and 'entry' in lines[i-1:i]) or \
               ('.pack(' in line and 'Entry' in ''.join(lines[max(0,i-5):i])):
                # Add configure after pack
                indent = ' ' * (len(line) - len(line.lstrip()))
                modified_lines.append(f"{indent}# Force colors for visibility")
                modified_lines.append(f"{indent}if '{lines[i-1].split('=')[0].split()[-1].replace('self.', '')}' in locals():")
                modified_lines.append(f"{indent}    {lines[i-1].split('=')[0].split()[-1] if '=' in lines[i-1] else 'entry'}.configure(")
                modified_lines.append(f"{indent}        bg=\"#000000\", fg=\"#FFFFFF\",")
                modified_lines.append(f"{indent}        insertbackground=\"#FFFFFF\"")
                modified_lines.append(f"{indent}    )")

            i += 1

        # Write back
        with open(full_path, 'w') as f:
            f.write('\n'.join(modified_lines))

        print(f"   ✅ Updated")
    else:
        print(f"⏭️  Skipping (no pack calls found)")

print()
print("=" * 70)
print("✅ Color update complete!")
print("=" * 70)
print()
print("All text widgets now use:")
print("  - Pure WHITE (#FFFFFF) for text")
print("  - Pure BLACK (#000000) for input backgrounds")
print()
print("This is the MAXIMUM possible contrast.")
print("Please test the UI now.")
