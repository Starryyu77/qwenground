"""
VLM Client - Qwen2-VL模型客户端
支持本地部署和API调用
"""

import torch
from typing import List, Dict, Optional, Union, Tuple
import numpy as np
import logging
from PIL import Image
import base64
import io
import re

logger = logging.getLogger(__name__)


class QwenVLMClient:
    """Qwen2-VL视觉-语言模型客户端"""
    
    def __init__(self,
                 model_name: str = "Qwen/Qwen2-VL-7B-Instruct",
                 device: str = "cuda",
                 use_api: bool = False,
                 api_url: Optional[str] = None,
                 api_key: Optional[str] = None):
        """
        Args:
            model_name: 模型名称
            device: 设备 (cuda/cpu)
            use_api: 是否使用API模式（vLLM服务器）
            api_url: API服务器地址
            api_key: API密钥
        """
        self.model_name = model_name
        self.device = device
        self.use_api = use_api
        self.api_url = api_url or "http://localhost:8000/v1"
        self.api_key = api_key
        
        self.model = None
        self.processor = None
        
        if not use_api:
            self._load_local_model()
    
    def _load_local_model(self):
        """加载本地模型"""
        try:
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
            
            logger.info(f"加载模型: {self.model_name}")
            
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto"
            )
            
            self.processor = AutoProcessor.from_pretrained(self.model_name)
            
            if self.device == "cuda" and torch.cuda.is_available():
                self.model = self.model.to(self.device)
            
            self.model.eval()
            logger.info("模型加载完成")
            
        except ImportError as e:
            logger.error("无法导入transformers或qwen-vl模块")
            logger.error("请运行: pip install transformers qwen-vl-utils")
            raise
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def generate(self,
                messages: List[Dict],
                max_tokens: int = 512,
                temperature: float = 0.1) -> str:
        """
        生成响应
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": [{"type": "image", "image": img}, {"type": "text", "text": "..."}]}]
            max_tokens: 最大生成token数
            temperature: 温度参数
            
        Returns:
            生成的文本
        """
        if self.use_api:
            return self._generate_via_api(messages, max_tokens, temperature)
        else:
            return self._generate_local(messages, max_tokens, temperature)
    
    def _generate_local(self,
                       messages: List[Dict],
                       max_tokens: int,
                       temperature: float) -> str:
        """本地模型生成"""
        try:
            from qwen_vl_utils import process_vision_info
            
            # 准备输入
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            
            # 处理图像
            image_inputs, video_inputs = process_vision_info(messages)
            
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            )
            
            inputs = inputs.to(self.device)
            
            # 生成
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0
                )
            
            # 解码
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            
            output_text = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )[0]
            
            return output_text
            
        except Exception as e:
            logger.error(f"生成失败: {e}")
            raise
    
    def _generate_via_api(self,
                         messages: List[Dict],
                         max_tokens: int,
                         temperature: float) -> str:
        """通过vLLM API生成"""
        try:
            import requests
            
            # 转换消息格式
            api_messages = self._convert_messages_for_api(messages)
            
            headers = {
                "Content-Type": "application/json",
            }
            
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "model": self.model_name,
                "messages": api_messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            raise
    
    def _convert_messages_for_api(self, messages: List[Dict]) -> List[Dict]:
        """转换消息格式为API格式"""
        api_messages = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if isinstance(content, str):
                api_messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                # 处理多模态内容
                converted_content = []
                
                for item in content:
                    if item["type"] == "text":
                        converted_content.append({
                            "type": "text",
                            "text": item["text"]
                        })
                    elif item["type"] == "image":
                        # 转换图像为base64
                        image = item["image"]
                        if isinstance(image, str):
                            # 已经是路径或URL
                            converted_content.append({
                                "type": "image_url",
                                "image_url": {"url": image}
                            })
                        else:
                            # PIL Image或numpy array
                            image_url = self._image_to_base64(image)
                            converted_content.append({
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            })
                
                api_messages.append({"role": role, "content": converted_content})
        
        return api_messages
    
    def _image_to_base64(self, image: Union[Image.Image, np.ndarray]) -> str:
        """转换图像为base64编码"""
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        base64_str = base64.b64encode(image_bytes).decode('utf-8')
        
        return f"data:image/png;base64,{base64_str}"
    
    def parse_grounding_response(self, response: str) -> Dict:
        """
        解析VLM的grounding响应
        
        Args:
            response: VLM生成的文本
            
        Returns:
            解析结果字典
        """
        # 尝试提取结构化信息
        result = {
            "target_object": None,
            "anchor_object": None,
            "spatial_relation": None,
            "bounding_box": None,
            "confidence": 0.5,
            "raw_response": response
        }
        
        # 提取目标物体
        target_match = re.search(r'target[:\s]+([a-zA-Z\s]+)', response, re.IGNORECASE)
        if target_match:
            result["target_object"] = target_match.group(1).strip()
        
        # 提取锚点物体
        anchor_match = re.search(r'anchor[:\s]+([a-zA-Z\s]+)', response, re.IGNORECASE)
        if anchor_match:
            result["anchor_object"] = anchor_match.group(1).strip()
        
        # 提取空间关系
        relations = ['on', 'above', 'below', 'left', 'right', 'near', 'inside', 'behind', 'front']
        for rel in relations:
            if rel in response.lower():
                result["spatial_relation"] = rel
                break
        
        # 提取边界框坐标（如果有）
        bbox_match = re.search(r'\[(\d+\.?\d*),\s*(\d+\.?\d*),\s*(\d+\.?\d*),\s*(\d+\.?\d*)\]', response)
        if bbox_match:
            result["bounding_box"] = [float(x) for x in bbox_match.groups()]
        
        return result
    
    def extract_query_components(self, query: str) -> Dict:
        """
        从自然语言查询中提取组件（目标、锚点、关系）
        
        Args:
            query: 自然语言查询，如 "the red apple on the wooden table"
            
        Returns:
            提取的组件
        """
        messages = [{
            "role": "user",
            "content": f"""分析以下查询，提取目标物体、锚点物体和空间关系。
            
查询: "{query}"

请以JSON格式返回：
{{
    "target": "目标物体名称",
    "anchor": "锚点物体名称（如果有）",
    "relation": "空间关系（如果有，例如on/above/near等）",
    "target_attributes": ["颜色", "材质等属性"]
}}

只返回JSON，不要其他文字。"""
        }]
        
        try:
            response = self.generate(messages, max_tokens=200, temperature=0.1)
            
            # 尝试解析JSON
            import json
            # 提取JSON部分
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result
            else:
                # 回退到简单解析
                return self._simple_query_parsing(query)
                
        except Exception as e:
            logger.warning(f"查询解析失败，使用简单方法: {e}")
            return self._simple_query_parsing(query)
    
    def _simple_query_parsing(self, query: str) -> Dict:
        """简单的查询解析（基于规则）"""
        result = {
            "target": None,
            "anchor": None,
            "relation": None,
            "target_attributes": []
        }
        
        # 提取空间关系
        relations = {
            'on': ['on', 'on top of'],
            'above': ['above', 'over'],
            'below': ['below', 'under', 'beneath'],
            'near': ['near', 'next to', 'beside'],
            'left': ['left of', 'to the left'],
            'right': ['right of', 'to the right'],
            'inside': ['inside', 'in', 'within']
        }
        
        query_lower = query.lower()
        for rel_key, rel_phrases in relations.items():
            for phrase in rel_phrases:
                if phrase in query_lower:
                    result["relation"] = rel_key
                    # 分割查询
                    parts = query_lower.split(phrase)
                    if len(parts) == 2:
                        result["target"] = parts[0].strip()
                        result["anchor"] = parts[1].strip()
                    break
            if result["relation"]:
                break
        
        # 如果没有找到关系，假设整个查询是目标
        if not result["target"]:
            result["target"] = query.strip()
        
        # 提取颜色属性
        colors = ['red', 'blue', 'green', 'yellow', 'black', 'white', 'brown', 'gray', 'orange']
        for color in colors:
            if color in query_lower:
                result["target_attributes"].append(color)
        
        return result

