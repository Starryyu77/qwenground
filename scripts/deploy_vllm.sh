#!/bin/bash
# QwenGround vLLM 部署脚本

set -e

echo "=========================================="
echo "QwenGround vLLM 部署脚本"
echo "=========================================="

# 配置参数（通过环境变量传入，避免在仓库中硬编码密钥）
MODEL_NAME=${MODEL_NAME:-"Qwen/Qwen2-VL-7B-Instruct"}
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8000}
GPU_COUNT=${GPU_COUNT:-1}
API_KEY=${API_KEY:-""}

echo ""
echo "配置信息:"
echo "  模型: $MODEL_NAME"
echo "  地址: $HOST:$PORT"
echo "  GPU数量: $GPU_COUNT"
if [ -z "$API_KEY" ]; then
  echo "  API密钥: [未设置] (请通过环境变量 API_KEY 提供)"
else
  echo "  API密钥: [已提供]"
fi
echo ""

# 检查vLLM是否安装
if ! python -c "import vllm" 2>/dev/null; then
    echo "❌ vLLM未安装"
    echo "请运行: pip install vllm"
    exit 1
fi

echo "✓ vLLM已安装"

# 检查GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️  警告: nvidia-smi不可用，无法检测GPU"
else
    echo ""
    echo "GPU信息:"
    nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader
    echo ""
fi

# 启动vLLM服务器
echo "启动vLLM服务器..."
echo ""

python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_NAME" \
    --host "$HOST" \
    --port "$PORT" \
    --tensor-parallel-size "$GPU_COUNT" \
    --dtype auto \
    ${API_KEY:+--api-key "$API_KEY"} \
    --max-model-len 4096 \
    --trust-remote-code

# 注意：服务器会持续运行直到手动停止（Ctrl+C）

