#!/bin/bash

# ============================================================
# ARKitScenes 数据集下载脚本
# ============================================================
# 
# 注意：下载 ARKitScenes 数据需要先接受使用条款
# 
# 1. 访问: https://github.com/apple/ARKitScenes
# 2. 阅读并接受使用协议
# 3. 数据下载 URL 需要访问权限
#
# ============================================================

set -e  # 遇到错误时退出

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║          ARKitScenes 数据集下载                           ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
ARKITSCENES_DIR="../ARKitScenes"
DOWNLOAD_DIR="${ARKITSCENES_DIR}/data"

echo -e "${BLUE}配置:${NC}"
echo "  ARKitScenes 仓库: $ARKITSCENES_DIR"
echo "  数据下载目录: $DOWNLOAD_DIR"
echo ""

# 检查 ARKitScenes 仓库
if [ ! -d "$ARKITSCENES_DIR" ]; then
    echo -e "${RED}❌ 错误: 找不到 ARKitScenes 目录${NC}"
    echo "请先克隆仓库:"
    echo "  git clone https://github.com/apple/ARKitScenes.git ../ARKitScenes"
    exit 1
fi

cd "$ARKITSCENES_DIR"

echo -e "${YELLOW}⚠️  重要提示:${NC}"
echo ""
echo "ARKitScenes 数据集需要先接受使用协议才能下载。"
echo ""
echo "请按照以下步骤操作:"
echo ""
echo "1. 访问 ARKitScenes 项目页面:"
echo "   ${BLUE}https://github.com/apple/ARKitScenes${NC}"
echo ""
echo "2. 阅读并接受使用条款"
echo ""
echo "3. 下载数据的两种方式:"
echo ""
echo "   ${GREEN}方式 A: 使用官方脚本 (推荐用于完整数据集)${NC}"
echo "   cd ../ARKitScenes"
echo "   python3 download_data.py 3dod --video_id_csv threedod/3dod_train_val_splits.csv \\"
echo "       --download_dir ./data"
echo ""
echo "   ${GREEN}方式 B: 手动下载单个场景${NC}"
echo "   python3 download_data.py raw --split Validation --video_id 48458663 \\"
echo "       --download_dir ./data \\"
echo "       --raw_dataset_assets lowres_wide lowres_depth annotation mesh"
echo ""

echo ""
echo -e "${BLUE}推荐: 下载 1-2 个验证集场景用于快速测试${NC}"
echo ""
echo "示例命令 (下载 1 个场景):"
echo ""
cat << 'EOF'
cd ../ARKitScenes

# 下载第一个验证集场景 (约 200-500 MB)
python3 download_data.py raw --split Validation --video_id 48458663 \
    --download_dir ./data \
    --raw_dataset_assets lowres_wide lowres_depth annotation mesh lowres_wide.traj lowres_wide_intrinsics

# 或者下载多个场景
python3 download_data.py raw --split Validation --video_id 48458663 42445417 \
    --download_dir ./data \
    --raw_dataset_assets lowres_wide lowres_depth annotation mesh lowres_wide.traj lowres_wide_intrinsics
EOF

echo ""
echo -e "${GREEN}下载完成后，运行以下命令验证:${NC}"
echo ""
echo "  ls -lh ../ARKitScenes/data/Validation/"
echo "  find ../ARKitScenes/data -name '*.png' | head -5"
echo ""

echo -e "${YELLOW}如果遇到 403 错误:${NC}"
echo "  - 确认已接受 ARKitScenes 使用协议"
echo "  - 尝试使用 VPN 或不同网络"
echo "  - 联系 ARKitScenes 项目维护者"
echo ""

echo -e "${BLUE}快速测试选项:${NC}"
echo "如果下载困难，可以:"
echo "  1. 使用演示数据: python scripts/create_demo_data.py"
echo "  2. 使用自己的 RGB-D 视频或图像序列"
echo "  3. 使用其他公开数据集 (ScanNet, Replica 等)"
echo ""

echo "════════════════════════════════════════════════════════════"

