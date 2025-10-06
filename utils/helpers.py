"""
Helper functions and utilities
"""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import sys


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    设置日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日志文件路径（可选）
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # 根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载YAML配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def save_json(data: Dict, output_path: str, indent: int = 2):
    """
    保存JSON文件
    
    Args:
        data: 要保存的数据
        output_path: 输出路径
        indent: 缩进空格数
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_json(input_path: str) -> Dict:
    """
    加载JSON文件
    
    Args:
        input_path: 输入路径
        
    Returns:
        数据字典
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def check_dependencies():
    """检查依赖是否安装"""
    dependencies = {
        'torch': 'PyTorch',
        'cv2': 'OpenCV (opencv-python)',
        'open3d': 'Open3D',
        'transformers': 'Transformers',
        'ultralytics': 'Ultralytics (YOLOv8)',
        'PIL': 'Pillow',
        'numpy': 'NumPy',
        'pandas': 'Pandas'
    }
    
    missing = []
    
    for module, name in dependencies.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(name)
    
    if missing:
        print("❌ 缺少以下依赖:")
        for dep in missing:
            print(f"  - {dep}")
        print("\n请运行: pip install -r requirements.txt")
        return False
    else:
        print("✅ 所有依赖已安装")
        return True


def print_banner():
    """打印启动横幅"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║               🎯 QwenGround System v1.0 🎯                ║
    ║                                                           ║
    ║   Zero-Shot 3D Visual Grounding with Qwen2-VL            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

