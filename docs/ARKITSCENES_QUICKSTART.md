# ARKitScenes 快速测试指南

这是一个 5 分钟快速开始指南，帮助您使用 ARKitScenes 数据集测试 QwenGround 系统。

---

## 🚀 快速开始（5分钟）

### 步骤 1: 下载示例数据（2-3分钟）

```bash
cd /Users/starryyu/Documents/tinghua/QwenGround

# 下载 1 个示例场景进行快速测试
python scripts/prepare_arkitscenes.py \
    --arkitscenes_dir ../ARKitScenes \
    --output_dir ./data/arkitscenes_test \
    --num_samples 1
```

**预期输出**:
```
准备下载 1 个ARKitScenes样本...
选择的video_ids: ['48458663']  # 示例ID
下载 video_id: 48458663...
✓ 成功下载 48458663
```

**注意**: 
- 首次下载需要网络连接
- 单个场景约 100-200MB
- 如果下载失败，请检查网络连接并重试

---

### 步骤 2: 查看下载的数据（30秒）

```bash
# 查看处理后的场景
ls data/arkitscenes_test/processed/

# 查看场景内容（假设 video_id 是 48458663）
ls data/arkitscenes_test/processed/48458663/

# 输出应该包含:
# - images/           # RGB 图像序列
# - metadata.json     # 场景元数据
# - *.mp4            # 视频文件（如果 ffmpeg 可用）
```

查看元数据中的测试查询：

```bash
# 查看可用的测试查询
cat data/arkitscenes_test/processed/*/metadata.json | grep -A 5 "test_queries"
```

---

### 步骤 3: 运行第一个测试（1-2分钟）

```bash
# 获取实际的 video_id
VIDEO_ID=$(ls data/arkitscenes_test/processed/ | head -n 1)
echo "使用场景: $VIDEO_ID"

# 运行测试
python qwenground_main.py \
    --input_type images \
    --input_path data/arkitscenes_test/processed/$VIDEO_ID/images \
    --query "the chair" \
    --device cpu \
    --output_dir ./outputs/arkitscenes_demo \
    --save_intermediate
```

**预期行为**:
1. 🔄 首次运行会下载模型（YOLOv8、MiDaS、Qwen2-VL）
2. ⏱️ CPU 模式处理较慢，请耐心等待
3. 📊 会显示进度条和处理状态
4. ✅ 完成后会保存结果到 `outputs/arkitscenes_demo/`

---

### 步骤 4: 查看结果（30秒）

```bash
# 查看输出文件
ls outputs/arkitscenes_demo/

# 查看最终结果
cat outputs/arkitscenes_demo/final_result.json

# 查看可视化（在 macOS 上）
open outputs/arkitscenes_demo/visualization.png
```

---

## 📊 示例输出

### final_result.json 内容示例

```json
{
  "query": "the chair",
  "found": true,
  "target_object": "chair",
  "target_frame_id": 15,
  "target_2d_bbox": [120, 80, 250, 200],
  "target_3d_location": [1.2, 0.5, 2.3],
  "confidence": 0.87,
  "processing_time": 45.2
}
```

### 可视化图像

可视化图像会显示：
- 🎯 检测到的目标物体（红框标注）
- 📷 关键帧视图
- 🗺️ 3D 点云（如果启用）

---

## 🔄 运行更多测试

### 测试不同的查询

```bash
VIDEO_ID=$(ls data/arkitscenes_test/processed/ | head -n 1)

# 测试 1: 简单物体
python qwenground_main.py \
    --input_type images \
    --input_path data/arkitscenes_test/processed/$VIDEO_ID/images \
    --query "the table" \
    --device cpu \
    --output_dir ./outputs/test_table

# 测试 2: 带空间关系
python qwenground_main.py \
    --input_type images \
    --input_path data/arkitscenes_test/processed/$VIDEO_ID/images \
    --query "the chair near the table" \
    --device cpu \
    --output_dir ./outputs/test_chair_near_table

# 测试 3: 复杂查询
python qwenground_main.py \
    --input_type images \
    --input_path data/arkitscenes_test/processed/$VIDEO_ID/images \
    --query "the lamp on the desk" \
    --device cpu \
    --output_dir ./outputs/test_lamp
```

### 使用自动生成的测试脚本

```bash
# 运行所有预定义的测试
cd data/arkitscenes_test
./run_tests.sh
```

---

## ⚡ 性能提示

### 如果有 CUDA GPU

