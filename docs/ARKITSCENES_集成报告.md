# ARKitScenes 数据集集成报告

**日期**: 2025年10月6日  
**项目**: QwenGround  
**任务**: 集成 ARKitScenes 数据集进行测试

---

## 📋 执行总结

### 完成的工作

✅ **步骤 1**: 克隆 ARKitScenes 仓库  
✅ **步骤 2**: 创建数据准备脚本和下载指南  
✅ **步骤 3**: 创建测试文档  
✅ **步骤 4**: 提供快速开始指南  
✅ **步骤 5**: 创建演示数据用于快速测试

### 重要提示 ⚠️

**ARKitScenes 数据集下载需要接受使用协议**

由于 ARKitScenes 数据集的访问限制，您需要：
1. 访问 https://github.com/apple/ARKitScenes
2. 阅读并接受使用条款
3. 使用官方下载脚本手动下载数据

**快速开始选项**：
- ✅ **演示数据**: 已创建合成测试数据，可立即运行测试
- 📥 **真实数据**: 参考 `scripts/download_arkitscenes.sh` 下载真实场景

### 交付物清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `scripts/prepare_arkitscenes.py` | Python脚本 | 自动下载和处理ARKitScenes数据 |
| `scripts/download_arkitscenes.sh` | Shell脚本 | ARKitScenes 下载详细指南 |
| `scripts/create_demo_data.py` | Python脚本 | 创建演示数据用于快速测试 |
| `data/demo_scene/` | 数据目录 | 合成的演示场景（5帧图像） |
| `ARKITSCENES_TESTING.md` | 文档 | 详细的测试指南（包含数据结构、评估等） |
| `ARKITSCENES_QUICKSTART.md` | 文档 | 5分钟快速开始指南 |
| `ARKITSCENES_集成报告.md` | 文档 | 本报告 |

---

## 🎯 ARKitScenes 数据集概述

### 数据集信息

