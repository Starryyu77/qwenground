"""
QwenGround System - Main System Class
零-shot 3D场景理解和定位系统
"""

import time
from pathlib import Path
from typing import Dict, Optional, Union
import logging

from modules.perspective_adapter import PerspectiveAdapter
from modules.reconstruction_3d import Reconstruction3D, PointCloud3D
from modules.fusion_alignment import FusionAlignment
from modules.object_lookup_table import ObjectLookupTable, Object3D
from modules.visualization import Visualizer
from utils.vlm_client import QwenVLMClient
from utils.object_detector import ObjectDetector
from utils.helpers import save_json

logger = logging.getLogger(__name__)


class QwenGroundSystem:
    """QwenGround主系统类"""
    
    def __init__(self,
                 model_name: str = "Qwen/Qwen2-VL-7B-Instruct",
                 device: str = "cuda",
                 use_api: bool = False,
                 api_url: Optional[str] = None,
                 api_key: Optional[str] = None,
                 config: Optional[Dict] = None):
        """
        初始化QwenGround系统
        
        Args:
            model_name: VLM模型名称
            device: 设备 (cuda/cpu)
            use_api: 是否使用API模式
            api_url: API服务器地址
            api_key: API密钥
            config: 配置字典（可选）
        """
        logger.info("初始化QwenGround系统...")
        
        self.model_name = model_name
        self.device = device
        self.config = config or self._default_config()
        
        # 初始化各个模块
        logger.info("初始化模块...")
        
        # 1. VLM客户端
        self.vlm_client = QwenVLMClient(
            model_name=model_name,
            device=device,
            use_api=use_api,
            api_url=api_url,
            api_key=api_key
        )
        
        # 2. 物体检测器
        self.object_detector = ObjectDetector(
            model_name=self.config['detection']['yolo_model'],
            conf_threshold=self.config['detection']['conf_threshold'],
            iou_threshold=self.config['detection']['iou_threshold'],
            device=device
        )
        
        # 3. 视角适应模块
        self.perspective_adapter = PerspectiveAdapter(
            keyframe_count=self.config['reconstruction']['keyframe_count'],
            min_scene_change=0.3,
            target_resolution=(1280, 720)
        )
        
        # 4. 3D重建模块
        self.reconstruction_3d = Reconstruction3D(
            depth_model_type=self.config['reconstruction']['depth_model'],
            voxel_size=0.05,
            use_gpu=(device == "cuda")
        )
        
        # 5. 融合对齐模块
        self.fusion_alignment = FusionAlignment(
            vlm_client=self.vlm_client,
            object_detector=self.object_detector
        )
        
        # 6. 可视化器
        self.visualizer = Visualizer()
        
        logger.info("系统初始化完成")
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'reconstruction': {
                'keyframe_count': 15,
                'depth_model': 'MiDaS_small',
                'method': 'depth',  # 'depth' or 'sfm'
            },
            'detection': {
                'yolo_model': 'yolov8x.pt',
                'conf_threshold': 0.25,
                'iou_threshold': 0.5,
            },
            'vlm': {
                'max_tokens': 512,
                'temperature': 0.1,
            }
        }
    
    def run(self,
            input_path: str,
            query: str,
            input_type: str = "video",
            output_dir: str = "./outputs",
            visualize: bool = True,
            save_intermediate: bool = False) -> Dict:
        """
        运行完整的QwenGround流程
        
        Args:
            input_path: 输入路径（视频文件或图像文件夹）
            query: 自然语言查询
            input_type: 输入类型 ("video" 或 "images")
            output_dir: 输出目录
            visualize: 是否生成可视化
            save_intermediate: 是否保存中间结果
            
        Returns:
            结果字典
        """
        logger.info("="*60)
        logger.info("开始运行QwenGround")
        logger.info(f"输入: {input_path}")
        logger.info(f"查询: {query}")
        logger.info(f"输入类型: {input_type}")
        logger.info("="*60)
        
        start_time = time.time()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # ===== 步骤1: 视角适应 =====
            logger.info("\n[1/5] 视角适应：提取关键帧...")
            step_start = time.time()
            
            if input_type == "video":
                keyframes = self.perspective_adapter.extract_keyframes_from_video(
                    input_path,
                    method="hybrid"
                )
            else:  # images
                keyframes = self.perspective_adapter.load_images_from_folder(input_path)
            
            logger.info(f"  ✓ 提取了 {len(keyframes)} 个关键帧 (耗时: {time.time()-step_start:.2f}s)")
            
            # ===== 步骤2: 3D重建 =====
            logger.info("\n[2/5] 3D重建：生成点云...")
            step_start = time.time()
            
            pointcloud = self.reconstruction_3d.reconstruct_from_keyframes(
                keyframes,
                method=self.config['reconstruction']['method']
            )
            
            logger.info(f"  ✓ 生成点云: {len(pointcloud.points)} 个点 (耗时: {time.time()-step_start:.2f}s)")
            
            if save_intermediate:
                pcd_path = output_dir / "pointcloud.ply"
                self.reconstruction_3d.save_pointcloud(pointcloud, str(pcd_path))
            
            # ===== 步骤3: 构建OLT =====
            logger.info("\n[3/5] 构建Object Lookup Table...")
            step_start = time.time()
            
            olt = self.fusion_alignment.build_olt_from_keyframes(keyframes, pointcloud)
            
            logger.info(f"  ✓ 检测到 {len(olt)} 个唯一物体 (耗时: {time.time()-step_start:.2f}s)")
            
            if save_intermediate:
                olt_path = output_dir / "olt.json"
                olt.save(str(olt_path))
            
            # ===== 步骤4: 目标定位 =====
            logger.info("\n[4/5] 目标定位：使用VLM进行grounding...")
            step_start = time.time()
            
            target_object = self.fusion_alignment.ground_target_object(
                query, keyframes, olt
            )
            
            if target_object is None:
                logger.error("  ✗ 未能定位目标物体")
                return self._create_error_result("未能定位目标物体")
            
            logger.info(f"  ✓ 成功定位: {target_object.class_name} (耗时: {time.time()-step_start:.2f}s)")
            
            # ===== 步骤5: 可视化 =====
            if visualize:
                logger.info("\n[5/5] 生成可视化...")
                step_start = time.time()
                
                # 3D可视化
                self.visualizer.visualize_pointcloud_with_bbox(
                    pointcloud,
                    target_object,
                    output_path=str(output_dir / "scene_with_bbox.ply"),
                    show_interactive=False
                )
                
                # 旋转动画
                self.visualizer.create_rotation_animation(
                    pointcloud,
                    target_object,
                    output_path=str(output_dir / "animation.gif"),
                    num_frames=36,
                    fps=10
                )
                
                # 汇总可视化
                self.visualizer.generate_summary_visualization(
                    pointcloud,
                    target_object,
                    query,
                    output_path=str(output_dir / "summary.png")
                )
                
                # 保存结果图像
                self.visualizer.save_result_images(
                    keyframes,
                    target_object,
                    output_dir=str(output_dir / "result_images")
                )
                
                logger.info(f"  ✓ 可视化完成 (耗时: {time.time()-step_start:.2f}s)")
            
            # ===== 生成最终结果 =====
            total_time = time.time() - start_time
            
            result = self._create_result(
                query=query,
                target_object=target_object,
                num_frames=len(keyframes),
                num_objects=len(olt),
                processing_time=total_time,
                output_dir=str(output_dir)
            )
            
            # 保存结果JSON
            result_path = output_dir / "result.json"
            save_json(result, str(result_path))
            
            logger.info("\n" + "="*60)
            logger.info("✅ QwenGround完成!")
            logger.info(f"总耗时: {total_time:.2f}秒")
            logger.info(f"结果已保存至: {output_dir}")
            logger.info("="*60 + "\n")
            
            return result
            
        except Exception as e:
            logger.error(f"运行失败: {e}", exc_info=True)
            return self._create_error_result(str(e))
    
    def _create_result(self,
                      query: str,
                      target_object: Object3D,
                      num_frames: int,
                      num_objects: int,
                      processing_time: float,
                      output_dir: str) -> Dict:
        """创建结果字典"""
        # 解析查询获取组件
        query_components = self.vlm_client.extract_query_components(query)
        
        return {
            "success": True,
            "query": query,
            "query_components": query_components,
            "target_object": target_object.class_name,
            "anchor_object": query_components.get("anchor"),
            "spatial_relation": query_components.get("relation"),
            "3d_bbox": target_object.bbox_3d,
            "bbox_format": "xyzwhd",
            "center_3d": target_object.center_3d,
            "confidence": target_object.confidence,
            "metadata": {
                "num_frames": num_frames,
                "num_objects": num_objects,
                "processing_time": round(processing_time, 2),
                "model": self.model_name,
                "device": self.device
            },
            "output_files": {
                "point_cloud": f"{output_dir}/pointcloud.ply",
                "scene_with_bbox": f"{output_dir}/scene_with_bbox.ply",
                "animation": f"{output_dir}/animation.gif",
                "summary": f"{output_dir}/summary.png",
                "result_images": f"{output_dir}/result_images/"
            }
        }
    
    def _create_error_result(self, error_message: str) -> Dict:
        """创建错误结果"""
        return {
            "success": False,
            "error": error_message,
            "target_object": None,
            "3d_bbox": None,
            "confidence": 0.0
        }

