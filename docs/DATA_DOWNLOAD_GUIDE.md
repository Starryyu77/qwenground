# ARKitScenes 数据下载指南

## 📌 重要提示

**ARKitScenes 数据集下载遇到了 403 错误，这是因为数据集需要先接受使用协议。**

当前状态：
- ✅ ARKitScenes 仓库已克隆
- ❌ 数据集未下载（仅有目录结构，约 176KB）
- ✅ 演示数据已创建，可立即测试

---

## 🚀 快速开始（推荐）

### 选项 1: 使用演示数据（立即可用）

演示数据已经创建完成，包含 5 帧合成室内场景图像：

```bash
# 查看演示数据
ls -lh data/demo_scene/images/

# 运行测试
python qwenground_main.py \
    --input_type images \
    --input_path data/demo_scene/images \
    --query "the chair" \
    --device cpu \
    --output_dir ./outputs/demo_test
```

**优点**:
- ✅ 无需下载，立即可用
- ✅ 体积小（约 100KB）
- ✅ 适合快速验证系统功能

**缺点**:
- ❌ 简单的合成图像
- ❌ 不适合真实场景评估

---

## 📥 下载真实 ARKitScenes 数据

### 步骤 1: 接受使用协议

1. 访问 ARKitScenes 项目页面：
   ```
   https://github.com/apple/ARKitScenes
   ```

2. 阅读 README 和使用条款

3. 按照说明接受数据使用协议

### 步骤 2: 下载数据

ARKitScenes 提供了官方下载脚本。推荐下载 1-2 个验证集场景用于测试。

#### 方式 A: 下载单个场景（约 200-500 MB）

```bash
cd ../ARKitScenes

# 下载第一个验证集场景
python3 download_data.py raw --split Validation --video_id 48458663 \
    --download_dir ./data \
    --raw_dataset_assets lowres_wide lowres_depth annotation mesh lowres_wide.traj lowres_wide_intrinsics
```

#### 方式 B: 下载多个场景

```bash
cd ../ARKitScenes

# 下载 2-3 个场景用于测试
python3 download_data.py raw --split Validation \
    --video_id 48458663 42445417 41125722 \
    --download_dir ./data \
    --raw_dataset_assets lowres_wide lowres_depth annotation mesh lowres_wide.traj lowres_wide_intrinsics
```

#### 方式 C: 下载完整验证集（不推荐，数据量大）

```bash
cd ../ARKitScenes

# 下载完整 3DOD 数据集（数百 GB）
python3 download_data.py 3dod \
    --video_id_csv threedod/3dod_train_val_splits.csv \
    --download_dir ./data
```

### 步骤 3: 验证下载

```bash
# 检查数据目录
ls -lh ../ARKitScenes/data/Validation/

# 查找图像文件
find ../ARKitScenes/data -name "*.png" | head -10

# 检查数据大小（应该有数百 MB）
du -sh ../ARKitScenes/data/*
```

### 步骤 4: 运行 QwenGround 测试

```bash
cd /path/to/QwenGround

# 使用真实 ARKitScenes 数据
python qwenground_main.py \
    --input_type images \
    --input_path ../ARKitScenes/data/Validation/48458663/lowres_wide \
    --query "the chair" \
    --device cpu \
    --output_dir ./outputs/arkitscenes_test
```

---

## 🔧 故障排除

### 问题 1: 403 Forbidden 错误

**原因**: 需要接受 ARKitScenes 使用协议

**解决方案**:
1. 访问 https://github.com/apple/ARKitScenes
2. 阅读并接受使用条款
3. 如果问题持续，尝试使用 VPN 或联系项目维护者

### 问题 2: 下载速度慢

**解决方案**:
- 只下载必要的 assets（不要下载 mov 视频文件）
- 先下载 1-2 个场景测试，不要一次下载全部
- 使用稳定的网络连接

### 问题 3: 磁盘空间不足

**数据大小参考**:
- 单个场景（lowres）: ~200-500 MB
- 完整验证集: ~50 GB
- 完整训练集: ~600 GB

**建议**:
- 只下载验证集中的几个场景
- 选择 `lowres_wide` 和 `lowres_depth`，跳过高分辨率数据

---

## 📊 数据集选择对比

| 选项 | 大小 | 下载时间 | 真实性 | 用途 |
|------|------|----------|--------|------|
| 演示数据 | ~100 KB | 立即 | 合成 | 快速功能验证 |
| 1个ARKitScenes场景 | ~300 MB | 5-10分钟 | 真实 | 初步测试 |
| 3个ARKitScenes场景 | ~1 GB | 15-30分钟 | 真实 | 可靠测试 |
| 完整验证集 | ~50 GB | 几小时 | 真实 | 完整评估 |

---

## 🎯 推荐流程

**第一次使用者**:
```bash
# 1. 使用演示数据验证安装
python qwenground_main.py --input_type images --input_path data/demo_scene/images --query "the chair" --device cpu --output_dir ./outputs/demo

# 2. 如果演示成功，下载 1 个真实场景
cd ../ARKitScenes
python3 download_data.py raw --split Validation --video_id 48458663 --download_dir ./data --raw_dataset_assets lowres_wide lowres_depth annotation

# 3. 测试真实场景
cd ../QwenGround
python qwenground_main.py --input_type images --input_path ../ARKitScenes/data/Validation/48458663/lowres_wide --query "the chair" --device cpu --output_dir ./outputs/real_test
```

**研究者/开发者**:
```bash
# 下载完整验证集
cd ../ARKitScenes
python3 download_data.py 3dod --video_id_csv threedod/3dod_train_val_splits.csv --download_dir ./data

# 运行批量评估
cd ../QwenGround
python scripts/evaluate_arkitscenes.py --data_dir ../ARKitScenes/data/Validation
```

---

## 📞 获取帮助

如果遇到问题：

1. **查看 ARKitScenes 官方文档**:
   - GitHub: https://github.com/apple/ARKitScenes
   - DATA.md: 详细的数据说明

2. **检查系统要求**:
   ```bash
   python --version  # Python 3.8+
   pip list | grep torch  # PyTorch
   ```

3. **查看日志**:
   ```bash
   # QwenGround 日志
   cat outputs/demo_test/log.txt
   ```

4. **使用演示数据**:
   如果真实数据下载困难，演示数据足以验证系统功能

---

## ✅ 验证清单

下载完成后，请验证：

- [ ] 数据目录存在: `../ARKitScenes/data/Validation/`
- [ ] 有图像文件: `find ../ARKitScenes/data -name "*.png" | wc -l` 应该 > 0
- [ ] 数据大小合理: `du -sh ../ARKitScenes/data/` 应该 > 100 MB
- [ ] 可以运行 QwenGround 测试
- [ ] 输出结果包含定位信息

---

**更新时间**: 2025年10月6日  
**相关文档**: 
- `ARKITSCENES_QUICKSTART.md` - 快速开始指南
- `ARKITSCENES_TESTING.md` - 详细测试文档
- `scripts/download_arkitscenes.sh` - 下载脚本