- **来源**: Apple Research
- **论文**: [ARKitScenes - NeurIPS 2021](https://openreview.net/forum?id=tjZjv_qh_CE)
- **GitHub**: https://github.com/apple/ARKitScenes
- **规模**: 5,047 个场景捕获，1,661 个独特场景

### 数据特点

| 特性 | 描述 |
|------|------|
| **RGB 图像** | 256×192 像素（低分辨率），适合快速测试 |
| **深度数据** | iPad Pro LiDAR 扫描的深度图 |
| **相机位姿** | 完整的 6-DoF 轨迹 |
| **3D 标注** | 家具和物体的 3D 定向边界框 |
| **场景类型** | 真实室内环境（客厅、卧室、厨房等） |

### 为什么选择 ARKitScenes？

1. ✅ **真实数据**: 真实的室内环境，不是合成数据
2. ✅ **丰富标注**: 3D 边界框标注，适合评估
3. ✅ **多样场景**: 1,600+ 个不同的场景
4. ✅ **高质量**: 使用 iPad Pro 专业设备采集
5. ✅ **RGB-D**: 同时提供 RGB 和深度数据
6. ✅ **相机位姿**: 可以评估 3D 重建精度

---

## 🛠️ 集成方案

### 技术架构

```
ARKitScenes 数据集
        ↓
[prepare_arkitscenes.py]
        ↓
处理后的数据
├── images/              # RGB 图像序列
├── metadata.json        # 场景元数据
└── VIDEO_ID.mp4        # 视频文件（可选）
        ↓
QwenGround 系统
├── 视角适应模块
├── 3D 重建模块
├── 物体检测模块
└── VLM 理解模块
        ↓
测试结果
├── final_result.json    # 检测结果
├── visualization.png    # 可视化
└── point_cloud.ply     # 3D 点云
```

### 数据处理流程

```python
# prepare_arkitscenes.py 的核心功能

1. download_sample_data()
   - 从 ARKitScenes 下载指定数量的场景
   - 自动选择验证集场景（文件较小）

2. convert_to_video()
   - 将图像序列转换为视频（可选）
   - 保留原始图像序列

3. extract_annotations()
   - 提取 3D 边界框标注
   - 解析物体标签

4. generate_test_queries()
   - 根据标注自动生成测试查询
   - 生成不同复杂度的查询

5. generate_test_script()
   - 生成自动化测试脚本
   - 批量运行多个测试
```

---

## 📖 使用指南

### 快速开始（3步）

#### 步骤 1: 下载数据

```bash
cd /Users/starryyu/Documents/tinghua/QwenGround

python scripts/prepare_arkitscenes.py \
    --arkitscenes_dir ../ARKitScenes \
    --output_dir ./data/arkitscenes_test \
    --num_samples 1
```

**预期输出**:
```
准备下载 1 个ARKitScenes样本...
选择的video_ids: ['48458663']
下载 video_id: 48458663...
✓ 成功下载 48458663
✓ 复制了图像序列
✓ 保存元数据
```

#### 步骤 2: 运行测试

```bash
VIDEO_ID=$(ls data/arkitscenes_test/processed/ | head -n 1)

python qwenground_main.py \
    --input_type images \
    --input_path data/arkitscenes_test/processed/$VIDEO_ID/images \
    --query "the chair" \
    --device cpu \
    --output_dir ./outputs/arkitscenes_demo \
    --save_intermediate
```

#### 步骤 3: 查看结果

```bash
cat outputs/arkitscenes_demo/final_result.json
open outputs/arkitscenes_demo/visualization.png
```

### 批量测试

```bash
# 下载更多场景
python scripts/prepare_arkitscenes.py \
    --arkitscenes_dir ../ARKitScenes \
    --output_dir ./data/arkitscenes_full \
    --num_samples 5

# 运行自动生成的测试脚本
cd data/arkitscenes_full
./run_tests.sh
```

---

## 🧪 测试场景

### 推荐的测试查询

根据 ARKitScenes 的标注类别，以下是推荐的测试查询：

#### 1. 简单物体查询
```
- "the chair"
- "the table"
- "the sofa"
- "the bed"
- "the cabinet"
```

#### 2. 空间关系查询
```
- "the chair near the table"
- "the lamp on the desk"
- "the pillow on the bed"
- "the TV on the wall"
```

#### 3. 属性描述查询
```
- "the large table in the center"
- "the small chair in the corner"
- "the wooden cabinet"
```

#### 4. 复杂查询
```
- "the book on the table near the window"
- "the small lamp next to the bed"
- "the chair in front of the desk"
```

---

## 📊 预期结果

### 输出文件结构

```
outputs/arkitscenes_demo/
├── final_result.json          # 最终检测结果
├── visualization.png          # 可视化图像
├── point_cloud.ply           # 3D点云（如果启用）
├── qwenground.log            # 日志文件
└── intermediate/             # 中间结果
    ├── keyframes/            # 关键帧
    ├── detections/           # 物体检测
    └── depth_maps/           # 深度图
```

### final_result.json 示例

```json
{
  "query": "the chair",
  "found": true,
  "target_object": "chair",
  "target_frame_id": 15,
  "target_2d_bbox": [120, 80, 250, 200],
  "target_3d_location": [1.2, 0.5, 2.3],
  "confidence": 0.87,
  "processing_time": 45.2,
  "num_keyframes": 20,
  "num_detections": 8
}
```

---

## 🔍 评估方法

### 定性评估

1. **视觉检查**: 查看可视化结果，确认检测框位置
2. **3D 可视化**: 使用 MeshLab 或 CloudCompare 查看点云
3. **日志分析**: 检查处理日志，确认各模块正常工作

### 定量评估（高级）

对于更严格的评估，可以：

1. **定位精度**: 计算预测的 3D 位置与 Ground Truth 的距离
2. **检测准确率**: 统计成功找到目标物体的比例
3. **处理时间**: 记录平均处理时间
4. **IoU 评估**: 计算 2D/3D 边界框的 IoU

#### 评估脚本示例

```python
import json
import numpy as np
from pathlib import Path

def evaluate_results(results_dir, gt_dir):
    """评估测试结果"""
    
    results = []
    for result_file in Path(results_dir).glob("*/final_result.json"):
        with open(result_file) as f:
            results.append(json.load(f))
    
    # 统计
    total = len(results)
    found = sum(1 for r in results if r.get('found', False))
    avg_time = np.mean([r.get('processing_time', 0) for r in results])
    avg_conf = np.mean([r.get('confidence', 0) for r in results if r.get('found')])
    
    print(f"评估结果:")
    print(f"  总测试数: {total}")
    print(f"  成功检测: {found} ({found/total*100:.1f}%)")
    print(f"  平均处理时间: {avg_time:.1f}秒")
    print(f"  平均置信度: {avg_conf:.2f}")
    
    return {
        'total': total,
        'found': found,
        'accuracy': found/total,
        'avg_time': avg_time,
        'avg_confidence': avg_conf
    }

# 使用
metrics = evaluate_results("./outputs", "./data/arkitscenes_test")
```

---

## ⚙️ 配置优化

### 针对 ARKitScenes 的推荐配置

创建 `config/arkitscenes_config.yaml`:

```yaml
# ARKitScenes 特定配置

perspective_adapter:
  keyframe_count: 15              # ARKitScenes 场景较大，增加关键帧
  use_motion_analysis: true       # 利用相机运动信息
  motion_threshold: 0.5           # 运动阈值

reconstruction_3d:
  midas_model: "DPT_Large"        # 使用大模型提高精度
  depth_scale: 1000.0             # ARKitScenes 深度单位是毫米
  max_depth: 10.0                 # 室内场景最大深度 10 米
  point_cloud_resolution: 0.01    # 点云分辨率 1cm

vlm:
  model_name: "Qwen/Qwen2-VL-7B-Instruct"
  max_length: 2048
  temperature: 0.1                # 降低温度提高稳定性

visualization:
  show_3d: true
  save_point_cloud: true
  point_cloud_format: "ply"
  visualization_size: [1920, 1080]
```

使用配置：

```bash
python qwenground_main.py \
    --input_type images \
    --input_path data/arkitscenes_test/processed/$VIDEO_ID/images \
    --query "the chair" \
    --config config/arkitscenes_config.yaml \
    --device cpu
```

---

## 📈 性能指标

### 预期性能（参考值）

| 指标 | CPU 模式 | GPU 模式 |
|------|----------|----------|
| **处理时间（单场景）** | 2-5 分钟 | 30-60 秒 |
| **内存占用** | ~4-8 GB | ~6-10 GB |
| **模型下载时间** | ~30-60 分钟 | ~30-60 分钟 |
| **数据下载时间（单场景）** | ~1-3 分钟 | ~1-3 分钟 |

### 优化建议

1. **使用 GPU**: 速度提升 5-10 倍
2. **减少关键帧**: 从 20 减少到 10-15
3. **使用小模型**: MiDaS_small 代替 DPT_Large
4. **API 模式**: 部署 vLLM 服务器

---

## 🐛 已知问题和解决方案

### 问题 1: 下载失败

**现象**: `Connection timeout` 或 `Download failed`

**原因**: 网络连接问题或 AWS S3 限速

**解决方案**:
```bash
# 重试下载
python scripts/prepare_arkitscenes.py \
    --arkitscenes_dir ../ARKitScenes \
    --output_dir ./data/arkitscenes_test \
    --num_samples 1

# 或使用 --skip_download 跳过已下载的场景
```

### 问题 2: 内存不足

**现象**: `OOM (Out of Memory)`

**原因**: 图像序列过长或点云过大

**解决方案**:
```yaml
# 在配置文件中减少资源使用
perspective_adapter:
  keyframe_count: 10  # 从 20 减少

reconstruction_3d:
  point_cloud_resolution: 0.02  # 降低点云密度
```

### 问题 3: CUDA 不可用

**现象**: `CUDA not available`

**原因**: macOS 不支持 CUDA

**解决方案**:
```bash
# 使用 CPU 模式（已默认）
--device cpu

# 或在 CUDA 环境下运行
--device cuda
```

---

## 📚 相关资源

### ARKitScenes 相关

- **论文**: [ARKitScenes - NeurIPS 2021](https://openreview.net/forum?id=tjZjv_qh_CE)
- **GitHub**: https://github.com/apple/ARKitScenes
- **数据文档**: [DATA.md](https://github.com/apple/ARKitScenes/blob/main/DATA.md)

### QwenGround 文档

- **README**: 项目主文档
- **QUICKSTART**: 快速入门指南
- **ARCHITECTURE**: 架构设计文档
- **INSTALL**: 安装指南

### 引用

如果使用 ARKitScenes 数据集，请引用：

```bibtex
@inproceedings{dehghan2021arkitscenes,
  title={{ARK}itScenes - A Diverse Real-World Dataset for 3D Indoor Scene Understanding Using Mobile {RGB}-D Data},
  author={Gilad Baruch and Zhuoyuan Chen and Afshin Dehghan and Tal Dimry and Yuri Feigin and Peter Fu and Thomas Gebauer and Brandon Joffe and Daniel Kurz and Arik Schwartz and Elad Shulman},
  booktitle={Thirty-fifth Conference on Neural Information Processing Systems Datasets and Benchmarks Track (Round 1)},
  year={2021},
  url={https://openreview.net/forum?id=tjZjv_qh_CE}
}
```

---

## ✅ 集成检查清单

在完成 ARKitScenes 集成后，确认以下项目：

- [x] ✅ 克隆 ARKitScenes 仓库
- [x] ✅ 创建数据准备脚本
- [x] ✅ 创建测试文档
- [x] ✅ 提供快速开始指南
- [ ] 🔄 下载至少 1 个测试场景（待用户执行）
- [ ] 🔄 运行第一个测试（待用户执行）
- [ ] 🔄 查看和验证结果（待用户执行）
- [ ] 🔄 进行批量测试（可选）
- [ ] 🔄 评估和分析性能（可选）

---

## 🎯 下一步行动

### 立即可做

1. **下载数据**: 运行数据准备脚本
   ```bash
   python scripts/prepare_arkitscenes.py \
       --arkitscenes_dir ../ARKitScenes \
       --output_dir ./data/arkitscenes_test \
       --num_samples 1
   ```

2. **运行测试**: 执行第一个测试
   ```bash
   # 参考 ARKITSCENES_QUICKSTART.md
   ```

3. **查看结果**: 分析输出文件

### 进阶任务

1. **批量测试**: 下载多个场景，运行批量测试
2. **性能评估**: 统计成功率、处理时间等
3. **优化配置**: 调整参数以获得最佳性能
4. **对比评估**: 与 Ground Truth 进行定量对比

---

## 📞 支持

如遇到问题：

1. 查看文档: `ARKITSCENES_QUICKSTART.md` 或 `ARKITSCENES_TESTING.md`
2. 检查日志: `outputs/*/qwenground.log`
3. 提交 Issue 或联系维护者

---

## 🎉 总结

ARKitScenes 数据集已成功集成到 QwenGround 测试流程中：

✅ **完成的工作**:
- 克隆数据集仓库
- 创建自动化准备脚本
- 编写详细测试文档
- 提供快速开始指南

🚀 **系统状态**: 准备就绪，可以立即开始测试

📖 **文档**: 提供了完整的使用指南和故障排除方案

**测试准备完成！** 现在可以使用真实的 RGB-D 数据测试 QwenGround 系统了！

---

**集成日期**: 2025年10月6日  
**集成人员**: AI Coding Assistant  
**状态**: ✅ 完成

