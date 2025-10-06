#!/usr/bin/env python3
"""
快速依赖检查 - 避免段错误的库
"""

import sys
import subprocess


def check_with_subprocess(module_name, display_name):
    """使用子进程检查依赖，避免段错误影响主进程"""
    try:
        result = subprocess.run(
            [sys.executable, '-c', f'import {module_name}; print({module_name}.__version__)'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  ✓ {display_name:20s} - 版本: {version}")
            return True
        else:
            error = result.stderr.strip().split('\n')[-1] if result.stderr else 'Unknown error'
            if 'ModuleNotFoundError' in error or 'No module named' in error:
                print(f"  ✗ {display_name:20s} - 未安装")
            else:
                print(f"  ⚠️  {display_name:20s} - 导入错误")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  {display_name:20s} - 超时")
        return False
    except Exception as e:
        print(f"  ⚠️  {display_name:20s} - {type(e).__name__}")
        return False


def main():
    print("=" * 70)
    print("QwenGround 依赖检查")
    print("=" * 70)
    
    print(f"\n📌 Python版本: {sys.version.split()[0]}")
    
    print("\n" + "=" * 70)
    print("检查依赖包:")
    print("=" * 70)
    
    # 安全的依赖列表
    safe_deps = [
        ('torch', 'PyTorch'),
        ('torchvision', 'TorchVision'),
        ('transformers', 'Transformers'),
        ('cv2', 'OpenCV'),
        ('PIL', 'Pillow'),
        ('numpy', 'NumPy'),
        ('yaml', 'PyYAML'),
        ('matplotlib', 'Matplotlib'),
        ('tqdm', 'tqdm'),
    ]
    
    # 可能有问题的依赖
    risky_deps = [
        ('timm', 'timm'),
        ('qrcode', 'QRCode'),
        ('open3d', 'Open3D'),
        ('ultralytics', 'Ultralytics'),
    ]
    
    print("\n[安全依赖]")
    safe_count = sum(check_with_subprocess(m, d) for m, d in safe_deps)
    
    print("\n[高级依赖]")
    risky_count = sum(check_with_subprocess(m, d) for m, d in risky_deps)
    
    total = len(safe_deps) + len(risky_deps)
    installed = safe_count + risky_count
    
    print(f"\n📊 总计: {installed}/{total} 依赖已安装")
    
    # 缺失的依赖
    missing = []
    for module, display in safe_deps + risky_deps:
        result = subprocess.run(
            [sys.executable, '-c', f'import {module}'],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            if module == 'cv2':
                missing.append('opencv-python')
            elif module == 'PIL':
                missing.append('pillow')
            elif module == 'yaml':
                missing.append('pyyaml')
            else:
                missing.append(module)
    
    # CUDA检查
    print("\n" + "=" * 70)
    print("CUDA检查:")
    print("=" * 70)
    result = subprocess.run(
        [sys.executable, '-c', 
         'import torch; print("CUDA可用" if torch.cuda.is_available() else "CUDA不可用(将使用CPU)")'],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        print(f"  {result.stdout.strip()}")
    
    # 总结
    print("\n" + "=" * 70)
    if missing:
        print("❌ 缺失依赖:")
        print("=" * 70)
        print(f"\n需要安装: {', '.join(missing)}")
        print(f"\n运行命令:")
        print(f"  pip install {' '.join(missing)}")
        return 1
    else:
        print("✅ 所有依赖已安装!")
        print("=" * 70)
        print("\n下一步:")
        print("  python qwenground_main.py --help")
        return 0


if __name__ == "__main__":
    sys.exit(main())

