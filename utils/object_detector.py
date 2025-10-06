"""
Object Detector - 使用YOLOv8进行2D物体检测
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ObjectDetector:
    """2D物体检测器（基于YOLOv8）"""
    
    def __init__(self,
                 model_name: str = "yolov8x.pt",
                 conf_threshold: float = 0.25,
                 iou_threshold: float = 0.5,
                 device: str = "cuda"):
        """
        Args:
            model_name: YOLO模型名称
            conf_threshold: 置信度阈值
            iou_threshold: NMS的IoU阈值
            device: 设备
        """
        self.model_name = model_name
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.model = None
    
    def initialize(self):
        """初始化YOLO模型"""
        if self.model is not None:
            return
        
        try:
            from ultralytics import YOLO
            
            logger.info(f"加载YOLO模型: {self.model_name}")
            self.model = YOLO(self.model_name)
            
            # 移至指定设备
            if self.device == "cuda":
                import torch
                if torch.cuda.is_available():
                    self.model.to(self.device)
                else:
                    logger.warning("CUDA不可用，使用CPU")
                    self.device = "cpu"
            
            logger.info("YOLO模型加载完成")
            
        except ImportError:
            logger.error("无法导入ultralytics")
            logger.error("请运行: pip install ultralytics")
            raise
        except Exception as e:
            logger.error(f"YOLO模型加载失败: {e}")
            raise
    
    def detect(self, image: np.ndarray) -> List[Dict]:
        """
        检测图像中的物体
        
        Args:
            image: BGR图像
            
        Returns:
            检测结果列表，每个元素包含:
            {
                "class_name": str,
                "class_id": int,
                "confidence": float,
                "bbox": [x1, y1, x2, y2],  # 像素坐标
                "bbox_norm": [x1, y1, x2, y2]  # 归一化坐标 (0-1)
            }
        """
        if self.model is None:
            self.initialize()
        
        # 运行检测
        results = self.model.predict(
            image,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False
        )
        
        detections = []
        h, w = image.shape[:2]
        
        for result in results:
            boxes = result.boxes
            
            for i in range(len(boxes)):
                # 获取边界框
                xyxy = boxes.xyxy[i].cpu().numpy()
                x1, y1, x2, y2 = xyxy
                
                # 归一化坐标
                x1_norm, y1_norm = x1 / w, y1 / h
                x2_norm, y2_norm = x2 / w, y2 / h
                
                # 获取类别和置信度
                class_id = int(boxes.cls[i].cpu().numpy())
                confidence = float(boxes.conf[i].cpu().numpy())
                class_name = result.names[class_id]
                
                detections.append({
                    "class_name": class_name,
                    "class_id": class_id,
                    "confidence": confidence,
                    "bbox": [float(x1), float(y1), float(x2), float(y2)],
                    "bbox_norm": [float(x1_norm), float(y1_norm), 
                                 float(x2_norm), float(y2_norm)]
                })
        
        logger.debug(f"检测到 {len(detections)} 个物体")
        return detections
    
    def detect_batch(self, images: List[np.ndarray]) -> List[List[Dict]]:
        """
        批量检测
        
        Args:
            images: 图像列表
            
        Returns:
            每个图像的检测结果列表
        """
        if self.model is None:
            self.initialize()
        
        all_detections = []
        
        for image in images:
            detections = self.detect(image)
            all_detections.append(detections)
        
        return all_detections
    
    def draw_detections(self,
                       image: np.ndarray,
                       detections: List[Dict],
                       show_labels: bool = True,
                       show_conf: bool = True) -> np.ndarray:
        """
        在图像上绘制检测结果
        
        Args:
            image: 原始图像
            detections: 检测结果
            show_labels: 是否显示标签
            show_conf: 是否显示置信度
            
        Returns:
            绘制后的图像
        """
        img_draw = image.copy()
        
        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
            class_name = det["class_name"]
            confidence = det["confidence"]
            
            # 绘制边界框
            color = self._get_color_for_class(det["class_id"])
            cv2.rectangle(img_draw, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签
            if show_labels:
                label = class_name
                if show_conf:
                    label += f" {confidence:.2f}"
                
                # 计算文本背景
                (text_w, text_h), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )
                
                # 绘制文本背景
                cv2.rectangle(
                    img_draw,
                    (x1, y1 - text_h - 5),
                    (x1 + text_w, y1),
                    color,
                    -1
                )
                
                # 绘制文本
                cv2.putText(
                    img_draw,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
        
        return img_draw
    
    def _get_color_for_class(self, class_id: int) -> Tuple[int, int, int]:
        """为类别生成一致的颜色"""
        np.random.seed(class_id)
        color = tuple(np.random.randint(0, 255, 3).tolist())
        return color
    
    def filter_detections_by_class(self,
                                  detections: List[Dict],
                                  class_names: List[str]) -> List[Dict]:
        """
        按类别过滤检测结果
        
        Args:
            detections: 检测结果
            class_names: 要保留的类别名称列表
            
        Returns:
            过滤后的检测结果
        """
        class_names_lower = [name.lower() for name in class_names]
        
        filtered = [
            det for det in detections
            if det["class_name"].lower() in class_names_lower
        ]
        
        return filtered
    
    def get_detection_center(self, detection: Dict) -> np.ndarray:
        """获取检测框的中心点（归一化坐标）"""
        x1, y1, x2, y2 = detection["bbox_norm"]
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        return np.array([cx, cy])
    
    def compute_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """计算两个边界框的IoU"""
        x1_min, y1_min, x1_max, y1_max = bbox1
        x2_min, y2_min, x2_max, y2_max = bbox2
        
        # 计算交集
        inter_xmin = max(x1_min, x2_min)
        inter_ymin = max(y1_min, y2_min)
        inter_xmax = min(x1_max, x2_max)
        inter_ymax = min(y1_max, y2_max)
        
        if inter_xmax < inter_xmin or inter_ymax < inter_ymin:
            return 0.0
        
        inter_area = (inter_xmax - inter_xmin) * (inter_ymax - inter_ymin)
        
        # 计算并集
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = area1 + area2 - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0

