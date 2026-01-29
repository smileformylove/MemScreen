#!/bin/bash
# Check GitHub Actions build status

echo "🔍 Checking MemScreen build status..."
echo ""

# Check recent tags
echo "📌 Recent tags:"
git tag -l | tail -5
echo ""

# Check if gh CLI is available
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI found"
    echo ""
    echo "🔨 Recent workflow runs:"
    gh run list --limit 5
    echo ""

    echo "📥 Latest releases:"
    gh release list --limit 5
    echo ""
else
    echo "⚠️  GitHub CLI not found"
    echo "Install with: brew install gh"
    echo ""
fi

echo "🌐 Links to check manually:"
echo "  Actions: https://github.com/smileformylove/MemScreen/actions"
echo "  Releases: https://github.com/smileformylove/MemScreen/releases"
echo "  Tags: https://github.com/smileformylove/MemScreen/tags"
echo ""

# Get latest tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -n "$LATEST_TAG" ]; then
    echo "🏷️  Latest tag: $LATEST_TAG"
    echo "   Release page: https://github.com/smileformylove/MemScreen/releases/tag/$LATEST_TAG"
fi
