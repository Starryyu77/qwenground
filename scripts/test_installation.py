#!/usr/bin/env python3
"""
测试QwenGround安装
"""

import sys
import importlib


def test_import(module_name, package_name=None):
    """测试导入模块"""
    display_name = package_name or module_name
    try:
        mod = importlib.import_module(module_name)
        version = getattr(mod, '__version__', 'unknown')
        print(f"✓ {display_name:20s} - 版本: {version}")
        return True
    except ImportError as e:
        print(f"✗ {display_name:20s} - 未安装: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {display_name:20s} - 导入错误: {type(e).__name__}")
        return False


def test_cuda():
    """测试CUDA"""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA可用")
            print(f"  - CUDA版本: {torch.version.cuda}")
            print(f"  - GPU数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"  - GPU {i}: {torch.cuda.get_device_name(i)}")
            return True
        else:
            print("✗ CUDA不可用 (将使用CPU)")
            return False
    except:
        return False


def test_qwenground_imports():
    """测试QwenGround模块导入"""
    print("\n测试QwenGround模块:")
    
    modules = [
        ('modules.perspective_adapter', 'PerspectiveAdapter'),
        ('modules.reconstruction_3d', 'Reconstruction3D'),
        ('modules.fusion_alignment', 'FusionAlignment'),
        ('modules.object_lookup_table', 'ObjectLookupTable'),
        ('modules.visualization', 'Visualizer'),
        ('utils.vlm_client', 'VLMClient'),
        ('utils.object_detector', 'ObjectDetector'),
    ]
    
    success_count = 0
    for module_name, display_name in modules:
        try:
            importlib.import_module(module_name)
            print(f"✓ {display_name}")
            success_count += 1
        except Exception as e:
            print(f"✗ {display_name} - 错误: {e}")
    
    return success_count == len(modules)


def main():
    print("="*60)
    print("QwenGround 安装测试")
    print("="*60)
    
    print("\n检查Python版本:")
    print(f"Python {sys.version}")
    
    if sys.version_info < (3, 10):
        print("⚠️  警告: 推荐使用Python 3.10+")
    
    print("\n检查核心依赖:")
    
    dependencies = [
        ('torch', 'PyTorch'),
        ('torchvision', 'TorchVision'),
        ('transformers', 'Transformers'),
        ('cv2', 'OpenCV'),
        ('open3d', 'Open3D'),
        ('ultralytics', 'Ultralytics'),
        ('PIL', 'Pillow'),
        ('numpy', 'NumPy'),
        ('pandas', 'Pandas'),
        ('yaml', 'PyYAML'),
        ('matplotlib', 'Matplotlib'),
        ('tqdm', 'tqdm'),
    ]
    
    success_count = 0
    for module, package in dependencies:
        if test_import(module, package):
            success_count += 1
    
    print(f"\n依赖检查: {success_count}/{len(dependencies)} 通过")
    
    print("\n检查CUDA支持:")
    test_cuda()
    
    # 测试QwenGround模块
    qwenground_ok = test_qwenground_imports()
    
    print("\n" + "="*60)
    
    if success_count == len(dependencies) and qwenground_ok:
        print("✅ 所有测试通过! QwenGround已正确安装")
        print("="*60)
        return 0
    else:
        print("❌ 部分测试失败，请检查依赖安装")
        print("="*60)
        print("\n修复步骤:")
        print("1. 运行: pip install -r requirements.txt")
        print("2. 如果使用GPU，确保安装了正确的PyTorch CUDA版本")
        print("3. 重新运行此测试脚本")
        return 1


if __name__ == "__main__":
    sys.exit(main())

