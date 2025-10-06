"""
Object Lookup Table (OLT)
存储和管理检测到的物体及其2D/3D边界框
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class Object3D:
    """3D物体数据结构"""
    object_id: int
    class_name: str
    confidence: float
    bbox_2d: List[float]  # [x1, y1, x2, y2] 归一化坐标
    bbox_3d: Optional[List[float]] = None  # [x, y, z, w, h, d]
    center_3d: Optional[List[float]] = None  # [x, y, z]
    frame_ids: Optional[List[int]] = None  # 出现的帧ID
    embedding: Optional[np.ndarray] = None  # 特征向量（用于相似度匹配）
    attributes: Optional[Dict] = None  # 额外属性
    
    def to_dict(self) -> Dict:
        """转换为字典（用于序列化）"""
        d = asdict(self)
        if self.embedding is not None:
            d['embedding'] = self.embedding.tolist()
        return d
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'Object3D':
        """从字典创建对象"""
        if 'embedding' in d and d['embedding'] is not None:
            d['embedding'] = np.array(d['embedding'])
        return cls(**d)


class ObjectLookupTable:
    """物体查找表：管理所有检测到的物体"""
    
    def __init__(self):
        self.objects: List[Object3D] = []
        self.next_id = 0
        self._spatial_index = None  # 用于快速空间查询的索引
    
    def add_object(self, obj: Object3D) -> int:
        """
        添加物体到表中
        
        Args:
            obj: Object3D实例
            
        Returns:
            分配的object_id
        """
        if obj.object_id is None or obj.object_id < 0:
            obj.object_id = self.next_id
            self.next_id += 1
        
        self.objects.append(obj)
        logger.debug(f"添加物体: ID={obj.object_id}, 类别={obj.class_name}")
        
        return obj.object_id
    
    def get_object(self, object_id: int) -> Optional[Object3D]:
        """根据ID获取物体"""
        for obj in self.objects:
            if obj.object_id == object_id:
                return obj
        return None
    
    def get_objects_by_class(self, class_name: str) -> List[Object3D]:
        """根据类别获取所有物体"""
        return [obj for obj in self.objects if obj.class_name.lower() == class_name.lower()]
    
    def get_objects_in_frame(self, frame_id: int) -> List[Object3D]:
        """获取特定帧中的所有物体"""
        return [obj for obj in self.objects 
                if obj.frame_ids and frame_id in obj.frame_ids]
    
    def find_nearest_object(self, 
                           center_3d: np.ndarray,
                           class_name: Optional[str] = None,
                           max_distance: float = 2.0) -> Optional[Object3D]:
        """
        找到最近的物体
        
        Args:
            center_3d: 查询点 [x, y, z]
            class_name: 可选的类别过滤
            max_distance: 最大距离阈值
            
        Returns:
            最近的物体，如果没有在阈值内则返回None
        """
        candidates = self.objects if class_name is None else self.get_objects_by_class(class_name)
        
        if not candidates:
            return None
        
        min_dist = float('inf')
        nearest_obj = None
        
        for obj in candidates:
            if obj.center_3d is None:
                continue
            
            dist = np.linalg.norm(np.array(obj.center_3d) - center_3d)
            if dist < min_dist and dist < max_distance:
                min_dist = dist
                nearest_obj = obj
        
        return nearest_obj
    
    def find_objects_in_region(self,
                               center: np.ndarray,
                               radius: float) -> List[Object3D]:
        """
        找到区域内的所有物体
        
        Args:
            center: 区域中心 [x, y, z]
            radius: 半径
            
        Returns:
            区域内的物体列表
        """
        objects_in_region = []
        
        for obj in self.objects:
            if obj.center_3d is None:
                continue
            
            dist = np.linalg.norm(np.array(obj.center_3d) - center)
            if dist <= radius:
                objects_in_region.append(obj)
        
        return objects_in_region
    
    def find_objects_by_spatial_relation(self,
                                        anchor_obj: Object3D,
                                        relation: str,
                                        class_name: Optional[str] = None) -> List[Object3D]:
        """
        根据空间关系查找物体
        
        Args:
            anchor_obj: 锚点物体
            relation: 空间关系 ["on", "above", "below", "left", "right", "near"]
            class_name: 可选的类别过滤
            
        Returns:
            满足关系的物体列表
        """
        if anchor_obj.center_3d is None:
            return []
        
        anchor_center = np.array(anchor_obj.center_3d)
        candidates = self.objects if class_name is None else self.get_objects_by_class(class_name)
        
        results = []
        
        for obj in candidates:
            if obj.object_id == anchor_obj.object_id or obj.center_3d is None:
                continue
            
            obj_center = np.array(obj.center_3d)
            
            if self._check_spatial_relation(obj_center, anchor_center, relation):
                results.append(obj)
        
        return results
    
    def _check_spatial_relation(self,
                               obj_pos: np.ndarray,
                               anchor_pos: np.ndarray,
                               relation: str) -> bool:
        """检查两个物体是否满足空间关系"""
        diff = obj_pos - anchor_pos
        
        # 定义阈值
        near_threshold = 1.5
        vertical_threshold = 0.2
        horizontal_threshold = 0.3
        
        if relation == "near":
            return np.linalg.norm(diff) < near_threshold
        elif relation == "above":
            return diff[2] > vertical_threshold  # z轴向上
        elif relation == "below":
            return diff[2] < -vertical_threshold
        elif relation == "left":
            return diff[0] < -horizontal_threshold  # x轴向左
        elif relation == "right":
            return diff[0] > horizontal_threshold
        elif relation == "on":
            # "on"表示物体在锚点上方且接近
            return (diff[2] > 0.05 and diff[2] < 0.5 and 
                   np.linalg.norm(diff[:2]) < 0.5)
        else:
            return False
    
    def merge_duplicate_objects(self, 
                               iou_threshold: float = 0.5,
                               distance_threshold: float = 0.3):
        """
        合并重复的物体（例如同一物体在多帧中被检测）
        
        Args:
            iou_threshold: 2D IoU阈值
            distance_threshold: 3D距离阈值
        """
        merged_objects = []
        used = set()
        
        for i, obj1 in enumerate(self.objects):
            if i in used:
                continue
            
            # 找到所有相似的物体
            similar_objs = [obj1]
            
            for j, obj2 in enumerate(self.objects[i+1:], start=i+1):
                if j in used:
                    continue
                
                if self._is_duplicate(obj1, obj2, iou_threshold, distance_threshold):
                    similar_objs.append(obj2)
                    used.add(j)
            
            # 合并相似物体
            merged_obj = self._merge_objects(similar_objs)
            merged_objects.append(merged_obj)
        
        logger.info(f"合并前: {len(self.objects)} 个物体, 合并后: {len(merged_objects)} 个物体")
        self.objects = merged_objects
    
    def _is_duplicate(self, 
                     obj1: Object3D, 
                     obj2: Object3D,
                     iou_threshold: float,
                     distance_threshold: float) -> bool:
        """判断两个物体是否重复"""
        # 类别必须相同
        if obj1.class_name != obj2.class_name:
            return False
        
        # 计算2D IoU
        iou = self._compute_iou_2d(obj1.bbox_2d, obj2.bbox_2d)
        
        # 如果有3D中心，也检查3D距离
        if obj1.center_3d and obj2.center_3d:
            dist = np.linalg.norm(np.array(obj1.center_3d) - np.array(obj2.center_3d))
            return iou > iou_threshold or dist < distance_threshold
        else:
            return iou > iou_threshold
    
    def _compute_iou_2d(self, bbox1: List[float], bbox2: List[float]) -> float:
        """计算2D边界框的IoU"""
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
    
    def _merge_objects(self, objects: List[Object3D]) -> Object3D:
        """合并多个相似物体"""
        if len(objects) == 1:
            return objects[0]
        
        # 使用置信度最高的物体作为基础
        base_obj = max(objects, key=lambda o: o.confidence)
        
        # 合并帧ID
        all_frame_ids = set()
        for obj in objects:
            if obj.frame_ids:
                all_frame_ids.update(obj.frame_ids)
        
        # 平均3D边界框
        if all(obj.bbox_3d for obj in objects):
            avg_bbox_3d = np.mean([obj.bbox_3d for obj in objects], axis=0).tolist()
        else:
            avg_bbox_3d = base_obj.bbox_3d
        
        # 平均3D中心
        if all(obj.center_3d for obj in objects):
            avg_center_3d = np.mean([obj.center_3d for obj in objects], axis=0).tolist()
        else:
            avg_center_3d = base_obj.center_3d
        
        # 平均置信度
        avg_confidence = np.mean([obj.confidence for obj in objects])
        
        return Object3D(
            object_id=base_obj.object_id,
            class_name=base_obj.class_name,
            confidence=float(avg_confidence),
            bbox_2d=base_obj.bbox_2d,
            bbox_3d=avg_bbox_3d,
            center_3d=avg_center_3d,
            frame_ids=sorted(list(all_frame_ids)),
            embedding=base_obj.embedding,
            attributes=base_obj.attributes
        )
    
    def to_dataframe(self) -> pd.DataFrame:
        """转换为Pandas DataFrame"""
        data = []
        for obj in self.objects:
            row = {
                'object_id': obj.object_id,
                'class_name': obj.class_name,
                'confidence': obj.confidence,
                'bbox_2d': str(obj.bbox_2d),
                'bbox_3d': str(obj.bbox_3d),
                'center_3d': str(obj.center_3d),
                'frame_ids': str(obj.frame_ids)
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    def save(self, output_path: str):
        """保存OLT到JSON文件"""
        data = {
            'objects': [obj.to_dict() for obj in self.objects],
            'next_id': self.next_id
        }
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"OLT已保存至: {output_path}")
    
    def load(self, input_path: str):
        """从JSON文件加载OLT"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.objects = [Object3D.from_dict(obj_dict) for obj_dict in data['objects']]
        self.next_id = data['next_id']
        
        logger.info(f"从 {input_path} 加载了 {len(self.objects)} 个物体")
    
    def __len__(self) -> int:
        return len(self.objects)
    
    def __repr__(self) -> str:
        return f"ObjectLookupTable({len(self.objects)} objects)"

