# QwenGround 安装指南

## 系统要求

### 硬件要求

- **GPU**: NVIDIA GPU（推荐）
  - 7B模型: 至少16GB VRAM (RTX 3090/4090, A100)
  - 72B模型: 至少80GB VRAM (A100-80GB, H100)
- **CPU**: 如果没有GPU也可运行（但速度较慢）
- **内存**: 至少32GB RAM
- **存储**: 至少50GB可用空间

### 软件要求

- **操作系统**: Linux (推荐), macOS, Windows (WSL2)
- **Python**: 3.10+
- **CUDA**: 11.8+ (如果使用GPU)
- **PyTorch**: 2.0+

## 安装步骤

### 1. 克隆或下载项目

```bash
cd /Users/starryyu/Documents/tinghua/QwenGround
```

### 2. 创建虚拟环境（推荐）

```bash
# 使用conda
conda create -n qwenground python=3.10
conda activate qwenground

# 或使用venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
```

### 3. 安装PyTorch

根据你的CUDA版本安装PyTorch：

```bash
# CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# CPU版本（不推荐）
pip install torch torchvision
```

验证安装：

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

### 4. 安装其他依赖

```bash
pip install -r requirements.txt
```

### 5. (可选) 安装COLMAP

对于更好的3D重建效果，安装COLMAP：

```bash
# Ubuntu/Debian
sudo apt-get install colmap

# macOS
brew install colmap

# 或从源码编译: https://colmap.github.io/install.html
```

### 6. 下载模型权重

#### Qwen2-VL模型

模型会在首次运行时自动下载，或手动下载：

```bash
# 使用huggingface-cli
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2-VL-7B-Instruct

# 或者在Python中
from transformers import Qwen2VLForConditionalGeneration
model = Qwen2VLForConditionalGeneration.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")
```

#### YOLO模型

YOLOv8模型会在首次运行时自动下载。

#### MiDaS深度估计模型

MiDaS模型会在首次运行时自动下载。

### 7. 测试安装

```bash
python scripts/test_installation.py
```

如果看到 "✅ 所有测试通过!"，说明安装成功。

## 常见问题

### 1. CUDA内存不足

如果遇到CUDA OOM错误：

- 使用更小的模型（如Qwen2-VL-2B）
- 减少关键帧数量（修改config中的`keyframe_count`）
- 使用API模式部署vLLM

### 2. 依赖冲突

如果遇到依赖冲突：

```bash
# 清理环境
pip uninstall -y torch torchvision transformers
pip cache purge

# 重新安装
pip install -r requirements.txt
```

### 3. Open3D可视化问题

如果在服务器上运行（无显示器）：

- 设置`show_interactive: false`（配置文件中）
- 或使用`--no_visualize`参数

### 4. MiDaS下载失败

如果MiDaS模型下载失败：

```bash
# 手动下载
python -c "import torch; torch.hub.load('intel-isl/MiDaS', 'MiDaS_small')"
```

### 5. vLLM部署问题

对于vLLM API模式：

```bash
# 安装vLLM
pip install vllm

# 启动服务器
bash scripts/deploy_vllm.sh

# 或手动启动
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2-VL-7B-Instruct \
    --host 0.0.0.0 \
    --port 8000
```

## 性能优化

### 1. 使用混合精度

系统默认在GPU上使用FP16，无需额外配置。

### 2. 调整批处理大小

修改配置文件以优化性能：

```yaml
reconstruction:
  keyframe_count: 10  # 减少以加速
  
detection:
  conf_threshold: 0.3  # 提高以减少检测数量
```

### 3. 使用更轻量的模型

```yaml
model:
  name: "Qwen/Qwen2-VL-2B-Instruct"  # 更小的模型

detection:
  yolo_model: "yolov8m.pt"  # 中等大小的YOLO
  
reconstruction:
  depth_model: "MiDaS_small"  # 更快的深度模型
```

## 更新

更新到最新版本：

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

## 卸载

```bash
# 删除虚拟环境
conda env remove -n qwenground
# 或
rm -rf venv

# 删除项目
rm -rf /path/to/QwenGround
```

## 获取帮助

如果遇到问题：

1. 查看日志文件（如果启用了日志记录）
2. 运行测试脚本获取详细信息：`python scripts/test_installation.py`
3. 检查GPU状态：`nvidia-smi`
4. 提交Issue（如果是Bug）

