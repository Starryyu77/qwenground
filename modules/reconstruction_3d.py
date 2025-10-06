"""
3D Reconstruction Module
从2D图像生成3D点云和场景重建
"""

import cv2
import numpy as np
import open3d as o3d
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PointCloud3D:
    """3D点云数据结构"""
    points: np.ndarray  # (N, 3)
    colors: Optional[np.ndarray] = None  # (N, 3)
    normals: Optional[np.ndarray] = None  # (N, 3)
    metadata: Optional[Dict] = None


class Reconstruction3D:
    """3D重建模块：从2D图像生成3D点云"""
    
    def __init__(self,
                 depth_model_type: str = "MiDaS_small",
                 voxel_size: float = 0.05,
                 use_gpu: bool = True):
        """
        Args:
            depth_model_type: 深度估计模型类型
            voxel_size: 体素下采样大小
            use_gpu: 是否使用GPU
        """
        self.depth_model_type = depth_model_type
        self.voxel_size = voxel_size
        self.use_gpu = use_gpu
        self.depth_model = None
        self.depth_transform = None
        
    def initialize_depth_model(self):
        """初始化MiDaS深度估计模型"""
        if self.depth_model is not None:
            return
        
        try:
            import torch
            logger.info(f"加载深度估计模型: {self.depth_model_type}")
            
            # 加载MiDaS模型
            if self.depth_model_type == "MiDaS_small":
                self.depth_model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
            elif self.depth_model_type == "DPT_Large":
                self.depth_model = torch.hub.load("intel-isl/MiDaS", "DPT_Large")
            else:
                self.depth_model = torch.hub.load("intel-isl/MiDaS", "DPT_Hybrid")
            
            # 加载transforms
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
            
            if self.depth_model_type == "MiDaS_small":
                self.depth_transform = midas_transforms.small_transform
            else:
                self.depth_transform = midas_transforms.dpt_transform
            
            if self.use_gpu and torch.cuda.is_available():
                self.depth_model = self.depth_model.to("cuda")
                logger.info("深度模型已移至GPU")
            
            self.depth_model.eval()
            logger.info("深度估计模型加载完成")
            
        except Exception as e:
            logger.error(f"深度模型加载失败: {e}")
            raise
    
    def estimate_depth(self, image: np.ndarray) -> np.ndarray:
        """
        估计单张图像的深度图
        
        Args:
            image: BGR图像 (H, W, 3)
            
        Returns:
            深度图 (H, W)，值越大表示越远
        """
        import torch
        
        if self.depth_model is None:
            self.initialize_depth_model()
        
        # 转换为RGB
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 预处理
        input_batch = self.depth_transform(img_rgb)
        
        if self.use_gpu and torch.cuda.is_available():
            input_batch = input_batch.to("cuda")
        
        # 推理
        with torch.no_grad():
            prediction = self.depth_model(input_batch)
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img_rgb.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()
        
        depth_map = prediction.cpu().numpy()
        
        # 归一化到 0-1
        depth_map = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min() + 1e-8)
        
        return depth_map
    
    def depth_to_pointcloud(self,
                           image: np.ndarray,
                           depth_map: np.ndarray,
                           camera_intrinsics: Optional[np.ndarray] = None) -> PointCloud3D:
        """
        从深度图生成点云
        
        Args:
            image: RGB图像
            depth_map: 深度图
            camera_intrinsics: 相机内参矩阵 (3x3)
            
        Returns:
            PointCloud3D对象
        """
        h, w = depth_map.shape
        
        # 如果没有提供相机内参，使用估计值
        if camera_intrinsics is None:
            focal_length = w * 1.2  # 经验值
            cx, cy = w / 2, h / 2
            camera_intrinsics = np.array([
                [focal_length, 0, cx],
                [0, focal_length, cy],
                [0, 0, 1]
            ])
        
        # 生成像素网格
        u, v = np.meshgrid(np.arange(w), np.arange(h))
        u = u.flatten()
        v = v.flatten()
        depth = depth_map.flatten()
        
        # 深度缩放（将归一化深度转换为真实尺度，这里使用经验值）
        depth = depth * 5.0  # 假设场景深度在5米内
        
        # 反投影到3D
        fx, fy = camera_intrinsics[0, 0], camera_intrinsics[1, 1]
        cx, cy = camera_intrinsics[0, 2], camera_intrinsics[1, 2]
        
        x = (u - cx) * depth / fx
        y = (v - cy) * depth / fy
        z = depth
        
        points = np.stack([x, y, z], axis=1)
        
        # 提取颜色
        if len(image.shape) == 3:
            colors = image.reshape(-1, 3) / 255.0
            # BGR转RGB
            colors = colors[:, ::-1]
        else:
            colors = None
        
        # 过滤无效点
        valid_mask = (z > 0) & (z < 10.0)  # 过滤太近或太远的点
        points = points[valid_mask]
        if colors is not None:
            colors = colors[valid_mask]
        
        return PointCloud3D(
            points=points,
            colors=colors,
            metadata={"camera_intrinsics": camera_intrinsics}
        )
    
    def reconstruct_from_keyframes(self,
                                   keyframes: List[Dict],
                                   method: str = "depth") -> PointCloud3D:
        """
        从关键帧重建3D场景
        
        Args:
            keyframes: 关键帧列表
            method: 重建方法 ["depth", "sfm"]
            
        Returns:
            合并的点云
        """
        logger.info(f"开始3D重建，方法: {method}")
        
        if method == "depth":
            return self._reconstruct_from_depth(keyframes)
        elif method == "sfm":
            return self._reconstruct_from_sfm(keyframes)
        else:
            raise ValueError(f"不支持的重建方法: {method}")
    
    def _reconstruct_from_depth(self, keyframes: List[Dict]) -> PointCloud3D:
        """使用深度估计进行重建"""
        all_points = []
        all_colors = []
        
        logger.info(f"处理 {len(keyframes)} 个关键帧...")
        
        for idx, kf in enumerate(keyframes):
            frame = kf["frame"]
            
            # 估计深度
            depth_map = self.estimate_depth(frame)
            
            # 生成点云
            pcd = self.depth_to_pointcloud(frame, depth_map)
            
            # 为不同视角添加位置偏移（简化的多视角融合）
            offset = self._compute_frame_offset(idx, len(keyframes))
            pcd.points += offset
            
            all_points.append(pcd.points)
            if pcd.colors is not None:
                all_colors.append(pcd.colors)
            
            logger.info(f"  帧 {idx+1}/{len(keyframes)}: 生成 {len(pcd.points)} 个点")
        
        # 合并所有点云
        merged_points = np.vstack(all_points)
        merged_colors = np.vstack(all_colors) if all_colors else None
        
        logger.info(f"合并点云: 总共 {len(merged_points)} 个点")
        
        # 下采样
        merged_pcd = PointCloud3D(points=merged_points, colors=merged_colors)
        merged_pcd = self._downsample_pointcloud(merged_pcd)
        
        logger.info(f"下采样后: {len(merged_pcd.points)} 个点")
        
        return merged_pcd
    
    def _reconstruct_from_sfm(self, keyframes: List[Dict]) -> PointCloud3D:
        """
        使用SfM（Structure from Motion）进行重建
        这是简化版本，实际应用建议使用COLMAP
        """
        logger.warning("SfM方法需要COLMAP支持，当前使用简化版本")
        
        # 如果没有COLMAP，回退到深度估计方法
        try:
            # 尝试使用Open3D的RGBD Odometry
            return self._reconstruct_with_open3d_odometry(keyframes)
        except Exception as e:
            logger.warning(f"Open3D odometry失败，回退到深度方法: {e}")
            return self._reconstruct_from_depth(keyframes)
    
    def _reconstruct_with_open3d_odometry(self, keyframes: List[Dict]) -> PointCloud3D:
        """使用Open3D的RGBD Odometry"""
        # 这是一个简化的实现
        # 实际使用时需要更复杂的特征匹配和位姿估计
        
        all_pcds = []
        prev_depth = None
        cumulative_transform = np.eye(4)
        
        for idx, kf in enumerate(keyframes):
            frame = kf["frame"]
            
            # 估计深度
            depth_map = self.estimate_depth(frame)
            
            # 转换为Open3D格式
            color = o3d.geometry.Image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.uint8))
            depth = o3d.geometry.Image((depth_map * 1000).astype(np.uint16))
            
            rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
                color, depth, depth_scale=1000.0, convert_rgb_to_intensity=False
            )
            
            # 创建点云
            intrinsic = o3d.camera.PinholeCameraIntrinsic(
                width=frame.shape[1],
                height=frame.shape[0],
                fx=frame.shape[1] * 1.2,
                fy=frame.shape[1] * 1.2,
                cx=frame.shape[1] / 2,
                cy=frame.shape[0] / 2
            )
            
            pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, intrinsic)
            
            # 应用累积变换
            pcd.transform(cumulative_transform)
            
            # 估计相邻帧的变换（简化版）
            if idx > 0 and prev_depth is not None:
                # 这里应该使用ICP或特征匹配，简化为固定平移
                translation = np.array([0.5 * idx, 0, 0])
                transform = np.eye(4)
                transform[:3, 3] = translation
                cumulative_transform = transform @ cumulative_transform
            
            all_pcds.append(pcd)
            prev_depth = depth_map
        
        # 合并点云
        merged = o3d.geometry.PointCloud()
        for pcd in all_pcds:
            merged += pcd
        
        # 下采样
        merged = merged.voxel_down_sample(voxel_size=self.voxel_size)
        
        # 转换为自定义格式
        points = np.asarray(merged.points)
        colors = np.asarray(merged.colors) if merged.has_colors() else None
        
        return PointCloud3D(points=points, colors=colors)
    
    def _compute_frame_offset(self, frame_idx: int, total_frames: int) -> np.ndarray:
        """
        为不同帧计算空间偏移（模拟不同视角）
        实际应用中应该使用相机位姿估计
        """
        # 简化：在圆形轨迹上分布
        angle = 2 * np.pi * frame_idx / total_frames
        radius = 2.0
        
        x_offset = radius * np.cos(angle) * 0.1
        y_offset = radius * np.sin(angle) * 0.1
        z_offset = 0
        
        return np.array([x_offset, y_offset, z_offset])
    
    def _downsample_pointcloud(self, pcd: PointCloud3D) -> PointCloud3D:
        """下采样点云"""
        # 转换为Open3D格式
        o3d_pcd = o3d.geometry.PointCloud()
        o3d_pcd.points = o3d.utility.Vector3dVector(pcd.points)
        
        if pcd.colors is not None:
            o3d_pcd.colors = o3d.utility.Vector3dVector(pcd.colors)
        
        # 体素下采样
        o3d_pcd = o3d_pcd.voxel_down_sample(voxel_size=self.voxel_size)
        
        # 统计去除离群点
        o3d_pcd, _ = o3d_pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
        
        # 转换回自定义格式
        points = np.asarray(o3d_pcd.points)
        colors = np.asarray(o3d_pcd.colors) if o3d_pcd.has_colors() else None
        
        return PointCloud3D(points=points, colors=colors, metadata=pcd.metadata)
    
    def save_pointcloud(self, pcd: PointCloud3D, output_path: str):
        """保存点云为PLY文件"""
        o3d_pcd = o3d.geometry.PointCloud()
        o3d_pcd.points = o3d.utility.Vector3dVector(pcd.points)
        
        if pcd.colors is not None:
            o3d_pcd.colors = o3d.utility.Vector3dVector(pcd.colors)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        o3d.io.write_point_cloud(str(output_path), o3d_pcd)
        logger.info(f"点云已保存至: {output_path}")
    
    def load_pointcloud(self, input_path: str) -> PointCloud3D:
        """加载PLY点云文件"""
        o3d_pcd = o3d.io.read_point_cloud(str(input_path))
        
        points = np.asarray(o3d_pcd.points)
        colors = np.asarray(o3d_pcd.colors) if o3d_pcd.has_colors() else None
        
        return PointCloud3D(points=points, colors=colors)

