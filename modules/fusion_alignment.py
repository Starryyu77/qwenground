"""
Fusion Alignment Module
融合2D视图与3D空间描述，使用VLM进行grounding
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from PIL import Image
import logging

from modules.object_lookup_table import ObjectLookupTable, Object3D
from modules.reconstruction_3d import PointCloud3D
from utils.vlm_client import QwenVLMClient
from utils.object_detector import ObjectDetector

logger = logging.getLogger(__name__)


class FusionAlignment:
    """融合对齐模块：2D-3D融合和VLM grounding"""
    
    def __init__(self,
                 vlm_client: QwenVLMClient,
                 object_detector: ObjectDetector):
        """
        Args:
            vlm_client: VLM客户端
            object_detector: 物体检测器
        """
        self.vlm_client = vlm_client
        self.object_detector = object_detector
    
    def build_olt_from_keyframes(self,
                                 keyframes: List[Dict],
                                 pointcloud: PointCloud3D) -> ObjectLookupTable:
        """
        从关键帧构建Object Lookup Table
        
        Args:
            keyframes: 关键帧列表
            pointcloud: 3D点云
            
        Returns:
            填充好的OLT
        """
        logger.info("构建Object Lookup Table...")
        
        olt = ObjectLookupTable()
        
        # 检测所有帧中的物体
        for kf in keyframes:
            frame = kf["frame"]
            frame_id = kf["frame_id"]
            
            detections = self.object_detector.detect(frame)
            logger.info(f"  帧 {frame_id}: 检测到 {len(detections)} 个物体")
            
            # 为每个检测创建3D物体
            for det in detections:
                # 估计3D位置
                bbox_3d, center_3d = self._estimate_3d_bbox(
                    det, frame, pointcloud
                )
                
                # 创建物体对象
                obj = Object3D(
                    object_id=-1,  # 将由OLT分配
                    class_name=det["class_name"],
                    confidence=det["confidence"],
                    bbox_2d=det["bbox_norm"],
                    bbox_3d=bbox_3d,
                    center_3d=center_3d,
                    frame_ids=[frame_id],
                    attributes={"detection": det}
                )
                
                olt.add_object(obj)
        
        # 合并重复物体（同一物体在多帧中出现）
        olt.merge_duplicate_objects(iou_threshold=0.5, distance_threshold=0.5)
        
        logger.info(f"OLT构建完成: 共 {len(olt)} 个唯一物体")
        
        return olt
    
    def _estimate_3d_bbox(self,
                         detection: Dict,
                         image: np.ndarray,
                         pointcloud: PointCloud3D) -> Tuple[List[float], List[float]]:
        """
        从2D检测和点云估计3D边界框
        
        Args:
            detection: 2D检测结果
            image: 图像
            pointcloud: 3D点云
            
        Returns:
            (bbox_3d, center_3d)
            bbox_3d: [x, y, z, w, h, d]
            center_3d: [x, y, z]
        """
        # 获取2D边界框（归一化坐标）
        x1_norm, y1_norm, x2_norm, y2_norm = detection["bbox_norm"]
        
        h, w = image.shape[:2]
        x1, y1 = int(x1_norm * w), int(y1_norm * h)
        x2, y2 = int(x2_norm * w), int(y2_norm * h)
        
        # 将2D框投影到点云（简化版本）
        # 实际应用中需要准确的相机-点云对应关系
        
        if pointcloud.points.shape[0] == 0:
            # 如果没有点云，使用默认值
            logger.warning("点云为空，使用默认3D边界框")
            center_3d = [0.0, 0.0, 1.0]
            bbox_3d = [0.0, 0.0, 1.0, 0.3, 0.3, 0.3]
            return bbox_3d, center_3d
        
        # 估计深度（使用点云的平均深度）
        avg_depth = np.mean(pointcloud.points[:, 2])
        
        # 简化：假设物体在视野中心附近
        cx_norm = (x1_norm + x2_norm) / 2
        cy_norm = (y1_norm + y2_norm) / 2
        
        # 将归一化坐标映射到3D（粗略估计）
        # 假设场景范围在 -5 到 5 之间
        scene_range = 5.0
        x_3d = (cx_norm - 0.5) * 2 * scene_range
        y_3d = (cy_norm - 0.5) * 2 * scene_range
        z_3d = avg_depth
        
        # 估计尺寸（基于2D框大小）
        width_3d = (x2_norm - x1_norm) * scene_range * 0.5
        height_3d = (y2_norm - y1_norm) * scene_range * 0.5
        depth_3d = (width_3d + height_3d) / 2  # 假设深度为宽高平均
        
        center_3d = [float(x_3d), float(y_3d), float(z_3d)]
        bbox_3d = [
            float(x_3d), float(y_3d), float(z_3d),
            float(width_3d), float(height_3d), float(depth_3d)
        ]
        
        return bbox_3d, center_3d
    
    def ground_target_object(self,
                            query: str,
                            keyframes: List[Dict],
                            olt: ObjectLookupTable) -> Optional[Object3D]:
        """
        使用VLM定位目标物体
        
        Args:
            query: 自然语言查询
            keyframes: 关键帧列表
            olt: Object Lookup Table
            
        Returns:
            定位到的目标物体，如果失败返回None
        """
        logger.info(f"开始定位目标: '{query}'")
        
        # 步骤1: 解析查询
        query_components = self.vlm_client.extract_query_components(query)
        logger.info(f"查询解析: {query_components}")
        
        target_name = query_components.get("target", "").strip()
        anchor_name = query_components.get("anchor", "").strip()
        relation = query_components.get("relation")
        
        if not target_name:
            logger.error("无法从查询中提取目标物体")
            return None
        
        # 步骤2: 在OLT中查找候选物体
        target_candidates = self._find_candidate_objects(target_name, olt)
        
        if not target_candidates:
            logger.warning(f"在OLT中未找到匹配 '{target_name}' 的物体")
            return None
        
        logger.info(f"找到 {len(target_candidates)} 个目标候选物体")
        
        # 步骤3: 如果有锚点和空间关系，进行过滤
        if anchor_name and relation:
            target_candidates = self._filter_by_spatial_relation(
                target_candidates, anchor_name, relation, olt
            )
            logger.info(f"空间关系过滤后剩余 {len(target_candidates)} 个候选")
        
        if not target_candidates:
            logger.warning("空间关系过滤后无候选物体")
            return None
        
        # 步骤4: 使用VLM进行最终验证（选择最佳候选）
        if len(target_candidates) == 1:
            return target_candidates[0]
        
        best_candidate = self._verify_with_vlm(
            query, target_candidates, keyframes
        )
        
        if best_candidate:
            logger.info(f"成功定位目标: {best_candidate.class_name} (ID: {best_candidate.object_id})")
        else:
            logger.warning("VLM验证失败")
        
        return best_candidate
    
    def _find_candidate_objects(self,
                               target_name: str,
                               olt: ObjectLookupTable) -> List[Object3D]:
        """在OLT中查找候选物体"""
        # 精确匹配
        candidates = olt.get_objects_by_class(target_name)
        
        if candidates:
            return candidates
        
        # 模糊匹配（包含关系）
        target_lower = target_name.lower()
        fuzzy_candidates = []
        
        for obj in olt.objects:
            if target_lower in obj.class_name.lower() or obj.class_name.lower() in target_lower:
                fuzzy_candidates.append(obj)
        
        # 同义词匹配（简化版）
        if not fuzzy_candidates:
            synonyms = self._get_synonyms(target_name)
            for synonym in synonyms:
                fuzzy_candidates.extend(olt.get_objects_by_class(synonym))
        
        return fuzzy_candidates
    
    def _get_synonyms(self, class_name: str) -> List[str]:
        """获取类别名称的同义词"""
        # 简化的同义词词典
        synonym_dict = {
            "laptop": ["computer", "notebook"],
            "phone": ["mobile", "cellphone", "smartphone"],
            "bottle": ["container"],
            "cup": ["mug", "glass"],
            "person": ["people", "man", "woman"],
        }
        
        return synonym_dict.get(class_name.lower(), [])
    
    def _filter_by_spatial_relation(self,
                                    candidates: List[Object3D],
                                    anchor_name: str,
                                    relation: str,
                                    olt: ObjectLookupTable) -> List[Object3D]:
        """根据空间关系过滤候选物体"""
        # 查找锚点物体
        anchor_objects = self._find_candidate_objects(anchor_name, olt)
        
        if not anchor_objects:
            logger.warning(f"未找到锚点物体: {anchor_name}")
            return candidates
        
        # 使用置信度最高的锚点
        anchor = max(anchor_objects, key=lambda o: o.confidence)
        logger.info(f"使用锚点: {anchor.class_name} (ID: {anchor.object_id})")
        
        # 根据空间关系过滤
        filtered_candidates = []
        
        for candidate in candidates:
            if candidate.center_3d and anchor.center_3d:
                if olt._check_spatial_relation(
                    np.array(candidate.center_3d),
                    np.array(anchor.center_3d),
                    relation
                ):
                    filtered_candidates.append(candidate)
        
        return filtered_candidates
    
    def _verify_with_vlm(self,
                        query: str,
                        candidates: List[Object3D],
                        keyframes: List[Dict]) -> Optional[Object3D]:
        """
        使用VLM验证候选物体（选择最佳匹配）
        
        简化版本：根据置信度和出现次数选择
        完整版本应该使用VLM对每个候选进行视觉验证
        """
        # 选择置信度最高的候选
        best_candidate = max(candidates, key=lambda c: c.confidence)
        
        # TODO: 使用VLM进行视觉验证
        # 这里应该生成带有标注的图像，然后让VLM判断哪个是正确的
        
        return best_candidate
    
    def create_annotated_image(self,
                              image: np.ndarray,
                              olt: ObjectLookupTable,
                              frame_id: int,
                              highlight_id: Optional[int] = None) -> np.ndarray:
        """
        创建带标注的图像（用于VLM输入）
        
        Args:
            image: 原始图像
            olt: Object Lookup Table
            frame_id: 帧ID
            highlight_id: 要高亮的物体ID
            
        Returns:
            标注后的图像
        """
        img_annotated = image.copy()
        
        # 获取该帧中的所有物体
        objects_in_frame = olt.get_objects_in_frame(frame_id)
        
        h, w = image.shape[:2]
        
        for obj in objects_in_frame:
            # 获取2D边界框
            x1, y1, x2, y2 = obj.bbox_2d
            x1, y1 = int(x1 * w), int(y1 * h)
            x2, y2 = int(x2 * w), int(y2 * h)
            
            # 选择颜色
            if highlight_id is not None and obj.object_id == highlight_id:
                color = (0, 255, 0)  # 绿色高亮
                thickness = 3
            else:
                color = (255, 0, 0)  # 蓝色普通
                thickness = 2
            
            # 绘制边界框
            cv2.rectangle(img_annotated, (x1, y1), (x2, y2), color, thickness)
            
            # 绘制标签
            label = f"[{obj.object_id}] {obj.class_name}"
            cv2.putText(
                img_annotated,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )
        
        return img_annotated

