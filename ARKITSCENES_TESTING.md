# ARKitScenes 数据集测试指南

本文档描述如何使用 [ARKitScenes](https://github.com/apple/ARKitScenes) 数据集来测试 QwenGround 系统。

---

## 📋 关于 ARKitScenes

ARKitScenes 是由 Apple 发布的大规模 RGB-D 室内场景数据集，具有以下特点：

- **规模大**: 5,047 个场景捕获，1,661 个独特场景
- **质量高**: 使用 iPad Pro 的 LiDAR 扫描仪采集
- **标注丰富**: 包含 3D 边界框标注和场景网格
- **真实数据**: 真实室内环境的 RGB-D 数据

### 数据集特性

| 特性 | 描述 |
|------|------|
| RGB 图像 | 低分辨率 (256×192) 和高分辨率 |
| 深度图 | LiDAR 深度数据 |
| 相机位姿 | 完整的相机轨迹 |
| 3D 标注 | 家具和物体的 3D 边界框 |
| 场景网格 | ARKit 重建的 3D 网格 |

---

## 🚀 快速开始

### 1. 克隆 ARKitScenes 仓库

ARKitScenes 仓库已经克隆到：
```bash
/Users/starryyu/Documents/tinghua/ARKitScenes
```

### 2. 安装依赖

ARKitScenes 的依赖已经包含在 QwenGround 的 `requirements.txt` 中。

### 3. 准备测试数据

我们提供了一个自动化脚本来下载和准备数据：

```bash
# 进入 QwenGround 目录
cd /Users/starryyu/Documents/tinghua/QwenGround

# 运行数据准备脚本（下载3个示例场景）
python scripts/prepare_arkitscenes.py \
    --arkitscenes_dir ../ARKitScenes \
    --output_dir ./data/arkitscenes_processed \
    --num_samples 3
```

**参数说明**:
- `--arkitscenes_dir`: ARKitScenes 仓库路径
- `--output_dir`: 处理后数据的输出目录
- `--num_samples`: 要下载的场景数量（建议从 3-5 开始）
- `--skip_download`: 如果数据已下载，可以跳过下载步骤

### 4. 查看处理后的数据

```bash
# 查看处理后的场景
ls data/arkitscenes_processed/processed/

# 查看某个场景的元数据
cat data/arkitscenes_processed/processed/VIDEO_ID/metadata.json
```

每个处理后的场景包含：
- `images/`: RGB 图像序列
- `metadata.json`: 场景元数据和测试查询
- `VIDEO_ID.mp4`: 视频文件（如果 ffmpeg 可用）

---

## 🧪 运行测试

### 方法 1: 使用自动生成的测试脚本

数据准备完成后，会自动生成一个测试脚本：

```bash
cd data/arkitscenes_processed
./run_tests.sh
```

这个脚本会：
1. 对每个场景运行多个测试查询
2. 自动保存结果到 `test_outputs/`
3. 生成可视化结果

### 方法 2: 手动运行单个测试

```bash
# 使用图像序列作为输入
python qwenground_main.py \
    --input_type images \
    --input_path ./data/arkitscenes_processed/processed/VIDEO_ID/images \
    --query "the chair in the room" \
    --device cpu \
    --output_dir ./outputs/arkitscenes_test1 \
    --save_intermediate

# 使用视频作为输入（如果可用）
python qwenground_main.py \
    --input_type video \
    --input_path ./data/arkitscenes_processed/processed/VIDEO_ID/VIDEO_ID.mp4 \
    --query "the table" \
    --device cpu \
    --output_dir ./outputs/arkitscenes_test2
```

### 方法 3: 批量测试多个查询

创建一个测试脚本：

```bash
#!/bin/bash

VIDEO_ID="47333462"  # 替换为实际的 video_id
IMAGES_DIR="./data/arkitscenes_processed/processed/$VIDEO_ID/images"

# 测试多个查询
queries=(
    "the chair"
    "the table in the scene"
    "the sofa near the wall"
    "the lamp on the table"
    "the bed in the bedroom"
)

for i in "${!queries[@]}"; do
    echo "测试查询 $((i+1)): ${queries[$i]}"
    python qwenground_main.py \
        --input_type images \
        --input_path "$IMAGES_DIR" \
        --query "${queries[$i]}" \
        --device cpu \
        --output_dir "./outputs/${VIDEO_ID}/query_$((i+1))" \
        --save_intermediate
    echo "完成查询 $((i+1))"
    echo "================================"
done
```

---

## 📊 测试查询示例

根据 ARKitScenes 的标注，以下是一些常见的测试查询：

### 家具类
- "the chair"
- "the table"
- "the sofa"
- "the bed"
- "the cabinet"

### 带空间关系
- "the chair near the table"
- "the lamp on the desk"
- "the pillow on the bed"
- "the TV on the wall"

### 带属性描述
- "the large table in the center"
- "the small chair in the corner"
- "the wooden cabinet"
- "the black sofa"

### 复杂查询
- "the book on the table near the window"
- "the small lamp next to the bed"
- "the chair in front of the desk"

---

## 📁 数据结构

### ARKitScenes 原始数据结构

```
raw_data/
├── Training/
│   └── VIDEO_ID/
│       ├── lowres_wide/          # RGB 图像
│       │   ├── 0.png
│       │   ├── 1.png
│       │   └── ...
│       ├── lowres_depth/         # 深度图
│       │   ├── 0.png
│       │   └── ...
│       ├── lowres_wide_intrinsics/  # 相机内参
│       ├── lowres_wide.traj      # 相机轨迹
│       └── annotation.json       # 3D 标注
└── Validation/
    └── ...
```

### 处理后的数据结构

```
processed/
└── VIDEO_ID/
    ├── images/                # RGB 图像序列
    │   ├── 000000.png
    │   ├── 000001.png
    │   └── ...
    ├── VIDEO_ID.mp4          # 视频文件（可选）
    └── metadata.json         # 元数据和查询
```

### metadata.json 格式

```json
{
  "video_id": "47333462",
  "split": "Validation",
  "video_path": "processed/47333462/47333462.mp4",
  "images_dir": "processed/47333462/images",
  "num_images": 120,
  "annotations": [
    {
      "label": "chair",
      "bbox": [...],
      "uid": "..."
    }
  ],
  "test_queries": [
    "the chair",
    "find the chair in the scene",
    "the table"
  ]
}
```

---

## 🔍 评估和分析

### 1. 查看结果

测试完成后，检查输出目录：

```bash
ls outputs/arkitscenes_test1/

# 输出文件:
# - final_result.json          # 最终结果
# - visualization.png          # 可视化图像
# - point_cloud.ply           # 3D 点云（如果启用）
# - intermediate/             # 中间结果（如果启用）
```

### 2. 可视化结果

```python
import json
import matplotlib.pyplot as plt
from PIL import Image

# 读取结果
with open('outputs/arkitscenes_test1/final_result.json', 'r') as f:
    result = json.load(f)

# 显示可视化
img = Image.open('outputs/arkitscenes_test1/visualization.png')
plt.figure(figsize=(12, 8))
plt.imshow(img)
plt.axis('off')
plt.title(f"Query: {result['query']}")
plt.show()

# 打印检测结果
print(f"查询: {result['query']}")
print(f"找到物体: {result.get('found', False)}")
if 'target_3d_location' in result:
    print(f"3D位置: {result['target_3d_location']}")
```

### 3. 与 Ground Truth 对比

```python
import json

# 读取 ARKitScenes 标注
with open('data/arkitscenes_processed/raw_data/Validation/VIDEO_ID/annotation.json', 'r') as f:
    gt_annotations = json.load(f)

# 读取 QwenGround 结果
with open('outputs/arkitscenes_test1/final_result.json', 'r') as f:
    pred_result = json.load(f)

# 对比分析
# TODO: 实现 IoU 计算、定位精度评估等
```

---

## ⚙️ 高级配置

### 自定义配置文件

创建 `config/arkitscenes_config.yaml`:

```yaml
# ARKitScenes 特定配置
perspective_adapter:
  keyframe_count: 15  # ARKitScenes 场景通常较大
  use_motion_analysis: true

reconstruction_3d:
  midas_model: "DPT_Large"  # 使用大模型获得更好精度
  depth_scale: 1000.0  # ARKitScenes 深度单位是毫米
  
visualization:
  show_3d: true
  save_point_cloud: true
```

使用配置：

```bash
python qwenground_main.py \
    --input_type images \
    --input_path ./data/arkitscenes_processed/processed/VIDEO_ID/images \
    --query "the chair" \
    --config config/arkitscenes_config.yaml \
    --device cpu
```

---

## 📈 性能优化

### 对于大规模测试

如果要测试大量场景，建议：

1. **使用 GPU**（如果可用）:
   ```bash
   --device cuda
   ```

2. **使用 API 模式部署 VLM**:
   ```bash
   # 启动 vLLM 服务器
   bash scripts/deploy_vllm.sh
   
   # 使用 API 模式
   python qwenground_main.py --use_api --api_url http://localhost:8000/v1
   ```

3. **减少关键帧数量**:
   ```bash
   # 在配置文件中设置
   perspective_adapter:
     keyframe_count: 10  # 默认 20
   ```

4. **批量处理**:
   ```python
   # 创建批处理脚本
   for video_id in video_ids:
       # 并行处理多个场景
   ```

---

## 🐛 常见问题

### Q1: 下载数据失败

**A**: ARKitScenes 数据托管在 AWS S3，确保网络连接正常。如果下载失败：
- 检查网络连接
- 重试下载命令
- 使用较小的 `--num_samples` 值

### Q2: 内存不足

**A**: ARKitScenes 场景可能很大。解决方案：
- 减少关键帧数量
- 使用较小的 MiDaS 模型
- 增加系统交换空间

### Q3: 处理速度慢

**A**: 在 CPU 模式下处理较慢是正常的。优化方法：
- 使用 GPU (`--device cuda`)
- 部署 vLLM API 服务器
- 减少输入帧数

### Q4: 找不到标注文件

**A**: 确保下载了完整的 3DOD 数据集：
```bash
python download_data.py 3dod --video_id VIDEO_ID --split Validation
```

---

## 📚 参考资源

### ARKitScenes 论文
```bibtex
@inproceedings{dehghan2021arkitscenes,
  title={{ARK}itScenes - A Diverse Real-World Dataset for 3D Indoor Scene Understanding Using Mobile {RGB}-D Data},
  author={Gilad Baruch and Zhuoyuan Chen and Afshin Dehghan and Tal Dimry and Yuri Feigin and Peter Fu and Thomas Gebauer and Brandon Joffe and Daniel Kurz and Arik Schwartz and Elad Shulman},
  booktitle={Thirty-fifth Conference on Neural Information Processing Systems Datasets and Benchmarks Track (Round 1)},
  year={2021},
  url={https://openreview.net/forum?id=tjZjv_qh_CE}
}
```

### 相关链接
- [ARKitScenes GitHub](https://github.com/apple/ARKitScenes)
- [ARKitScenes 论文](https://openreview.net/forum?id=tjZjv_qh_CE)
- [ARKitScenes 数据文档](https://github.com/apple/ARKitScenes/blob/main/DATA.md)

---

## 🎯 测试清单

在完成测试后，检查以下项目：

- [ ] 成功下载至少 3 个 ARKitScenes 场景
- [ ] 数据准备脚本运行成功
- [ ] 生成了测试脚本和元数据
- [ ] 运行了至少一个完整的测试
- [ ] 查看了可视化结果
- [ ] 保存了中间结果用于分析
- [ ] 与 Ground Truth 进行了对比（可选）
- [ ] 记录了性能指标（处理时间、精度等）

---

## ✅ 总结

使用 ARKitScenes 测试 QwenGround 的步骤：

1. ✅ 克隆 ARKitScenes 仓库
2. ✅ 运行数据准备脚本
3. ✅ 查看处理后的数据
4. 🔄 运行测试（自动或手动）
5. 📊 分析和可视化结果
6. 📈 评估性能和精度

**祝测试顺利！** 🚀

如有问题，请参考 [QwenGround 主文档](README.md) 或提交 Issue。

