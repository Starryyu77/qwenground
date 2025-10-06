# QwenGround 快速入门

5分钟快速开始使用QwenGround！

## 前置条件

- Python 3.10+
- CUDA 11.8+ (推荐使用GPU)
- 至少16GB VRAM

## 安装

```bash
# 1. 进入项目目录
cd /Users/starryyu/Documents/tinghua/QwenGround

# 2. 创建虚拟环境
conda create -n qwenground python=3.10
conda activate qwenground

# 3. 安装PyTorch (CUDA 11.8)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 4. 安装依赖
pip install -r requirements.txt

# 5. 测试安装
python scripts/test_installation.py
```

## 第一次运行

### 示例1: 视频输入

```bash
python qwenground_main.py \
    --input_type video \
    --input_path ./path/to/your/video.mp4 \
    --query "the red apple on the table" \
    --output_dir ./outputs/test1
```

### 示例2: 图像序列

```bash
python qwenground_main.py \
    --input_type images \
    --input_path ./path/to/images/ \
    --query "the laptop near the window" \
    --output_dir ./outputs/test2
```

## 输出文件

运行完成后，在输出目录中会看到：

```
outputs/test1/
├── result.json              # 主要结果（JSON格式）
├── pointcloud.ply          # 3D点云
├── scene_with_bbox.ply     # 带边界框的场景
├── animation.gif           # 旋转动画
├── summary.png             # 结果摘要图
└── result_images/          # 标注后的关键帧
    ├── result_frame_0000.jpg
    ├── result_frame_0003.jpg
    └── ...
```

### 查看结果

```bash
# 查看JSON结果
cat outputs/test1/result.json

# 使用Open3D查看点云
python -c "import open3d as o3d; pcd = o3d.io.read_point_cloud('outputs/test1/pointcloud.ply'); o3d.visualization.draw_geometries([pcd])"
```

## Python API 使用

```python
from qwenground_system import QwenGroundSystem

# 初始化系统
system = QwenGroundSystem(
    model_name="Qwen/Qwen2-VL-7B-Instruct",
    device="cuda"
)

# 运行推理
result = system.run(
    input_path="path/to/video.mp4",
    query="the red apple on the wooden table",
    input_type="video",
    output_dir="./outputs/demo"
)

# 查看结果
if result['success']:
    print(f"目标物体: {result['target_object']}")
    print(f"3D边界框: {result['3d_bbox']}")
    print(f"置信度: {result['confidence']}")
```

## 使用vLLM API模式（推荐用于生产环境）

### 1. 启动vLLM服务器

```bash
# 推荐：通过环境变量提供密钥
export API_KEY="<your_api_key>"
bash scripts/deploy_vllm.sh
```

或手动启动：

```bash
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2-VL-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --api-key "$API_KEY"
```

### 2. 使用API模式运行

```bash
python qwenground_main.py \
    --use_api \
    --api_url http://localhost:8000/v1 \
    --api_key "$API_KEY" \
    --input_path ./video.mp4 \
    --query "the person on the left"
```

## 配置选项

### 使用配置文件

创建自定义配置：

```yaml
# config/my_config.yaml
reconstruction:
  keyframe_count: 20
  depth_model: "DPT_Large"

detection:
  yolo_model: "yolov8x.pt"
  conf_threshold: 0.3
```

运行：

```bash
python qwenground_main.py \
    --config config/my_config.yaml \
    --input_path ./video.mp4 \
    --query "..."
```

### 常用参数

```bash
# 调整关键帧数量（更多帧=更准确但更慢）
python qwenground_main.py ... --config config/default.yaml

# 不生成可视化（加速）
python qwenground_main.py ... --no_visualize

# 保存中间结果（用于调试）
python qwenground_main.py ... --save_intermediate

# 调整日志级别
python qwenground_main.py ... --log_level DEBUG
```

## 性能优化

### 对于较慢的机器

```yaml
# config/fast.yaml
reconstruction:
  keyframe_count: 8           # 减少帧数
  depth_model: "MiDaS_small"  # 使用小模型

detection:
  yolo_model: "yolov8m.pt"    # 使用中等模型
  conf_threshold: 0.35        # 提高阈值
```

### 对于高性能机器

```yaml
# config/quality.yaml
reconstruction:
  keyframe_count: 25          # 更多帧
  depth_model: "DPT_Large"    # 更好的模型

detection:
  yolo_model: "yolov8x.pt"    # 最大模型
  conf_threshold: 0.2         # 更低阈值
```

## 常见查询示例

```bash
# 空间关系查询
--query "the apple on the table"
--query "the book next to the lamp"
--query "the chair behind the desk"

# 属性查询
--query "the red apple"
--query "the wooden table"
--query "the black laptop"

# 组合查询
--query "the red apple on the wooden table"
--query "the person sitting on the blue chair"
--query "the bottle to the left of the cup"
```

## 故障排除

### GPU内存不足

```bash
# 使用更小的模型
python qwenground_main.py \
    --model_name Qwen/Qwen2-VL-2B-Instruct \
    ...
```

### 视频太大

```bash
# 在外部先降低分辨率
ffmpeg -i input.mp4 -vf scale=1280:720 output.mp4
```

### 深度模型下载慢

```bash
# 预先下载
python -c "import torch; torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')"
```

## 下一步

- 查看 `examples/example_usage.py` 了解更多API示例
- 阅读 `INSTALL.md` 了解详细安装说明
- 阅读 `README.md` 了解系统架构
- 修改 `config/default.yaml` 自定义配置

## 获取帮助

```bash
# 查看完整帮助
python qwenground_main.py --help

# 运行测试
python scripts/test_installation.py
```

---

🎉 享受使用QwenGround！

