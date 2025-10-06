#!/bin/bash
# 演示场景测试脚本

echo "运行 QwenGround 演示测试..."
echo ""

# 测试 1: 查找椅子
echo "测试 1: 查找椅子"
python qwenground_main.py \
    --input_type images \
    --input_path data/demo_scene/images \
    --query "the chair" \
    --device cpu \
    --output_dir ./outputs/demo_chair \
    --save_intermediate

echo ""
echo "测试完成！查看结果:"
echo "  cat ./outputs/demo_chair/final_result.json"
echo ""

# 可选: 更多测试
# python qwenground_main.py --input_type images --input_path data/demo_scene/images --query "the table" --device cpu --output_dir ./outputs/demo_table
# python qwenground_main.py --input_type images --input_path data/demo_scene/images --query "the lamp" --device cpu --output_dir ./outputs/demo_lamp
