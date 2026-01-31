# GitHub Social Preview Setup

This guide explains how to set up MemScreen's social preview on GitHub.

## What is Social Preview?

When someone shares your GitHub repository link on social media (Twitter, LinkedIn, etc.), GitHub displays a preview card with an image and description.

## Setup Instructions

### Method 1: Through GitHub UI (Recommended)

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Scroll down to **"Social preview"** section
4. Click **"Edit"**
5. Upload `assets/logo.png` as the social preview image
6. Save changes

### Method 2: Using GitHub API

Alternatively, you can use the GitHub REST API:

```bash
curl -X PATCH \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/smileformylove/MemScreen \
  -d '{"social_preview_image_path": "assets/logo.png"}'
```

## Recommended Image

- **File**: `assets/logo.png`
- **Size**: 280x280 pixels
- **Format**: PNG with transparency
- **Aspect Ratio**: 1:1 (square)

## Verify

After setting up, verify the preview:
1. Go to your repository
2. Share the URL on Twitter or LinkedIn
3. Check if the logo appears in the preview card

## Tips

- Use a high-quality image (at least 640x320 pixels for best results)
- Keep the image size under 10MB
- Use PNG or JPG format
- The image should represent your brand clearly

## Troubleshooting

**Image not showing up?**
- Clear your browser cache
- Wait a few minutes for GitHub to process the image
- Check the image URL is accessible

**Image looks blurry?**
- Use a higher resolution image
- Ensure the original image is at least 1280x640 pixels
