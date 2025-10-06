"""
QwenGround 使用示例
"""

from qwenground_system import QwenGroundSystem
from utils.helpers import setup_logging


def example_video_input():
    """示例1: 视频输入"""
    print("示例1: 视频输入")
    print("="*60)
    
    # 初始化系统
    system = QwenGroundSystem(
        model_name="Qwen/Qwen2-VL-7B-Instruct",
        device="cuda",
        use_api=False
    )
    
    # 运行推理
    result = system.run(
        input_path="path/to/your/video.mp4",
        query="the red apple on the wooden table",
        input_type="video",
        output_dir="./outputs/example1"
    )
    
    # 输出结果
    if result['success']:
        print(f"✅ 成功定位: {result['target_object']}")
        print(f"3D边界框: {result['3d_bbox']}")
        print(f"置信度: {result['confidence']}")
    else:
        print(f"❌ 失败: {result['error']}")


def example_image_sequence():
    """示例2: 图像序列输入"""
    print("\n示例2: 图像序列输入")
    print("="*60)
    
    # 初始化系统
    system = QwenGroundSystem(
        model_name="Qwen/Qwen2-VL-7B-Instruct",
        device="cuda"
    )
    
    # 运行推理
    result = system.run(
        input_path="path/to/your/images/",
        query="the laptop near the window",
        input_type="images",
        output_dir="./outputs/example2",
        visualize=True,
        save_intermediate=True
    )
    
    if result['success']:
        print(f"✅ 成功定位: {result['target_object']}")
        print(f"处理时间: {result['metadata']['processing_time']}秒")


def example_api_mode():
    """示例3: 使用vLLM API模式"""
    print("\n示例3: vLLM API模式")
    print("="*60)
    
    # 初始化系统（API模式）
    system = QwenGroundSystem(
        model_name="Qwen/Qwen2-VL-7B-Instruct",
        device="cuda",
        use_api=True,
        api_url="http://localhost:8000/v1",
        api_key="sk-34bb9d7e720b4160865a2be94e242c51"
    )
    
    # 运行推理
    result = system.run(
        input_path="path/to/your/video.mp4",
        query="the person sitting on the chair",
        input_type="video",
        output_dir="./outputs/example3"
    )
    
    if result['success']:
        print(f"✅ 成功定位: {result['target_object']}")


def example_custom_config():
    """示例4: 使用自定义配置"""
    print("\n示例4: 自定义配置")
    print("="*60)
    
    # 自定义配置
    custom_config = {
        'reconstruction': {
            'keyframe_count': 20,  # 更多关键帧
            'depth_model': 'DPT_Large',  # 更好的深度模型
            'method': 'depth',
        },
        'detection': {
            'yolo_model': 'yolov8x.pt',
            'conf_threshold': 0.3,
            'iou_threshold': 0.5,
        }
    }
    
    # 初始化系统
    system = QwenGroundSystem(
        model_name="Qwen/Qwen2-VL-7B-Instruct",
        device="cuda",
        config=custom_config
    )
    
    # 运行推理
    result = system.run(
        input_path="path/to/your/video.mp4",
        query="the bottle on the left side",
        input_type="video",
        output_dir="./outputs/example4"
    )
    
    if result['success']:
        print(f"✅ 成功定位: {result['target_object']}")


def main():
    """主函数"""
    # 设置日志
    setup_logging(log_level="INFO")
    
    print("\n" + "="*60)
    print("QwenGround 使用示例")
    print("="*60 + "\n")
    
    # 注意: 这些示例需要实际的视频/图像路径
    # 请替换为你自己的数据
    
    # 运行示例
    # example_video_input()
    # example_image_sequence()
    # example_api_mode()
    # example_custom_config()
    
    print("\n提示: 请修改示例代码中的路径为实际数据路径")


if __name__ == "__main__":
    main()

