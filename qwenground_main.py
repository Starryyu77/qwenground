#!/usr/bin/env python3
"""
QwenGround Main Entry Point
主入口脚本
"""

import argparse
import sys
from pathlib import Path

from qwenground_system import QwenGroundSystem
from utils.helpers import setup_logging, load_config, check_dependencies, print_banner


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="QwenGround: 零-Shot 3D场景理解和定位系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 视频输入
  python qwenground_main.py --input_type video --input_path video.mp4 \\
      --query "the red apple on the table"
  
  # 图像序列输入
  python qwenground_main.py --input_type images --input_path ./images/ \\
      --query "the laptop near the window"
  
  # 使用配置文件
  python qwenground_main.py --config config/default.yaml \\
      --input_path video.mp4 --query "..."
        """
    )
    
    # 必需参数
    parser.add_argument(
        '--input_path',
        type=str,
        required=True,
        help='输入路径（视频文件或图像文件夹）'
    )
    
    parser.add_argument(
        '--query',
        type=str,
        required=True,
        help='自然语言查询，例如: "the red apple on the wooden table"'
    )
    
    # 可选参数
    parser.add_argument(
        '--input_type',
        type=str,
        choices=['video', 'images'],
        default='video',
        help='输入类型 (默认: video)'
    )
    
    parser.add_argument(
        '--output_dir',
        type=str,
        default='./outputs',
        help='输出目录 (默认: ./outputs)'
    )
    
    parser.add_argument(
        '--model_name',
        type=str,
        default='Qwen/Qwen2-VL-7B-Instruct',
        help='VLM模型名称 (默认: Qwen/Qwen2-VL-7B-Instruct)'
    )
    
    parser.add_argument(
        '--device',
        type=str,
        choices=['cuda', 'cpu'],
        default='cuda',
        help='设备 (默认: cuda)'
    )
    
    parser.add_argument(
        '--use_api',
        action='store_true',
        help='使用vLLM API模式'
    )
    
    parser.add_argument(
        '--api_url',
        type=str,
        default='http://localhost:8000/v1',
        help='vLLM API服务器地址 (默认: http://localhost:8000/v1)'
    )
    
    parser.add_argument(
        '--api_key',
        type=str,
        default=None,
        help='API密钥'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='配置文件路径（YAML格式）'
    )
    
    parser.add_argument(
        '--no_visualize',
        action='store_true',
        help='不生成可视化'
    )
    
    parser.add_argument(
        '--save_intermediate',
        action='store_true',
        help='保存中间结果（点云、OLT等）'
    )
    
    parser.add_argument(
        '--log_level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别 (默认: INFO)'
    )
    
    parser.add_argument(
        '--log_file',
        type=str,
        default=None,
        help='日志文件路径（可选）'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    # 打印横幅
    print_banner()
    
    # 解析参数
    args = parse_args()
    
    # 设置日志
    setup_logging(log_level=args.log_level, log_file=args.log_file)
    
    # 检查依赖
    print("\n检查依赖...")
    if not check_dependencies():
        sys.exit(1)
    
    # 验证输入路径
    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"\n❌ 错误: 输入路径不存在: {input_path}")
        sys.exit(1)
    
    # 加载配置
    config = None
    if args.config:
        print(f"\n加载配置文件: {args.config}")
        config = load_config(args.config)
    
    # 初始化系统
    print(f"\n初始化QwenGround系统...")
    print(f"  模型: {args.model_name}")
    print(f"  设备: {args.device}")
    print(f"  API模式: {'是' if args.use_api else '否'}")
    
    try:
        system = QwenGroundSystem(
            model_name=args.model_name,
            device=args.device,
            use_api=args.use_api,
            api_url=args.api_url,
            api_key=args.api_key,
            config=config
        )
    except Exception as e:
        print(f"\n❌ 系统初始化失败: {e}")
        sys.exit(1)
    
    # 运行系统
    print("\n开始处理...\n")
    
    result = system.run(
        input_path=str(input_path),
        query=args.query,
        input_type=args.input_type,
        output_dir=args.output_dir,
        visualize=not args.no_visualize,
        save_intermediate=args.save_intermediate
    )
    
    # 输出结果
    if result['success']:
        print("\n" + "="*60)
        print("📊 结果摘要:")
        print("="*60)
        print(f"查询: {result['query']}")
        print(f"目标物体: {result['target_object']}")
        print(f"置信度: {result['confidence']:.3f}")
        print(f"3D边界框: {result['3d_bbox']}")
        print(f"3D中心: {result['center_3d']}")
        print(f"\n处理时间: {result['metadata']['processing_time']}秒")
        print(f"关键帧数: {result['metadata']['num_frames']}")
        print(f"检测物体数: {result['metadata']['num_objects']}")
        print(f"\n输出目录: {args.output_dir}")
        print("="*60)
        print("\n✅ 完成!")
    else:
        print("\n❌ 处理失败:")
        print(f"  错误: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

