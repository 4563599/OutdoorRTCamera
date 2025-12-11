import os
import shutil
import time
import threading
from pathlib import Path
import logging
from datetime import datetime

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CameraSimulator:
    def __init__(self, source_base_path, target_base_path, camera_mapping):
        """
        初始化相机模拟器

        Args:
            source_base_path: 源文件夹路径 (serve_text_data)
            target_base_path: 目标文件夹路径 (RT_text/atli_uploads)
            camera_mapping: 相机映射字典 {源相机文件夹: 目标相机文件夹}
        """
        self.source_base_path = Path(source_base_path)
        self.target_base_path = Path(target_base_path)
        self.camera_mapping = camera_mapping

        # 确保目标文件夹存在
        self.target_base_path.mkdir(parents=True, exist_ok=True)
        for target_camera in camera_mapping.values():
            (self.target_base_path / target_camera).mkdir(parents=True, exist_ok=True)

    def process_camera(self, source_camera, target_camera):
        """
        处理单个相机的图片传输

        Args:
            source_camera: 源相机文件夹名
            target_camera: 目标相机文件夹名
        """
        logger.info(f"开始处理相机 {source_camera} -> {target_camera}")

        # 源相机路径
        source_camera_path = self.source_base_path / source_camera

        # 检查源相机文件夹是否存在
        if not source_camera_path.exists():
            logger.error(f"源相机文件夹不存在: {source_camera_path}")
            return

        # 获取时间段文件夹并排序
        time_folders = sorted([
            folder for folder in source_camera_path.iterdir()
            if folder.is_dir()
        ])

        logger.info(f"相机 {source_camera} 找到 {len(time_folders)} 个时间段文件夹")

        for time_folder in time_folders:
            # 1. 创建同名时间段文件夹
            target_time_folder = self.target_base_path / target_camera / time_folder.name
            target_time_folder.mkdir(exist_ok=True)
            logger.info(f"相机 {source_camera}: 创建文件夹 {target_time_folder}")

            # 等待2秒
            time.sleep(5)

            # 2. 获取时间段文件夹中的图片并排序
            image_files = sorted([
                img for img in time_folder.iterdir()
                if img.is_file() and img.suffix.lower() in ['.jpg', '.jpeg', '.png']
            ])

            logger.info(f"相机 {source_camera}/{time_folder.name}: 找到 {len(image_files)} 张图片")

            # 3. 每隔15秒复制一张图片
            for img_file in image_files:
                # 复制图片
                target_img_path = target_time_folder / img_file.name

                try:
                    shutil.copy2(img_file, target_img_path)
                    logger.info(f"相机 {source_camera}: 复制 {img_file.name} -> {target_img_path}")
                except Exception as e:
                    logger.error(f"复制图片失败: {e}")
                    continue

                time.sleep(15)

            # 4. 当前时间段文件夹所有图片复制完成后，等待15秒
            logger.info(f"相机 {source_camera}/{time_folder.name}: 所有图片复制完成，等待15秒")
            time.sleep(15)

        logger.info(f"相机 {source_camera} 处理完成")

    def simulate_all_cameras(self):
        """
        模拟所有相机的传输流程（使用多线程实现同时传输）
        """
        threads = []

        # 为每个相机创建线程
        for source_camera, target_camera in self.camera_mapping.items():
            thread = threading.Thread(
                target=self.process_camera,
                args=(source_camera, target_camera),
                name=f"Camera-{source_camera}"
            )
            threads.append(thread)
            thread.start()
            logger.info(f"启动相机 {source_camera} 的传输线程")

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        logger.info("所有相机传输完成")


def main():
    """
    主函数
    """
    # 配置路径和映射关系
    SOURCE_BASE = "serve_text_data"
    TARGET_BASE = "RT_text/atli_uploads"

    # 相机映射关系：{源相机文件夹: 目标相机文件夹}
    CAMERA_MAPPING = {
        "176": "camera1",  # 源相机176 -> 目标camera1
        "293": "camera2"  # 源相机293 -> 目标camera2
    }

    # 创建模拟器并开始传输
    simulator = CameraSimulator(SOURCE_BASE, TARGET_BASE, CAMERA_MAPPING)

    try:
        simulator.simulate_all_cameras()
        print("\n" + "=" * 60)
        print("传输模拟完成！")
        print("=" * 60)

        # 显示目标文件夹结构
        print("\n目标文件夹结构:")
        show_folder_structure(TARGET_BASE, prefix="  ")

    except KeyboardInterrupt:
        print("\n传输被用户中断")
    except Exception as e:
        logger.error(f"传输过程中发生错误: {e}")


def show_folder_structure(folder_path, prefix=""):
    """
    显示文件夹结构

    Args:
        folder_path: 文件夹路径
        prefix: 显示前缀
    """
    try:
        for item in sorted(Path(folder_path).iterdir()):
            if item.is_dir():
                print(f"{prefix}├── {item.name}/")
                # 显示子目录下的文件夹
                for subitem in sorted(item.iterdir()):
                    if subitem.is_dir():
                        print(f"{prefix}│   ├── {subitem.name}/")
                        # 显示图片文件
                        images = sorted([
                            f.name for f in subitem.iterdir()
                            if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']
                        ])
                        for i, img in enumerate(images):
                            connector = "└──" if i == len(images) - 1 else "├──"
                            print(f"{prefix}│   │   {connector} {img}")
    except Exception as e:
        print(f"{prefix}错误: {e}")

if __name__ == "__main__":
    main()