# QwenGround 架构文档

## 项目结构

```
QwenGround/
│
├── 📄 主程序文件
│   ├── qwenground_main.py          # 命令行主入口
│   └── qwenground_system.py        # 系统核心类
│
├── 📦 核心模块 (modules/)
│   ├── __init__.py
│   ├── perspective_adapter.py      # 视角适应模块
│   ├── reconstruction_3d.py        # 3D重建模块
│   ├── fusion_alignment.py         # 融合对齐模块
│   ├── object_lookup_table.py      # 物体查找表
│   └── visualization.py            # 可视化模块
│
├── 🛠️ 工具模块 (utils/)
│   ├── __init__.py
│   ├── vlm_client.py               # Qwen-VL客户端
│   ├── object_detector.py          # YOLOv8检测器
│   └── helpers.py                  # 辅助函数
│
├── ⚙️ 配置 (config/)
│   └── default.yaml                # 默认配置文件
│
├── 📚 示例 (examples/)
│   └── example_usage.py            # Python API使用示例
│
├── 🔧 脚本 (scripts/)
│   ├── deploy_vllm.sh              # vLLM部署脚本
│   └── test_installation.py        # 安装测试脚本
│
└── 📖 文档
    ├── README.md                   # 项目说明
    ├── INSTALL.md                  # 安装指南
    ├── QUICKSTART.md               # 快速入门
    ├── PROJECT_SUMMARY.md          # 项目总结
    ├── ARCHITECTURE.md             # 架构文档（本文件）
    ├── requirements.txt            # Python依赖
    └── .gitignore                  # Git忽略规则
```

## 模块依赖关系

```
qwenground_main.py
    └── qwenground_system.QwenGroundSystem
            ├── modules.perspective_adapter.PerspectiveAdapter
            ├── modules.reconstruction_3d.Reconstruction3D
            ├── modules.fusion_alignment.FusionAlignment
            │       ├── utils.vlm_client.QwenVLMClient
            │       └── utils.object_detector.ObjectDetector
            ├── modules.object_lookup_table.ObjectLookupTable
            └── modules.visualization.Visualizer
```

## 数据流图

```
┌─────────────────┐
│  输入数据        │
│ (视频/图像)      │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────┐
│  PerspectiveAdapter               │
│  - 关键帧提取                      │
│  - 视角选择                        │
└────────┬─────────────────────────┘
         │ List[KeyFrame]
         ▼
┌──────────────────────────────────┐
│  Reconstruction3D                 │
│  - 深度估计 (MiDaS)                │
│  - 点云生成                        │
│  - 下采样优化                      │
└────────┬─────────────────────────┘
         │ PointCloud3D
         ▼
┌──────────────────────────────────┐
│  ObjectDetector (YOLOv8)          │
│  - 2D物体检测                      │
│  - 边界框提取                      │
└────────┬─────────────────────────┘
         │ List[Detection]
         ▼
┌──────────────────────────────────┐
│  ObjectLookupTable                │
│  - 构建物体表                      │
│  - 2D→3D映射                      │
│  - 跨帧合并                        │
└────────┬─────────────────────────┘
         │ OLT
         ├──────────┐
         │          │
         ▼          ▼
    ┌────────┐  ┌─────────────────┐
    │  Query │  │ VLMClient       │
    │  解析   │  │ (Qwen2-VL)      │
    └───┬────┘  └────────┬────────┘
        │                │
        └────────┬───────┘
                 ▼
        ┌──────────────────┐
        │ FusionAlignment  │
        │ - 候选过滤        │
        │ - 空间关系        │
        │ - VLM验证        │
        └────────┬─────────┘
                 │ Target Object
                 ▼
        ┌──────────────────┐
        │  Visualizer      │
        │  - 3D场景        │
        │  - 边界框        │
        │  - 动画          │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │   输出结果        │
        │ - JSON           │
        │ - PLY            │
        │ - GIF            │
        └──────────────────┘
```

## 核心类设计

### 1. QwenGroundSystem

**职责**: 系统主控制器

```python
class QwenGroundSystem:
    def __init__(self, model_name, device, config)
    def run(self, input_path, query, input_type, output_dir) -> Dict
    def _create_result(self, ...) -> Dict
```

