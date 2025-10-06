#!/usr/bin/env python3
"""
准备单个 ARKitScenes 场景用于 QwenGround 测试
"""

import os
import sys
import json
import shutil
from pathlib import Path
from PIL import Image

def prepare_scene(scene_path, output_dir, num_frames=20):
    """
    准备单个场景
    
    Args:
        scene_path: ARKitScenes 原始场景路径
        output_dir: 输出目录
        num_frames: 要提取的帧数
    """
    scene_path = Path(scene_path)
    output_dir = Path(output_dir)
    
    # 获取场景ID
    scene_id = scene_path.name
    print(f"\n{'='*60}")
    print(f"准备场景: {scene_id}")
    print(f"{'='*60}")
    
    # 创建输出目录
    output_scene_dir = output_dir / scene_id
    output_images_dir = output_scene_dir / "images"
    output_images_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取图像文件列表
    images_dir = scene_path / "lowres_wide"
    if not images_dir.exists():
        print(f"❌ 图像目录不存在: {images_dir}")
        return False
    
    image_files = sorted(list(images_dir.glob("*.png")))
    total_images = len(image_files)
    print(f"📷 找到 {total_images} 张图像")
    
    if total_images == 0:
        print("❌ 没有找到图像文件")
        return False
    
    # 均匀采样帧
    step = max(1, total_images // num_frames)
    selected_indices = list(range(0, total_images, step))[:num_frames]
    print(f"✓ 选择 {len(selected_indices)} 帧 (每隔 {step} 帧)")
    
    # 复制选中的图像
    print("📦 复制图像...")
    for i, idx in enumerate(selected_indices):
        src_img = image_files[idx]
        dst_img = output_images_dir / f"frame_{i:04d}.jpg"
        
        # 转换 PNG 到 JPG
        try:
            img = Image.open(src_img)
            img = img.convert("RGB")
            img.save(dst_img, "JPEG", quality=95)
        except Exception as e:
            print(f"⚠️  转换图像失败 {src_img}: {e}")
            continue
    
    print(f"✓ 已保存 {len(list(output_images_dir.glob('*.jpg')))} 张图像")
    
    # 读取标注信息
    annotation_file = scene_path / f"{scene_id}_3dod_annotation.json"
    objects = []
    if annotation_file.exists():
        with open(annotation_file, 'r') as f:
            data = json.load(f)
            if "data" in data:
                objects = [obj["label"] for obj in data["data"]]
        print(f"📋 场景包含物体: {', '.join(set(objects))}")
    
    # 创建元数据
    metadata = {
        "scene_id": scene_id,
        "total_frames": len(selected_indices),
        "resolution": [256, 192],  # ARKitScenes lowres_wide 分辨率
        "objects": list(set(objects)),
        "source": "ARKitScenes",
        "test_queries": [
            "the chair",
            "the table",
            "the bed",
            "the cabinet",
            "the tv",
            "the chair near the table"
        ]
    }
    
    metadata_file = output_scene_dir / "metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ 元数据已保存: {metadata_file}")
    
    # 创建测试脚本
    test_script = output_scene_dir / "run_test.sh"
    with open(test_script, 'w') as f:
        f.write(f"""#!/bin/bash
# 测试场景: {scene_id}

cd ../..

echo "运行 QwenGround 测试: {scene_id}"
echo "查询: the chair"

python qwenground_main.py \\
    --input_type images \\
    --input_path data/arkitscenes_test/processed/{scene_id}/images \\
    --query "the chair" \\
    --device cpu \\
    --output_dir ./outputs/arkitscenes_test_{scene_id} \\
    --save_intermediate

echo "测试完成！查看结果："
echo "  ls outputs/arkitscenes_test_{scene_id}/"
""")
    test_script.chmod(0o755)
    print(f"✓ 测试脚本已创建: {test_script}")
    
    print(f"\n{'='*60}")
    print(f"✅ 场景 {scene_id} 准备完成！")
    print(f"{'='*60}")
    print(f"输出目录: {output_scene_dir}")
    print(f"图像数量: {len(list(output_images_dir.glob('*.jpg')))}")
    print(f"\n运行测试:")
    print(f"  cd {output_scene_dir}")
    print(f"  ./run_test.sh")
    print("")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="准备单个ARKitScenes场景")
    parser.add_argument("--scene_path", required=True, help="ARKitScenes场景路径")
    parser.add_argument("--output_dir", required=True, help="输出目录")
    parser.add_argument("--num_frames", type=int, default=20, help="提取帧数")
    
    args = parser.parse_args()
    
    success = prepare_scene(args.scene_path, args.output_dir, args.num_frames)
    sys.exit(0 if success else 1)


