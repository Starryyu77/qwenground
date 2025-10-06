# 下一步操作指南

---

## 🎯 立即可做的事情

### 1. 测试演示数据（推荐，5-10分钟）

演示数据已经准备好，可以立即测试：

```bash
cd /Users/starryyu/Documents/tinghua/QwenGround

# 运行第一个测试
python qwenground_main.py \
    --input_type images \
    --input_path data/demo_scene/images \
    --query "the chair" \
    --device cpu \
    --output_dir ./outputs/demo_test

# 查看结果
cat ./outputs/demo_test/final_result.json
```

### 2. 查看演示图像

```bash
# 在 macOS 上打开图像查看
open data/demo_scene/images/frame_0002.jpg

# 或查看所有图像
open data/demo_scene/images/
```

### 3. 运行自动测试脚本

```bash
cd data/demo_scene
./run_demo_test.sh
```

---

## 📥 下载真实数据（可选）

如果您想使用真实的 ARKitScenes 数据：

### 简单方式：查看下载指南

```bash
# 运行交互式下载指南
./scripts/download_arkitscenes.sh

# 或阅读完整文档
cat docs/DATA_DOWNLOAD_GUIDE.md
```

### 快速下载一个场景

```bash
# 1. 访问并接受协议
# https://github.com/apple/ARKitScenes

# 2. 下载场景（约 300MB）
cd ../ARKitScenes
python3 download_data.py raw --split Validation --video_id 48458663 \
    --download_dir ./data \
    --raw_dataset_assets lowres_wide lowres_depth annotation mesh

# 3. 验证下载
ls -lh ./data/Validation/48458663/lowres_wide/

# 4. 使用真实数据测试
cd ../QwenGround
python qwenground_main.py \
    --input_type images \
    --input_path ../ARKitScenes/data/Validation/48458663/lowres_wide \
    --query "the chair" \
    --device cpu \
    --output_dir ./outputs/real_test
```

---

## 📚 查看文档

### 核心文档

1. **README_ARKITSCENES_STATUS.md** - 当前状态总结（从这里开始）
2. **ARKITSCENES_QUICKSTART.md** - 5分钟快速开始
3. **ARKITSCENES_TESTING.md** - 详细测试指南
4. **docs/DATA_DOWNLOAD_GUIDE.md** - 数据下载完整指南

### 快速查看

```bash
# 状态总结
cat README_ARKITSCENES_STATUS.md

# 快速开始
cat ARKITSCENES_QUICKSTART.md

# 下载指南
cat docs/DATA_DOWNLOAD_GUIDE.md
```

---

## 🔧 故障排除

### 如果演示测试失败

```bash
# 检查依赖
pip install -r requirements.txt

# 重新创建演示数据
python scripts/create_demo_data.py

# 查看系统日志
tail -f outputs/demo_test/*.log
```

### 如果下载遇到 403 错误

这是正常的，因为 ARKitScenes 需要先接受使用协议：
1. 访问 https://github.com/apple/ARKitScenes
2. 阅读并接受使用条款
3. 按照 `docs/DATA_DOWNLOAD_GUIDE.md` 中的说明操作

---

## 📊 推荐流程

### 第一次使用

```bash
# 步骤 1: 使用演示数据验证系统
cd /Users/starryyu/Documents/tinghua/QwenGround
python qwenground_main.py --input_type images --input_path data/demo_scene/images --query "the chair" --device cpu --output_dir ./outputs/demo

# 步骤 2: 查看结果
ls -lh outputs/demo/
cat outputs/demo/final_result.json

# 步骤 3: （可选）下载真实数据
./scripts/download_arkitscenes.sh
```

### 研究和开发

```bash
# 步骤 1: 确认演示数据可用
python qwenground_main.py --input_type images --input_path data/demo_scene/images --query "the chair" --device cpu --output_dir ./outputs/demo

# 步骤 2: 下载完整验证集
cd ../ARKitScenes
python3 download_data.py 3dod --video_id_csv threedod/3dod_train_val_splits.csv --download_dir ./data

# 步骤 3: 批量评估
cd ../QwenGround
python scripts/evaluate_arkitscenes.py --data_dir ../ARKitScenes/data/Validation
```

---

## ✅ 检查清单

请确认：

**立即可做**:
- [ ] 演示数据存在: `ls data/demo_scene/images/` 显示 5 个图像
- [ ] 可以运行测试: 执行演示测试命令
- [ ] 查看了相关文档: 至少阅读 `README_ARKITSCENES_STATUS.md`

**可选但推荐**:
- [ ] 已访问 ARKitScenes 项目页面
- [ ] 已接受使用协议（如需下载真实数据）
- [ ] 下载了至少 1 个真实场景
- [ ] 使用真实数据测试成功

---

## 🎉 祝贺！

ARKitScenes 集成已完成，您现在可以：

✅ 使用演示数据立即测试 QwenGround 系统  
✅ 按需下载真实 ARKitScenes 数据  
✅ 参考完整的文档和指南  
✅ 使用自动化脚本简化工作流程

**开始使用**:
```bash
python qwenground_main.py --input_type images --input_path data/demo_scene/images --query "the chair" --device cpu --output_dir ./outputs/demo_test
```

祝您使用愉快！🚀

