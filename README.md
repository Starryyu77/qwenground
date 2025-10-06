# QwenGround: 零-Shot 3D场景理解和定位系统

基于 [SeeGround](https://github.com/iris0329/SeeGround) 思路，使用 Qwen2-VL-7B-Instruct 实现的零-shot开放词汇3D视觉定位系统。

## 📋 项目概述

QwenGround 能够从视频或图像序列中理解3D场景，并根据自然语言描述定位目标物体的3D边界框。

### 核心特性

- 🎯 **零-Shot定位**: 无需3D标注，支持任意自然语言描述
- 🎥 **多输入模式**: 支持视频文件和图像序列
- 🔄 **2D到3D重建**: 从2D输入自动重建粗糙3D场景
- 🧠 **大模型驱动**: 基于Qwen2-VL的强大视觉-语言理解能力
- 📦 **3D可视化**: 输出交互式3D场景和边界框

## 🏗️ 系统架构

```
输入 (视频/图像) + 自然语言查询
    ↓
[1] Perspective Adaptation Module (关键帧提取/多视角生成)
    ↓
[2] 3D Reconstruction (SfM点云 / 深度估计)
    ↓
[3] Object Lookup Table (物体检测和3D边界框)
    ↓
[4] Fusion Alignment Module (VLM + 2D-3D融合)
    ↓
输出 (3D边界框JSON + 可视化)
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- CUDA 11.8+ (GPU推荐: RTX 3090/4090 或 A100)
- 16GB+ VRAM (7B模型) 或 80GB+ (72B模型)

### 安装

```bash
# 克隆项目
cd /Users/starryyu/Documents/tinghua/QwenGround

# 安装依赖
pip install -r requirements.txt

# (可选) 安装COLMAP用于更好的SfM
# Ubuntu: sudo apt-get install colmap
# macOS: brew install colmap
```

### 使用示例

#### 1. 视频输入

```bash
python qwenground_main.py \
    --input_type video \
    --input_path ./examples/kitchen_scene.mp4 \
    --query "the red apple on the wooden table" \
    --output_dir ./outputs/kitchen
```

#### 2. 图像序列输入

```bash
python qwenground_main.py \
    --input_type images \
    --input_path ./examples/room_images/ \
    --query "the laptop near the window" \
    --output_dir ./outputs/room
```

#### 3. Python API

```python
from qwenground import QwenGroundSystem

# 初始化系统
system = QwenGroundSystem(
    model_name="Qwen/Qwen2-VL-7B-Instruct",
    device="cuda"
)

# 运行推理
result = system.run(
    input_path="path/to/video.mp4",
    query="the red apple on the wooden table",
    input_type="video"
)

print(f"3D BBox: {result['3d_bbox']}")
print(f"Confidence: {result['confidence']}")
```

## 📊 输出格式

### JSON输出

```json
{
    "target_object": "apple",
    "anchor_object": "table",
    "3d_bbox": [0.5, 1.2, 0.8, 0.15, 0.15, 0.12],
    "confidence": 0.95,
    "bbox_format": "xyzwhd",
    "point_cloud": "output_scene.ply",
    "visualization": "output_3d_bbox.ply",
    "metadata": {
        "num_frames": 15,
        "num_objects": 8,
        "processing_time": 12.3
    }
}
```

### 可视化文件

- `output_scene.ply`: 重建的3D点云
- `output_3d_bbox.ply`: 带边界框的3D场景
- `output_animation.gif`: 多视角旋转动画

## 🔧 配置选项

### 模型配置

```yaml
# config/default.yaml
model:
  name: "Qwen/Qwen2-VL-7B-Instruct"
  device: "cuda"
  tensor_parallel_size: 1
  max_tokens: 512

reconstruction:
  keyframe_count: 15
  depth_model: "DPT_Large"
  min_confidence: 0.3

detection:
  yolo_model: "yolov8x.pt"
  iou_threshold: 0.5
  conf_threshold: 0.25
```

## 📁 项目结构

```
QwenGround/
├── qwenground_main.py          # 主入口
├── modules/
│   ├── perspective_adapter.py  # 视角适应模块
│   ├── reconstruction_3d.py    # 3D重建模块
│   ├── fusion_alignment.py     # 融合对齐模块
│   ├── object_lookup_table.py  # 物体查找表
│   └── visualization.py        # 可视化模块
├── utils/
│   ├── vlm_client.py           # VLM客户端
│   ├── depth_estimation.py     # 深度估计
│   └── helpers.py              # 辅助函数
├── config/
│   └── default.yaml            # 默认配置
├── requirements.txt
└── README.md
```

## 🎓 技术细节

### Perspective Adaptation Module

- 从视频提取10-20个关键帧（基于场景变化）
- 对图像序列进行视角分析和选择
- 根据查询内容优先选择相关视角

### 3D Reconstruction

- **视频模式**: OpenCV关键帧 → Open3D SfM → 稀疏点云
- **图像模式**: MiDaS深度估计 → 伪3D坐标生成
- 使用YOLOv8进行2D物体检测
- 将2D边界框投影到3D空间

### Fusion Alignment

- 使用Qwen-VL解析查询（提取target和anchor）
- 在2D视图上添加视觉提示（彩色框）
- 生成空间关系描述（"X位于Y的左上方"）
- VLM进行2D grounding → 映射到3D坐标

### Object Lookup Table

```python
OLT = {
    'object_id': 1,
    'class_name': 'apple',
    '2d_bbox': [x1, y1, x2, y2],
    '3d_bbox': [x, y, z, w, h, d],
    'confidence': 0.95,
    'frame_ids': [0, 3, 7],
    'embedding': np.array([...])
}
```

## 🔬 性能优化

- 使用vLLM加速VLM推理（2-3x加速）
- 关键帧采样减少计算量
- 多GPU并行（设置`tensor_parallel_size`）
- 混合精度推理（FP16）

## ⚠️ 已知限制

- 单物体场景效果最佳
- 需要中等质量的输入（分辨率≥720p）
- 快速运动场景可能影响重建质量
- 透明/反光物体可能定位不准

## 📝 引用

```bibtex
@inproceedings{qwenground2025,
  title={QwenGround: Zero-Shot 3D Visual Grounding with Vision-Language Models},
  author={Your Name},
  year={2025}
}

@inproceedings{li2025seeground,
  title={SeeGround: See and Ground for Zero-Shot Open-Vocabulary 3D Visual Grounding},
  author={Li et al.},
  booktitle={CVPR},
  year={2025}
}
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