```bash
python qwenground_main.py \
    --input_type images \
    --input_path data/arkitscenes_test/processed/$VIDEO_ID/images \
    --query "the chair" \
    --device cuda \
    --output_dir ./outputs/test_gpu
```

**速度提升**: GPU 模式通常快 5-10 倍

### 减少处理时间

编辑配置文件 `config/default.yaml`:

```yaml
perspective_adapter:
  keyframe_count: 10  # 默认 20，减少可加速

reconstruction_3d:
  midas_model: "MiDaS_small"  # 使用小模型，速度更快
```

然后运行：

```bash
python qwenground_main.py \
    --input_type images \
    --input_path data/arkitscenes_test/processed/$VIDEO_ID/images \
    --query "the chair" \
    --config config/default.yaml \
    --device cpu
```

---

## 🐛 故障排除

### 问题 1: 下载失败

```bash
# 错误: Connection timeout 或 Download failed

# 解决方案: 重试下载
python scripts/prepare_arkitscenes.py \
    --arkitscenes_dir ../ARKitScenes \
    --output_dir ./data/arkitscenes_test \
    --num_samples 1
```

### 问题 2: 内存不足

```bash
# 错误: OOM (Out of Memory)

# 解决方案: 减少关键帧数
# 编辑 config/default.yaml:
#   keyframe_count: 5  # 从 20 减少到 5
```

### 问题 3: 模型下载慢

```bash
# 首次运行会下载模型，需要时间

# 解决方案 1: 耐心等待
# 解决方案 2: 使用国内镜像（如果可用）
export HF_ENDPOINT=https://hf-mirror.com
```

### 问题 4: CUDA 不可用

```bash
# 在 macOS 上 CUDA 不可用是正常的

# 解决方案: 使用 CPU 模式
--device cpu

# 或者在 Linux/Windows with NVIDIA GPU 上运行
```

---

## 📈 批量测试（下载更多数据）

如果第一个测试成功，可以下载更多场景：

```bash
# 下载 5 个场景
python scripts/prepare_arkitscenes.py \
    --arkitscenes_dir ../ARKitScenes \
    --output_dir ./data/arkitscenes_full \
    --num_samples 5

# 运行批量测试
cd data/arkitscenes_full
./run_tests.sh
```

**预计时间**:
- 下载 5 个场景: ~5-10 分钟（取决于网络）
- 处理每个场景: ~2-5 分钟（CPU 模式）
- 总计: ~20-30 分钟

---

## ✅ 测试检查清单

完成以下步骤确保测试成功：

- [ ] ✅ 成功下载至少 1 个 ARKitScenes 场景
- [ ] ✅ 数据处理完成，生成了 metadata.json
- [ ] ✅ 运行了第一个测试命令
- [ ] ✅ 查看了 final_result.json
- [ ] ✅ 查看了可视化图像
- [ ] 🔄 尝试了不同的查询（可选）
- [ ] 🔄 运行了批量测试（可选）

---

## 🎯 下一步

### 完整测试

查看详细的测试指南：

```bash
cat ARKITSCENES_TESTING.md
```

### 自定义配置

了解如何调整系统参数以获得最佳性能：

```bash
cat QUICKSTART.md  # QwenGround 快速入门
cat README.md      # 完整文档
```

### 评估结果

编写评估脚本来分析结果：

```python
import json
import glob

# 收集所有测试结果
results = []
for result_file in glob.glob("outputs/*/final_result.json"):
    with open(result_file, 'r') as f:
        results.append(json.load(f))

# 统计
total = len(results)
found = sum(1 for r in results if r.get('found', False))
avg_time = sum(r.get('processing_time', 0) for r in results) / total

print(f"总测试数: {total}")
print(f"成功找到: {found} ({found/total*100:.1f}%)")
print(f"平均处理时间: {avg_time:.1f}秒")
```

---

## 📞 获取帮助

如果遇到问题：

1. 查看详细文档: `ARKITSCENES_TESTING.md`
2. 查看系统文档: `README.md`
3. 检查日志文件: `outputs/*/qwenground.log`
4. 提交 Issue 或联系维护者

---

## 🎉 恭喜！

如果您完成了上述步骤，说明 QwenGround 系统已经成功在 ARKitScenes 数据集上运行！

**接下来可以**:
- 📊 下载更多场景进行大规模测试
- 🔧 调整配置以优化性能
- 📈 评估和分析结果
- 🚀 在自己的数据上测试

**祝测试愉快！** 🚀

