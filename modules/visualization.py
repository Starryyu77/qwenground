"""
Visualization Module
3D场景和边界框可视化
"""

import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import cv2
from pathlib import Path
from typing import List, Optional, Tuple
import logging

from modules.reconstruction_3d import PointCloud3D
from modules.object_lookup_table import Object3D

logger = logging.getLogger(__name__)


class Visualizer:
    """3D可视化器"""
    
    def __init__(self):
        self.window_name = "QwenGround 3D Visualization"
    
    def visualize_pointcloud_with_bbox(self,
                                      pointcloud: PointCloud3D,
                                      target_object: Optional[Object3D] = None,
                                      output_path: Optional[str] = None,
                                      show_interactive: bool = True):
        """
        可视化点云和3D边界框
        
        Args:
            pointcloud: 3D点云
            target_object: 目标物体（包含3D边界框）
            output_path: 保存路径
            show_interactive: 是否显示交互式窗口
        """
        logger.info("生成3D可视化...")
        
        # 创建Open3D点云对象
        o3d_pcd = o3d.geometry.PointCloud()
        o3d_pcd.points = o3d.utility.Vector3dVector(pointcloud.points)
        
        if pointcloud.colors is not None:
            o3d_pcd.colors = o3d.utility.Vector3dVector(pointcloud.colors)
        
        # 创建可视化几何体列表
        geometries = [o3d_pcd]
        
        # 添加坐标系
        coord_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
            size=0.5, origin=[0, 0, 0]
        )
        geometries.append(coord_frame)
        
        # 如果有目标物体，添加边界框
        if target_object and target_object.bbox_3d:
            bbox_mesh = self._create_bbox_mesh(
                target_object.bbox_3d,
                color=[0, 1, 0]  # 绿色
            )
            geometries.append(bbox_mesh)
            
            # 添加标签（使用文本网格）
            # Open3D 不直接支持文本，这里用点表示中心
            if target_object.center_3d:
                center_point = o3d.geometry.TriangleMesh.create_sphere(radius=0.1)
                center_point.translate(target_object.center_3d)
                center_point.paint_uniform_color([1, 0, 0])  # 红色
                geometries.append(center_point)
        
        # 保存为PLY文件
        if output_path:
            self._save_visualization(geometries, output_path)
        
        # 显示交互式窗口
        if show_interactive:
            try:
                o3d.visualization.draw_geometries(
                    geometries,
                    window_name=self.window_name,
                    width=1280,
                    height=720
                )
            except Exception as e:
                logger.warning(f"交互式可视化失败（可能是在无显示环境）: {e}")
    
    def _create_bbox_mesh(self, 
                         bbox_3d: List[float],
                         color: List[float] = [0, 1, 0]) -> o3d.geometry.LineSet:
        """
        创建3D边界框线框
        
        Args:
            bbox_3d: [x, y, z, w, h, d] (中心坐标 + 尺寸)
            color: RGB颜色 (0-1)
            
        Returns:
            Open3D LineSet
        """
        x, y, z, w, h, d = bbox_3d
        
        # 计算8个角点
        half_w, half_h, half_d = w / 2, h / 2, d / 2
        
        corners = np.array([
            [x - half_w, y - half_h, z - half_d],  # 0: 左下后
            [x + half_w, y - half_h, z - half_d],  # 1: 右下后
            [x + half_w, y + half_h, z - half_d],  # 2: 右上后
            [x - half_w, y + half_h, z - half_d],  # 3: 左上后
            [x - half_w, y - half_h, z + half_d],  # 4: 左下前
            [x + half_w, y - half_h, z + half_d],  # 5: 右下前
            [x + half_w, y + half_h, z + half_d],  # 6: 右上前
            [x - half_w, y + half_h, z + half_d],  # 7: 左上前
        ])
        
        # 定义12条边
        lines = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # 后面
            [4, 5], [5, 6], [6, 7], [7, 4],  # 前面
            [0, 4], [1, 5], [2, 6], [3, 7],  # 连接前后
        ]
        
        # 创建LineSet
        line_set = o3d.geometry.LineSet()
        line_set.points = o3d.utility.Vector3dVector(corners)
        line_set.lines = o3d.utility.Vector2iVector(lines)
        
        # 设置颜色
        colors = [color for _ in range(len(lines))]
        line_set.colors = o3d.utility.Vector3dVector(colors)
        
        return line_set
    
    def _save_visualization(self, geometries: List, output_path: str):
        """保存可视化结果"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 合并所有几何体到一个场景
        # Open3D不直接支持保存多个几何体到一个文件
        # 这里只保存点云
        
        for geom in geometries:
            if isinstance(geom, o3d.geometry.PointCloud):
                o3d.io.write_point_cloud(str(output_path), geom)
                logger.info(f"点云已保存至: {output_path}")
                break
    
    def create_rotation_animation(self,
                                 pointcloud: PointCloud3D,
                                 target_object: Optional[Object3D] = None,
                                 output_path: str = "output_animation.gif",
                                 num_frames: int = 36,
                                 fps: int = 10):
        """
        创建旋转动画
        
        Args:
            pointcloud: 3D点云
            target_object: 目标物体
            output_path: 输出GIF路径
            num_frames: 帧数
            fps: 帧率
        """
        logger.info("生成旋转动画...")
        
        try:
            # 使用matplotlib创建动画
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            # 准备点云数据
            points = pointcloud.points
            colors = pointcloud.colors if pointcloud.colors is not None else 'blue'
            
            # 下采样以加速渲染
            if len(points) > 10000:
                indices = np.random.choice(len(points), 10000, replace=False)
                points = points[indices]
                if isinstance(colors, np.ndarray):
                    colors = colors[indices]
            
            def update(frame):
                ax.clear()
                
                # 绘制点云
                if isinstance(colors, np.ndarray):
                    ax.scatter(points[:, 0], points[:, 1], points[:, 2],
                             c=colors, s=1, alpha=0.5)
                else:
                    ax.scatter(points[:, 0], points[:, 1], points[:, 2],
                             c=colors, s=1, alpha=0.5)
                
                # 绘制边界框
                if target_object and target_object.bbox_3d:
                    self._draw_bbox_matplotlib(ax, target_object.bbox_3d)
                
                # 设置视角
                angle = frame * 360 / num_frames
                ax.view_init(elev=20, azim=angle)
                
                # 设置标签和标题
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_zlabel('Z')
                ax.set_title(f'QwenGround 3D Scene (Frame {frame+1}/{num_frames})')
                
                # 设置相同的坐标范围
                max_range = np.max([
                    points[:, 0].max() - points[:, 0].min(),
                    points[:, 1].max() - points[:, 1].min(),
                    points[:, 2].max() - points[:, 2].min()
                ]) / 2
                
                mid_x = (points[:, 0].max() + points[:, 0].min()) / 2
                mid_y = (points[:, 1].max() + points[:, 1].min()) / 2
                mid_z = (points[:, 2].max() + points[:, 2].min()) / 2
                
                ax.set_xlim(mid_x - max_range, mid_x + max_range)
                ax.set_ylim(mid_y - max_range, mid_y + max_range)
                ax.set_zlim(mid_z - max_range, mid_z + max_range)
            
            # 创建动画
            anim = FuncAnimation(fig, update, frames=num_frames, interval=1000/fps)
            
            # 保存为GIF
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            anim.save(str(output_path), writer='pillow', fps=fps)
            logger.info(f"动画已保存至: {output_path}")
            
            plt.close()
            
        except Exception as e:
            logger.error(f"创建动画失败: {e}")
    
    def _draw_bbox_matplotlib(self, ax, bbox_3d: List[float]):
        """在matplotlib 3D图上绘制边界框"""
        x, y, z, w, h, d = bbox_3d
        
        half_w, half_h, half_d = w / 2, h / 2, d / 2
        
        # 8个角点
        corners = np.array([
            [x - half_w, y - half_h, z - half_d],
            [x + half_w, y - half_h, z - half_d],
            [x + half_w, y + half_h, z - half_d],
            [x - half_w, y + half_h, z - half_d],
            [x - half_w, y - half_h, z + half_d],
            [x + half_w, y - half_h, z + half_d],
            [x + half_w, y + half_h, z + half_d],
            [x - half_w, y + half_h, z + half_d],
        ])
        
        # 12条边
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # 后面
            [4, 5], [5, 6], [6, 7], [7, 4],  # 前面
            [0, 4], [1, 5], [2, 6], [3, 7],  # 连接
        ]
        
        for edge in edges:
            points = corners[edge]
            ax.plot3D(*points.T, color='red', linewidth=2)
    
    def save_result_images(self,
                          keyframes: List,
                          target_object: Object3D,
                          output_dir: str):
        """
        保存结果图像（关键帧上标注目标物体）
        
        Args:
            keyframes: 关键帧列表
            target_object: 目标物体
            output_dir: 输出目录
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"保存结果图像到: {output_dir}")
        
        # 找到目标物体出现的帧
        target_frame_ids = target_object.frame_ids or []
        
        for kf in keyframes:
            frame_id = kf["frame_id"]
            
            if frame_id not in target_frame_ids:
                continue
            
            frame = kf["frame"].copy()
            h, w = frame.shape[:2]
            
            # 绘制边界框
            x1, y1, x2, y2 = target_object.bbox_2d
            x1, y1 = int(x1 * w), int(y1 * h)
            x2, y2 = int(x2 * w), int(y2 * h)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
            
            # 添加标签
            label = f"Target: {target_object.class_name}"
            cv2.putText(
                frame, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
            )
            
            # 保存
            output_path = output_dir / f"result_frame_{frame_id:04d}.jpg"
            cv2.imwrite(str(output_path), frame)
        
        logger.info(f"已保存 {len(target_frame_ids)} 张结果图像")
    
    def generate_summary_visualization(self,
                                      pointcloud: PointCloud3D,
                                      target_object: Object3D,
                                      query: str,
                                      output_path: str):
        """
        生成汇总可视化（2D图像）
        
        Args:
            pointcloud: 点云
            target_object: 目标物体
            query: 查询文本
            output_path: 输出路径
        """
        fig = plt.figure(figsize=(15, 5))
        
        # 子图1: 点云俯视图
        ax1 = fig.add_subplot(131)
        points = pointcloud.points
        ax1.scatter(points[:, 0], points[:, 1], s=0.5, alpha=0.5)
        
        if target_object.center_3d:
            cx, cy = target_object.center_3d[0], target_object.center_3d[1]
            ax1.scatter([cx], [cy], c='red', s=100, marker='*', label='Target')
            ax1.legend()
        
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.set_title('Top View')
        ax1.axis('equal')
        
        # 子图2: 点云侧视图
        ax2 = fig.add_subplot(132)
        ax2.scatter(points[:, 0], points[:, 2], s=0.5, alpha=0.5)
        
        if target_object.center_3d:
            cx, cz = target_object.center_3d[0], target_object.center_3d[2]
            ax2.scatter([cx], [cz], c='red', s=100, marker='*', label='Target')
            ax2.legend()
        
        ax2.set_xlabel('X')
        ax2.set_ylabel('Z')
        ax2.set_title('Side View')
        ax2.axis('equal')
        
        # 子图3: 信息文本
        ax3 = fig.add_subplot(133)
        ax3.axis('off')
        
        info_text = f"""
Query: {query}

Target Object:
  Class: {target_object.class_name}
  Confidence: {target_object.confidence:.3f}
  
3D Bounding Box:
  Center: ({target_object.center_3d[0]:.2f}, {target_object.center_3d[1]:.2f}, {target_object.center_3d[2]:.2f})
  Size: {target_object.bbox_3d[3:]:.2f}
  
Point Cloud:
  Total Points: {len(points)}
        """
        
        ax3.text(0.1, 0.5, info_text, fontsize=10, verticalalignment='center',
                family='monospace')
        
        plt.tight_layout()
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"汇总可视化已保存至: {output_path}")

