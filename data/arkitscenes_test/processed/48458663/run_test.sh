#!/bin/bash
# 测试场景: 48458663

cd ../..

echo "运行 QwenGround 测试: 48458663"
echo "查询: the chair"

python qwenground_main.py \
    --input_type images \
    --input_path data/arkitscenes_test/processed/48458663/images \
    --query "the chair" \
    --device cpu \
    --output_dir ./outputs/arkitscenes_test_48458663 \
    --save_intermediate

echo "测试完成！查看结果："
echo "  ls outputs/arkitscenes_test_48458663/"
