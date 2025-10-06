#!/usr/bin/env python3
"""
QwenGround 安全测试脚本 - 逐步检查依赖
"""

import sys


def check_dependency(module_name, package_name=None, install_name=None):
    """检查单个依赖"""
    display_name = package_name or module_name
    install_name = install_name or display_name.lower()
    
    try:
        mod = __import__(module_name)
        version = getattr(mod, '__version__', 'unknown')
        print(f"  ✓ {display_name:20s} - 版本: {version}")
        return True, None
    except ImportError:
        print(f"  ✗ {display_name:20s} - 未安装")
        return False, install_name
    except Exception as e:
        print(f"  ⚠️  {display_name:20s} - 错误: {type(e).__name__}")
        return False, install_name


def main():
    print("=" * 70)
    print("QwenGround 安装测试（安全模式）")
    print("=" * 70)
    
    print(f"\n📌 Python版本: {sys.version}")
    if sys.version_info < (3, 10):
        print("⚠️  警告: 推荐使用Python 3.10+")
    
    print("\n" + "=" * 70)
    print("检查核心依赖:")
    print("=" * 70)
    
    # 定义依赖列表 (module_name, display_name, install_name)
    dependencies = [
        ('torch', 'PyTorch', 'torch'),
        ('torchvision', 'TorchVision', 'torchvision'),
        ('transformers', 'Transformers', 'transformers'),
        ('cv2', 'OpenCV', 'opencv-python'),
        ('PIL', 'Pillow', 'pillow'),
        ('numpy', 'NumPy', 'numpy'),
        ('yaml', 'PyYAML', 'pyyaml'),
        ('matplotlib', 'Matplotlib', 'matplotlib'),
        ('tqdm', 'tqdm', 'tqdm'),
        ('qrcode', 'QRCode', 'qrcode[pil]'),
        ('timm', 'timm', 'timm'),
        ('open3d', 'Open3D', 'open3d'),
        ('ultralytics', 'Ultralytics', 'ultralytics'),
    ]
    
    success_count = 0
    missing = []
    
    for dep in dependencies:
        module_name = dep[0]
        display_name = dep[1]
        install_name = dep[2]
        success, missing_pkg = check_dependency(module_name, display_name, install_name)
        if success:
            success_count += 1
        elif missing_pkg:
            missing.append(missing_pkg)
    
    print(f"\n📊 结果: {success_count}/{len(dependencies)} 依赖已安装")
    
    # CUDA检查
    print("\n" + "=" * 70)
    print("检查CUDA支持:")
    print("=" * 70)
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  ✓ CUDA可用")
            print(f"    - CUDA版本: {torch.version.cuda}")
            print(f"    - GPU数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"    - GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            print("  ⚠️  CUDA不可用 (将使用CPU，速度会较慢)")
    except:
        print("  ✗ 无法检查CUDA")
    
    # QwenGround模块检查
    if success_count >= len(dependencies) - 2:  # 允许有2个可选依赖缺失
        print("\n" + "=" * 70)
        print("检查QwenGround模块:")
        print("=" * 70)
        
        modules = [
            'modules.perspective_adapter',
            'modules.reconstruction_3d',
            'modules.fusion_alignment',
            'modules.object_lookup_table',
            'modules.visualization',
            'utils.vlm_client',
            'utils.object_detector',
            'utils.helpers',
        ]
        
        module_success = 0
        for module_name in modules:
            try:
                __import__(module_name)
                print(f"  ✓ {module_name}")
                module_success += 1
            except Exception as e:
                print(f"  ✗ {module_name} - {type(e).__name__}: {str(e)[:50]}")
        
        print(f"\n📊 结果: {module_success}/{len(modules)} 模块导入成功")
    
    # 总结
    print("\n" + "=" * 70)
    
    if missing:
        print("❌ 发现缺失的依赖，需要安装:")
        print("=" * 70)
        print("\n安装缺失的依赖:")
        print(f"  pip install {' '.join(missing)}")
        print("\n或安装所有依赖:")
        print("  pip install -r requirements.txt")
        return 1
    
    if success_count == len(dependencies):
        print("✅ 所有依赖已安装!")
        print("=" * 70)
        print("\n下一步:")
        print("  1. 运行示例: python qwenground_main.py --help")
        print("  2. 查看快速入门: cat QUICKSTART.md")
        return 0
    else:
        print("⚠️  部分依赖缺失")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())

