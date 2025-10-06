"""
Perspective Adaptation Module
从视频/图像中提取关键帧并选择最佳视角
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerspectiveAdapter:
    """视角适应模块：提取关键帧和多视角处理"""
    
    def __init__(self, 
                 keyframe_count: int = 15,
                 min_scene_change: float = 0.3,
                 target_resolution: Tuple[int, int] = (1280, 720)):
        """
        Args:
            keyframe_count: 要提取的关键帧数量
            min_scene_change: 场景变化阈值（0-1）
            target_resolution: 目标分辨率 (width, height)
        """
        self.keyframe_count = keyframe_count
        self.min_scene_change = min_scene_change
        self.target_resolution = target_resolution
        
    def extract_keyframes_from_video(self, 
                                     video_path: str,
                                     method: str = "uniform") -> List[Dict]:
        """
        从视频中提取关键帧
        
        Args:
            video_path: 视频文件路径
            method: 提取方法 ["uniform", "scene_change", "hybrid"]
            
        Returns:
            关键帧列表，每个元素包含 {"frame": np.array, "timestamp": float, "frame_id": int}
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"视频信息: {total_frames}帧, {fps:.2f}fps, {duration:.2f}秒")
        
        if method == "uniform":
            keyframes = self._extract_uniform(cap, total_frames, fps)
        elif method == "scene_change":
            keyframes = self._extract_scene_change(cap, total_frames, fps)
        else:  # hybrid
            keyframes = self._extract_hybrid(cap, total_frames, fps)
        
        cap.release()
        logger.info(f"成功提取 {len(keyframes)} 个关键帧")
        return keyframes
    
    def _extract_uniform(self, cap, total_frames: int, fps: float) -> List[Dict]:
        """均匀采样关键帧"""
        keyframes = []
        interval = max(1, total_frames // self.keyframe_count)
        
        for i in tqdm(range(0, total_frames, interval), desc="提取关键帧"):
            if len(keyframes) >= self.keyframe_count:
                break
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if ret:
                frame_resized = self._resize_frame(frame)
                keyframes.append({
                    "frame": frame_resized,
                    "frame_id": i,
                    "timestamp": i / fps if fps > 0 else i,
                    "original_size": (frame.shape[1], frame.shape[0])
                })
        
        return keyframes
    
    def _extract_scene_change(self, cap, total_frames: int, fps: float) -> List[Dict]:
        """基于场景变化提取关键帧"""
        keyframes = []
        prev_frame_gray = None
        frame_id = 0
        
        # 计算所有帧的直方图差异
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        scene_changes = []
        
        with tqdm(total=total_frames, desc="分析场景变化") as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, (320, 180))  # 降低分辨率加速
                
                if prev_frame_gray is not None:
                    # 计算直方图差异
                    hist_diff = self._compute_histogram_difference(prev_frame_gray, gray)
                    scene_changes.append((frame_id, hist_diff, frame))
                
                prev_frame_gray = gray
                frame_id += 1
                pbar.update(1)
        
        # 选择场景变化最大的帧
        scene_changes.sort(key=lambda x: x[1], reverse=True)
        
        # 确保帧之间有最小间隔
        min_interval = max(1, total_frames // (self.keyframe_count * 2))
        selected_frames = []
        
        for fid, score, frame in scene_changes:
            if len(selected_frames) >= self.keyframe_count:
                break
            
            # 检查是否与已选帧距离足够
            if all(abs(fid - sf[0]) >= min_interval for sf in selected_frames):
                selected_frames.append((fid, score, frame))
        
        # 按时间顺序排序
        selected_frames.sort(key=lambda x: x[0])
        
        keyframes = []
        for fid, score, frame in selected_frames:
            frame_resized = self._resize_frame(frame)
            keyframes.append({
                "frame": frame_resized,
                "frame_id": fid,
                "timestamp": fid / fps if fps > 0 else fid,
                "scene_change_score": score,
                "original_size": (frame.shape[1], frame.shape[0])
            })
        
        return keyframes
    
    def _extract_hybrid(self, cap, total_frames: int, fps: float) -> List[Dict]:
        """混合方法：场景变化 + 均匀采样"""
        # 首先用场景变化提取 70%
        scene_count = int(self.keyframe_count * 0.7)
        original_count = self.keyframe_count
        self.keyframe_count = scene_count
        
        scene_keyframes = self._extract_scene_change(cap, total_frames, fps)
        
        # 然后在空白区间均匀采样 30%
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        selected_ids = set(kf["frame_id"] for kf in scene_keyframes)
        
        uniform_count = original_count - len(scene_keyframes)
        gaps = self._find_frame_gaps(selected_ids, total_frames)
        
        uniform_keyframes = []
        for gap_start, gap_end in gaps[:uniform_count]:
            mid_frame = (gap_start + gap_end) // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            ret, frame = cap.read()
            
            if ret:
                frame_resized = self._resize_frame(frame)
                uniform_keyframes.append({
                    "frame": frame_resized,
                    "frame_id": mid_frame,
                    "timestamp": mid_frame / fps if fps > 0 else mid_frame,
                    "original_size": (frame.shape[1], frame.shape[0])
                })
        
        self.keyframe_count = original_count
        all_keyframes = scene_keyframes + uniform_keyframes
        all_keyframes.sort(key=lambda x: x["frame_id"])
        
        return all_keyframes
    
    def load_images_from_folder(self, image_folder: str) -> List[Dict]:
        """
        从文件夹加载图像序列
        
        Args:
            image_folder: 图像文件夹路径
            
        Returns:
            图像列表
        """
        image_folder = Path(image_folder)
        if not image_folder.exists():
            raise FileNotFoundError(f"图像文件夹不存在: {image_folder}")
        
        # 支持的图像格式
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        image_paths = sorted([
            p for p in image_folder.iterdir() 
            if p.suffix.lower() in image_extensions
        ])
        
        if not image_paths:
            raise ValueError(f"文件夹中没有找到图像: {image_folder}")
        
        logger.info(f"找到 {len(image_paths)} 张图像")
        
        # 如果图像数量超过需求，进行采样
        if len(image_paths) > self.keyframe_count:
            indices = np.linspace(0, len(image_paths) - 1, self.keyframe_count, dtype=int)
            image_paths = [image_paths[i] for i in indices]
        
        keyframes = []
        for idx, img_path in enumerate(tqdm(image_paths, desc="加载图像")):
            frame = cv2.imread(str(img_path))
            if frame is None:
                logger.warning(f"无法读取图像: {img_path}")
                continue
            
            frame_resized = self._resize_frame(frame)
            keyframes.append({
                "frame": frame_resized,
                "frame_id": idx,
                "timestamp": idx,
                "original_size": (frame.shape[1], frame.shape[0]),
                "source_path": str(img_path)
            })
        
        return keyframes
    
    def select_relevant_views(self, 
                             keyframes: List[Dict],
                             query: str,
                             anchor_keywords: Optional[List[str]] = None) -> List[Dict]:
        """
        根据查询选择最相关的视角（简化版，基于规则）
        
        Args:
            keyframes: 关键帧列表
            query: 自然语言查询
            anchor_keywords: 锚点关键词（如 ["table", "desk"]）
            
        Returns:
            排序后的关键帧（最相关的在前）
        """
        # 简化实现：返回所有帧（实际应用中可以使用CLIP等模型进行相似度排序）
        # 这里假设所有视角都相关
        
        logger.info(f"选择与查询相关的视角: '{query}'")
        
        # 如果有场景变化分数，优先选择变化大的
        scored_frames = []
        for kf in keyframes:
            score = kf.get("scene_change_score", 0.5)
            scored_frames.append((score, kf))
        
        scored_frames.sort(key=lambda x: x[0], reverse=True)
        
        return [kf for _, kf in scored_frames]
    
    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """调整帧大小"""
        h, w = frame.shape[:2]
        target_w, target_h = self.target_resolution
        
        # 保持宽高比
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        return resized
    
    def _compute_histogram_difference(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """计算两帧的直方图差异"""
        hist1 = cv2.calcHist([frame1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([frame2], [0], None, [256], [0, 256])
        
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        
        # 使用Bhattacharyya距离
        diff = cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
        return diff
    
    def _find_frame_gaps(self, selected_ids: set, total_frames: int) -> List[Tuple[int, int]]:
        """找到未选择帧的间隙"""
        sorted_ids = sorted(list(selected_ids))
        gaps = []
        
        for i in range(len(sorted_ids) - 1):
            gap_start = sorted_ids[i]
            gap_end = sorted_ids[i + 1]
            if gap_end - gap_start > 1:
                gaps.append((gap_start, gap_end))
        
        # 按间隙大小排序
        gaps.sort(key=lambda x: x[1] - x[0], reverse=True)
        return gaps