**关键方法**:
- `run()`: 执行完整流程
- 协调各模块工作
- 处理异常和结果汇总

### 2. PerspectiveAdapter

**职责**: 关键帧提取和视角管理

```python
class PerspectiveAdapter:
    def extract_keyframes_from_video(self, video_path, method) -> List[Dict]
    def load_images_from_folder(self, folder_path) -> List[Dict]
    def select_relevant_views(self, keyframes, query) -> List[Dict]
```

**关键算法**:
- 场景变化检测（直方图差异）
- 混合采样策略
- 视角相关性评估

### 3. Reconstruction3D

**职责**: 3D场景重建

```python
class Reconstruction3D:
    def estimate_depth(self, image) -> np.ndarray
    def depth_to_pointcloud(self, image, depth_map) -> PointCloud3D
    def reconstruct_from_keyframes(self, keyframes, method) -> PointCloud3D
```

**关键算法**:
- MiDaS深度估计
- 相机投影模型
- 体素下采样

### 4. ObjectLookupTable

**职责**: 物体数据管理

```python
class ObjectLookupTable:
    def add_object(self, obj: Object3D) -> int
    def find_nearest_object(self, center_3d, class_name) -> Object3D
    def find_objects_by_spatial_relation(self, anchor, relation) -> List[Object3D]
    def merge_duplicate_objects(self)
```

**数据结构**:
```python
@dataclass
class Object3D:
    object_id: int
    class_name: str
    confidence: float
    bbox_2d: List[float]      # 2D边界框
    bbox_3d: List[float]      # 3D边界框 [x,y,z,w,h,d]
    center_3d: List[float]    # 3D中心
    frame_ids: List[int]      # 出现的帧
```

### 5. FusionAlignment

**职责**: 2D-3D融合和目标定位

```python
class FusionAlignment:
    def build_olt_from_keyframes(self, keyframes, pointcloud) -> ObjectLookupTable
    def ground_target_object(self, query, keyframes, olt) -> Object3D
```

**关键流程**:
1. 查询解析 (target/anchor/relation)
2. 候选物体查找
3. 空间关系过滤
4. VLM验证

### 6. QwenVLMClient

**职责**: VLM模型接口

```python
class QwenVLMClient:
    def generate(self, messages, max_tokens, temperature) -> str
    def extract_query_components(self, query) -> Dict
    def parse_grounding_response(self, response) -> Dict
```

**支持模式**:
- 本地推理（transformers）
- API模式（vLLM）

### 7. ObjectDetector

**职责**: 2D物体检测

```python
class ObjectDetector:
    def detect(self, image) -> List[Dict]
    def detect_batch(self, images) -> List[List[Dict]]
    def draw_detections(self, image, detections) -> np.ndarray
```

**输出格式**:
```python
{
    "class_name": "apple",
    "class_id": 47,
    "confidence": 0.95,
    "bbox": [x1, y1, x2, y2],       # 像素坐标
    "bbox_norm": [x1, y1, x2, y2]   # 归一化坐标
}
```

### 8. Visualizer

**职责**: 结果可视化

```python
class Visualizer:
    def visualize_pointcloud_with_bbox(self, pointcloud, target_object)
    def create_rotation_animation(self, pointcloud, target_object)
    def generate_summary_visualization(self, pointcloud, target_object, query)
```

## 配置系统

### 配置文件结构

```yaml
# config/default.yaml

model:
  name: "Qwen/Qwen2-VL-7B-Instruct"
  device: "cuda"
  
reconstruction:
  keyframe_count: 15
  depth_model: "MiDaS_small"
  method: "depth"
  
detection:
  yolo_model: "yolov8x.pt"
  conf_threshold: 0.25
  
visualization:
  create_animation: true
  animation_frames: 36
```

### 配置优先级

1. 命令行参数（最高）
2. 自定义配置文件
3. 默认配置文件（最低）

## API接口

### 命令行接口

```bash
python qwenground_main.py \
    --input_path VIDEO.mp4 \
    --query "the red apple on the table" \
    --input_type video \
    --output_dir ./outputs
```

### Python API

