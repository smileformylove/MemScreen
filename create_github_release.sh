#!/bin/bash
# MemScreen GitHub Release 创建脚本

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

VERSION="0.4.1"
FILE="dist/MemScreen-${VERSION}-macos.zip"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      MemScreen GitHub Release 创建工具                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查文件是否存在
if [ ! -f "$FILE" ]; then
    echo -e "${RED}❌ 文件不存在: $FILE${NC}"
    echo -e "${YELLOW}请先运行 ./build_macos.sh 构建应用${NC}"
    exit 1
fi

FILE_SIZE=$(ls -lh "$FILE" | awk '{print $5}')
echo -e "${GREEN}✅ 找到文件: $FILE (${FILE_SIZE})${NC}"
echo ""

# 检查是否安装了 gh CLI
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✅ GitHub CLI 已安装${NC}"
    echo ""
    echo -e "${YELLOW}正在创建 Release...${NC}"

    # 创建 Release
    gh release create "v${VERSION}" "$FILE" \
        --title "MemScreen v${VERSION} - macOS" \
        --notes "## 🎉 MemScreen v${VERSION} - macOS Release

**专为 macOS 用户优化**

### 📥 下载
- \`MemScreen-${VERSION}-macos.zip\`

### 🚀 快速安装
1. 下载并解压 \`MemScreen-${VERSION}-macos.zip\`
2. 将 \`MemScreen.app\` 拖到应用程序文件夹
3. 双击启动
4. 首次运行会自动检查并安装 Ollama

### 📋 系统要求
- macOS 10.15 (Catalina) 或更高版本
- 8GB RAM 最低（16GB 推荐）
- 5GB 可用空间

### 📚 更多信息
- 完整文档: https://github.com/smileformylove/MemScreen#readme
- 问题反馈: https://github.com/smileformylove/MemScreen/issues

---

**注意**: 此版本仅适用于 macOS。" \
        --discussion-category "announcements"

    echo ""
    echo -e "${GREEN}✅ Release 创建成功！${NC}"
    echo ""
    echo -e "${BLUE}查看 Release:${NC}"
    echo "   https://github.com/smileformylove/MemScreen/releases/tag/v${VERSION}"

else
    echo -e "${YELLOW}⚠️  GitHub CLI 未安装${NC}"
    echo ""
    echo -e "${BLUE}请手动创建 Release:${NC}"
    echo ""
    echo "1. 访问创建页面:"
    echo "   https://github.com/smileformylove/MemScreen/releases/new"
    echo ""
    echo "2. 填写信息:"
    echo "   • Tag: v${VERSION}"
    echo "   • Title: MemScreen v${VERSION} - macOS"
    echo ""
    echo "3. 上传文件:"
    echo "   拖拽文件: $FILE"
    echo ""
    echo "4. 点击 Publish release"
    echo ""
    echo -e "${YELLOW}💡 安装 GitHub CLI (可选):${NC}"
    echo "   brew install gh"
    echo "   gh auth login"
fi

echo ""
