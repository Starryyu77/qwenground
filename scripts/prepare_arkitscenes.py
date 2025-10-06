#!/usr/bin/env python3
"""
ARKitScenes数据集准备脚本
将ARKitScenes数据集转换为QwenGround可用的格式

使用方法:
    python scripts/prepare_arkitscenes.py \
        --arkitscenes_dir /path/to/ARKitScenes \
        --output_dir ./data/arkitscenes_processed \
        --num_samples 5
"""

import os
import sys
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ARKitScenesPreparator:
    """ARKitScenes数据准备器"""
    
    def __init__(self, arkitscenes_dir: str, output_dir: str):
        self.arkitscenes_dir = Path(arkitscenes_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # ARKitScenes数据目录
        self.raw_dir = self.arkitscenes_dir / "raw"
        self.threedod_dir = self.arkitscenes_dir / "threedod"
        
    def download_sample_data(self, num_samples: int = 3, use_validation: bool = True):
        """
        下载示例数据
        
        Args:
            num_samples: 要下载的样本数量
            use_validation: 是否使用验证集（验证集通常较小）
        """
        logger.info(f"准备下载 {num_samples} 个ARKitScenes样本...")
        
        # 读取CSV文件获取video_id
        csv_file = self.threedod_dir / "3dod_train_val_splits.csv"
        if not csv_file.exists():
            logger.error(f"CSV文件不存在: {csv_file}")
            return []
        
        # 解析CSV
        video_ids = []
        with open(csv_file, 'r') as f:
            lines = f.readlines()[1:]  # 跳过header
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    video_id, fold = parts[1], parts[2]
                    if use_validation and fold == "Validation":
                        video_ids.append(video_id)
                    elif not use_validation and fold == "Training":
                        video_ids.append(video_id)
                
                if len(video_ids) >= num_samples:
                    break
        
        logger.info(f"选择的video_ids: {video_ids}")
        
        # 下载数据
        download_script = self.arkitscenes_dir / "download_data.py"
        if not download_script.exists():
            logger.error(f"下载脚本不存在: {download_script}")
            return []
        
        download_dir = self.output_dir / "raw_data"
        download_dir.mkdir(parents=True, exist_ok=True)
        
        for video_id in video_ids:
            logger.info(f"下载 video_id: {video_id}...")
            split = "Validation" if use_validation else "Training"
            
            cmd = [
                sys.executable,
                str(download_script),
                "3dod",
                "--split", split,
                "--video_id", video_id,
                "--download_dir", str(download_dir)
            ]
            
            try:
                subprocess.run(cmd, check=True, cwd=str(self.arkitscenes_dir))
                logger.info(f"✓ 成功下载 {video_id}")
            except subprocess.CalledProcessError as e:
                logger.error(f"✗ 下载 {video_id} 失败: {e}")
        
        return video_ids
    
    def convert_to_video(self, scene_dir: Path, output_video: Path, fps: int = 10):
        """
        将ARKitScenes的图像序列转换为视频
        
        Args:
            scene_dir: 场景目录（包含图像的文件夹）
            output_video: 输出视频路径
            fps: 帧率
        """
        logger.info(f"转换图像序列到视频: {scene_dir} -> {output_video}")
        
        # 查找RGB图像
        image_dir = scene_dir / "lowres_wide"
        if not image_dir.exists():
            logger.warning(f"图像目录不存在: {image_dir}")
            return False
        
        images = sorted(list(image_dir.glob("*.png")))
        if len(images) == 0:
            logger.warning(f"未找到图像: {image_dir}")
            return False
        
        logger.info(f"找到 {len(images)} 张图像")
        
        # 使用ffmpeg转换（如果可用）
        try:
            cmd = [
                "ffmpeg",
                "-framerate", str(fps),
                "-pattern_type", "glob",
                "-i", str(image_dir / "*.png"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-y",
                str(output_video)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✓ 成功创建视频: {output_video}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"ffmpeg转换失败，使用备选方案: {e}")
            
            # 备选方案：创建符号链接到图像目录
            images_link = output_video.parent / (output_video.stem + "_images")
            if images_link.exists():
                shutil.rmtree(images_link)
            images_link.mkdir(parents=True, exist_ok=True)
            
            for i, img in enumerate(images):
                dst = images_link / f"{i:06d}.png"
                shutil.copy2(img, dst)
            
            logger.info(f"✓ 创建图像序列: {images_link}")
            return True
    
    def extract_annotations(self, scene_dir: Path) -> List[Dict[str, Any]]:
        """
        提取场景的标注信息
        
        Args:
            scene_dir: 场景目录
            
        Returns:
            标注列表
        """
        annotation_file = scene_dir / "annotation.json"
        if not annotation_file.exists():
            logger.warning(f"标注文件不存在: {annotation_file}")
            return []
        
        with open(annotation_file, 'r') as f:
            annotations = json.load(f)
        
        # 提取物体信息
        objects = []
        if 'data' in annotations:
            for item in annotations['data']:
                if 'label' in item:
                    obj = {
                        'label': item['label'],
                        'bbox': item.get('segments', {}).get('bboxes', []),
                        'uid': item.get('uid', '')
                    }
                    objects.append(obj)
        
        logger.info(f"提取了 {len(objects)} 个物体标注")
        return objects
    
    def generate_test_queries(self, annotations: List[Dict[str, Any]]) -> List[str]:
        """
        根据标注生成测试查询
        
        Args:
            annotations: 物体标注列表
            
        Returns:
            查询列表
        """
        queries = []
        
        # 提取唯一的标签
        labels = set()
        for ann in annotations:
            label = ann.get('label', '').lower()
            if label:
                labels.add(label)
        
        # 生成查询
        for label in list(labels)[:5]:  # 最多5个查询
            queries.append(f"the {label}")
            queries.append(f"find the {label} in the scene")
        
        return queries[:5]  # 返回前5个查询
    
    def prepare_scene(self, video_id: str, split: str = "Validation"):
        """
        准备单个场景
        
        Args:
            video_id: 视频ID
            split: 数据集划分（Training/Validation）
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"准备场景: {video_id}")
        logger.info(f"{'='*60}")
        
        # 场景目录
        scene_dir = self.output_dir / "raw_data" / split / video_id
        if not scene_dir.exists():
            logger.error(f"场景目录不存在: {scene_dir}")
            return None
        
        # 输出目录
        output_scene_dir = self.output_dir / "processed" / video_id
        output_scene_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 转换为视频或保持图像序列
        video_path = output_scene_dir / f"{video_id}.mp4"
        images_dir = output_scene_dir / "images"
        
        # 复制图像
        src_images = scene_dir / "lowres_wide"
        if src_images.exists():
            if images_dir.exists():
                shutil.rmtree(images_dir)
            shutil.copytree(src_images, images_dir)
            logger.info(f"✓ 复制了图像序列到: {images_dir}")
        
        # 尝试创建视频
        self.convert_to_video(scene_dir, video_path)
        
        # 2. 提取标注
        annotations = self.extract_annotations(scene_dir)
        
        # 3. 生成测试查询
        queries = self.generate_test_queries(annotations)
        
        # 4. 保存元数据
        metadata = {
            'video_id': video_id,
            'split': split,
            'video_path': str(video_path.relative_to(self.output_dir)),
            'images_dir': str(images_dir.relative_to(self.output_dir)),
            'num_images': len(list(images_dir.glob("*.png"))) if images_dir.exists() else 0,
            'annotations': annotations,
            'test_queries': queries
        }
        
        metadata_file = output_scene_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, indent=2, fp=f)
        
        logger.info(f"✓ 保存元数据到: {metadata_file}")
        logger.info(f"  - 图像数量: {metadata['num_images']}")
        logger.info(f"  - 物体标注: {len(annotations)}")
        logger.info(f"  - 测试查询: {len(queries)}")
        
        return metadata
    
    def generate_test_script(self, scenes_metadata: List[Dict[str, Any]]):
        """
        生成测试脚本
        
        Args:
            scenes_metadata: 场景元数据列表
        """
        test_script = self.output_dir / "run_tests.sh"
        
        with open(test_script, 'w') as f:
            f.write("#!/bin/bash\n\n")
            f.write("# ARKitScenes测试脚本\n")
            f.write("# 自动生成，用于测试QwenGround系统\n\n")
            f.write("QWENGROUND_DIR=\"../..\"  # QwenGround项目目录\n")
            f.write("OUTPUT_BASE=\"./test_outputs\"\n\n")
            
            for i, metadata in enumerate(scenes_metadata):
                video_id = metadata['video_id']
                images_dir = self.output_dir / metadata['images_dir']
                queries = metadata['test_queries']
                
                f.write(f"\n# ===== 测试场景 {i+1}: {video_id} =====\n")
                
                for j, query in enumerate(queries[:3]):  # 每个场景测试3个查询
                    f.write(f"\necho \"测试 {i+1}.{j+1}: {query}\"\n")
                    f.write(f"python $QWENGROUND_DIR/qwenground_main.py \\\n")
                    f.write(f"    --input_type images \\\n")
                    f.write(f"    --input_path \"{images_dir}\" \\\n")
                    f.write(f"    --query \"{query}\" \\\n")
                    f.write(f"    --device cpu \\\n")
                    f.write(f"    --output_dir \"$OUTPUT_BASE/{video_id}/query_{j+1}\" \\\n")
                    f.write(f"    --save_intermediate\n")
                    f.write(f"\necho \"完成测试 {i+1}.{j+1}\"\n")
                    f.write(f"echo \"{'='*60}\"\n")
            
            f.write("\necho \"所有测试完成！\"\n")
        
        # 使脚本可执行
        os.chmod(test_script, 0o755)
        logger.info(f"\n✓ 生成测试脚本: {test_script}")
        logger.info(f"  运行方式: cd {self.output_dir} && ./run_tests.sh")


def main():
    parser = argparse.ArgumentParser(
        description="准备ARKitScenes数据集用于QwenGround测试"
    )
    parser.add_argument(
        "--arkitscenes_dir",
        type=str,
        default="../ARKitScenes",
        help="ARKitScenes仓库目录"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./data/arkitscenes_processed",
        help="处理后数据的输出目录"
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        default=3,
        help="要下载和处理的样本数量"
    )
    parser.add_argument(
        "--skip_download",
        action="store_true",
        help="跳过下载步骤（如果数据已经存在）"
    )
    
    args = parser.parse_args()
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║         ARKitScenes 数据准备工具                              ║
    ║         for QwenGround System                                 ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # 创建准备器
    preparator = ARKitScenesPreparator(
        arkitscenes_dir=args.arkitscenes_dir,
        output_dir=args.output_dir
    )
    
    # 1. 下载数据
    if not args.skip_download:
        video_ids = preparator.download_sample_data(
            num_samples=args.num_samples,
            use_validation=True
        )
        if not video_ids:
            logger.error("下载失败，退出")
            return
    else:
        # 从现有数据中查找video_ids
        raw_data_dir = Path(args.output_dir) / "raw_data" / "Validation"
        if raw_data_dir.exists():
            video_ids = [d.name for d in raw_data_dir.iterdir() if d.is_dir()]
            logger.info(f"找到已存在的场景: {video_ids}")
        else:
            logger.error("未找到已存在的数据")
            return
    
    # 2. 处理每个场景
    scenes_metadata = []
    for video_id in video_ids:
        metadata = preparator.prepare_scene(video_id, split="Validation")
        if metadata:
            scenes_metadata.append(metadata)
    
    # 3. 生成测试脚本
    if scenes_metadata:
        preparator.generate_test_script(scenes_metadata)
    
    # 4. 输出总结
    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                    准备完成！                                  ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    📊 处理总结:
       - 处理场景数: {len(scenes_metadata)}
       - 输出目录: {args.output_dir}
    
    🚀 下一步:
       1. 查看处理后的数据: ls {args.output_dir}/processed/
       2. 运行测试脚本: cd {args.output_dir} && ./run_tests.sh
       3. 或手动运行单个测试
    
    📖 示例命令:
       python qwenground_main.py \\
           --input_type images \\
           --input_path {args.output_dir}/processed/VIDEO_ID/images \\
           --query "the chair" \\
           --device cpu \\
           --output_dir ./outputs
    """)


if __name__ == "__main__":
    main()