```python
from qwenground_system import QwenGroundSystem

system = QwenGroundSystem(
    model_name="Qwen/Qwen2-VL-7B-Instruct",
    device="cuda"
)

result = system.run(
    input_path="video.mp4",
    query="the red apple",
    input_type="video"
)
```

## 输出格式

### JSON结果

```json
{
    "success": true,
    "query": "the red apple on the wooden table",
    "target_object": "apple",
    "anchor_object": "table",
    "spatial_relation": "on",
    "3d_bbox": [0.5, 1.2, 0.8, 0.15, 0.15, 0.12],
    "bbox_format": "xyzwhd",
    "center_3d": [0.5, 1.2, 0.8],
    "confidence": 0.95,
    "metadata": {
        "num_frames": 15,
        "num_objects": 8,
        "processing_time": 12.3,
        "model": "Qwen/Qwen2-VL-7B-Instruct",
        "device": "cuda"
    },
    "output_files": {
        "point_cloud": "outputs/pointcloud.ply",
        "animation": "outputs/animation.gif",
        ...
    }
}
```

## 性能考虑

### 内存管理
- 点云下采样（体素大小可配置）
- 关键帧数量控制
- 批处理检测

### 计算优化
- GPU加速（PyTorch, YOLOv8）
- vLLM推理加速
- 混合精度（FP16）

### 缓存策略
- 模型权重缓存
- 深度图缓存
- OLT持久化

## 错误处理

### 异常层级

```
QwenGroundSystem.run()
    ├── 输入验证失败 → 返回错误结果
    ├── 模块初始化失败 → 抛出异常
    ├── 处理失败 → 记录日志 + 返回错误结果
    └── 成功 → 返回正常结果
```

### 容错机制
- 模型加载失败 → 降级到备用模型
- VLM验证失败 → 回退到规则方法
- 可视化失败 → 跳过但不影响核心结果

## 扩展点

### 1. 自定义检测器

```python
from utils.object_detector import ObjectDetector

class MyDetector(ObjectDetector):
    def detect(self, image):
        # 自定义逻辑
        pass
```

### 2. 自定义重建方法

```python
from modules.reconstruction_3d import Reconstruction3D

class MyReconstruction(Reconstruction3D):
    def reconstruct_from_keyframes(self, keyframes):
        # 使用SLAM或其他方法
        pass
```

### 3. 自定义VLM

```python
from utils.vlm_client import QwenVLMClient

class MyVLM(QwenVLMClient):
    def generate(self, messages):
        # 使用其他VLM
        pass
```

## 测试策略

### 单元测试（待实现）
```python
# tests/test_perspective_adapter.py
# tests/test_reconstruction_3d.py
# tests/test_olt.py
```

### 集成测试
```bash
python scripts/test_installation.py
```

### 端到端测试
```bash
python qwenground_main.py --input_path test_data/video.mp4 ...
```

## 部署架构

### 单机模式

```
[用户] → [QwenGround] → [本地GPU]
```

### API服务模式

```
[用户] → [QwenGround Client]
           ↓
        [vLLM Server] (GPU)
           ↓
        [Qwen2-VL Model]
```

### 分布式模式（未来）

```
[用户] → [负载均衡器]
           ├→ [Worker 1] → [GPU Pool]
           ├→ [Worker 2] → [GPU Pool]
           └→ [Worker N] → [GPU Pool]
```

## 技术选型理由

### Qwen2-VL vs 其他VLM
- ✅ 强大的中英文理解
- ✅ 开源可部署
- ✅ 支持高分辨率图像
- ✅ 性能优异

### YOLOv8 vs 其他检测器
- ✅ 实时性能
- ✅ 易于部署
- ✅ COCO预训练
- ✅ 持续更新

### MiDaS vs 其他深度估计
- ✅ 鲁棒性强
- ✅ 零-shot泛化
- ✅ 相对深度足够
- ✅ 推理速度快

### Open3D vs 其他3D库
- ✅ 功能全面
- ✅ Python友好
- ✅ 可视化优秀
- ✅ 活跃维护

---

**文档版本**: v1.0  
**最后更新**: 2025-10-06  
**维护者**: QwenGround Team

