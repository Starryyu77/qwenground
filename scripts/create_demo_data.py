#!/usr/bin/env python3
"""
创建演示数据 - 用于快速测试 QwenGround 系统

这个脚本会生成一些简单的测试图像，模拟室内场景，
以便在没有真实数据集时快速测试系统。
"""

import os
import sys
from pathlib import Path
import json

def create_demo_scene():
    """创建演示场景"""
    
    # 创建输出目录
    output_dir = Path("./data/demo_scene")
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                                                               ║")
    print("║         创建演示数据 for QwenGround                           ║")
    print("║                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        # 创建一系列模拟室内场景的图像
        scenes = [
            {
                "name": "frame_0000.jpg",
                "objects": [
                    {"type": "chair", "pos": (100, 200), "size": (80, 100), "color": (139, 69, 19)},
                    {"type": "table", "pos": (300, 180), "size": (150, 120), "color": (160, 82, 45)},
                ]
            },
            {
                "name": "frame_0001.jpg",
                "objects": [
                    {"type": "chair", "pos": (110, 200), "size": (85, 105), "color": (139, 69, 19)},
                    {"type": "table", "pos": (310, 180), "size": (150, 120), "color": (160, 82, 45)},
                    {"type": "lamp", "pos": (450, 100), "size": (30, 80), "color": (255, 215, 0)},
                ]
            },
            {
                "name": "frame_0002.jpg",
                "objects": [
                    {"type": "chair", "pos": (120, 200), "size": (90, 110), "color": (139, 69, 19)},
                    {"type": "table", "pos": (320, 180), "size": (150, 120), "color": (160, 82, 45)},
                    {"type": "lamp", "pos": (460, 100), "size": (30, 80), "color": (255, 215, 0)},
                ]
            },
            {
                "name": "frame_0003.jpg",
                "objects": [
                    {"type": "chair", "pos": (130, 200), "size": (95, 115), "color": (139, 69, 19)},
                    {"type": "table", "pos": (330, 180), "size": (150, 120), "color": (160, 82, 45)},
                    {"type": "lamp", "pos": (470, 100), "size": (30, 80), "color": (255, 215, 0)},
                    {"type": "sofa", "pos": (50, 350), "size": (200, 100), "color": (70, 130, 180)},
                ]
            },
            {
                "name": "frame_0004.jpg",
                "objects": [
                    {"type": "chair", "pos": (140, 200), "size": (100, 120), "color": (139, 69, 19)},
                    {"type": "table", "pos": (340, 180), "size": (150, 120), "color": (160, 82, 45)},
                    {"type": "lamp", "pos": (480, 100), "size": (30, 80), "color": (255, 215, 0)},
                    {"type": "sofa", "pos": (60, 350), "size": (200, 100), "color": (70, 130, 180)},
                ]
            },
        ]
        
        print(f"📸 创建 {len(scenes)} 帧图像...")
        
        for i, scene in enumerate(scenes):
            # 创建图像（640x480，室内场景背景色）
            img = Image.new('RGB', (640, 480), color=(245, 245, 220))  # 米色背景
            draw = ImageDraw.Draw(img)
            
            # 添加地板
            draw.rectangle([0, 350, 640, 480], fill=(210, 180, 140))
            
            # 添加墙壁纹理
            for j in range(0, 640, 50):
                draw.line([j, 0, j, 350], fill=(240, 240, 230), width=1)
            
            # 绘制物体
            for obj in scene['objects']:
                x, y = obj['pos']
                w, h = obj['size']
                color = obj['color']
                
                # 绘制物体主体
                draw.rectangle([x, y, x+w, y+h], fill=color, outline=(0, 0, 0), width=2)
                
                # 添加简单的3D效果
                shadow_color = tuple(max(0, c-50) for c in color)
                draw.rectangle([x+5, y+5, x+w+5, y+h+5], fill=shadow_color, outline=None)
                
                # 绘制物体（覆盖阴影）
                draw.rectangle([x, y, x+w, y+h], fill=color, outline=(0, 0, 0), width=2)
                
                # 添加标签（用于调试）
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
                except:
                    font = ImageFont.load_default()
                draw.text((x+5, y+5), obj['type'], fill=(255, 255, 255), font=font)
            
            # 保存图像
            img_path = images_dir / scene['name']
            img.save(img_path, quality=95)
            print(f"  ✓ 创建: {scene['name']}")
        
        # 创建元数据
        metadata = {
            "scene_id": "demo_scene",
            "num_frames": len(scenes),
            "resolution": [640, 480],
            "objects": ["chair", "table", "lamp", "sofa"],
            "description": "演示场景 - 包含椅子、桌子、台灯和沙发",
            "note": "这是用于测试的合成数据"
        }
        
        metadata_path = output_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, indent=2, fp=f)
        
        print(f"\n✓ 元数据保存到: {metadata_path}")
        
        # 创建测试脚本
        test_script = f"""#!/bin/bash
# 演示场景测试脚本

echo "运行 QwenGround 演示测试..."
echo ""

# 测试 1: 查找椅子
echo "测试 1: 查找椅子"
python qwenground_main.py \\
    --input_type images \\
    --input_path data/demo_scene/images \\
    --query "the chair" \\
    --device cpu \\
    --output_dir ./outputs/demo_chair \\
    --save_intermediate

echo ""
echo "测试完成！查看结果:"
echo "  cat ./outputs/demo_chair/final_result.json"
echo ""

# 可选: 更多测试
# python qwenground_main.py --input_type images --input_path data/demo_scene/images --query "the table" --device cpu --output_dir ./outputs/demo_table
# python qwenground_main.py --input_type images --input_path data/demo_scene/images --query "the lamp" --device cpu --output_dir ./outputs/demo_lamp
"""
        
        test_script_path = output_dir / "run_demo_test.sh"
        with open(test_script_path, 'w') as f:
            f.write(test_script)
        os.chmod(test_script_path, 0o755)
        
        print(f"✓ 测试脚本保存到: {test_script_path}")
        
        print("\n" + "="*60)
        print("✅ 演示数据创建成功！")
        print("="*60)
        print(f"\n📁 输出位置: {output_dir.absolute()}")
        print(f"📸 图像数量: {len(scenes)} 帧")
        print(f"📦 包含物体: {', '.join(metadata['objects'])}")
        
        print("\n🚀 快速测试命令:")
        print(f"\n  python qwenground_main.py \\")
        print(f"      --input_type images \\")
        print(f"      --input_path data/demo_scene/images \\")
        print(f"      --query \"the chair\" \\")
        print(f"      --device cpu \\")
        print(f"      --output_dir ./outputs/demo_test")
        
        print(f"\n或运行自动测试脚本:")
        print(f"  cd data/demo_scene && ./run_demo_test.sh")
        
        return True
        
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("\n请安装 Pillow:")
        print("  pip install Pillow")
        return False
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_demo_scene()
    sys.exit(0 if success else 1)

