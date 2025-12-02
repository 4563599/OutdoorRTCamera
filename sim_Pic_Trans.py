import os
import time
import shutil
import random
import logging
from datetime import datetime


def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 生成日志文件名（包含时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"sim_pic_trans_{timestamp}.log")

    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"日志文件: {log_file}")
    return logger


def simulate_image_transfer():
    """
    在本地构造与服务器一致的目录结构，逐相机拷贝样例图片以驱动监控脚本。

    会自动创建 TLS_* 批次目录、随机后缀，并按顺序复制多张图片。
    """

    # 设置日志
    logger = setup_logging()

    # 基础路径
    base_upload_path = r"D:\pic_back\atli_uploads"
    ocr_text_img_path = "ocr_text_img"  # 源图片文件夹

    logger.info(f"开始图片传输模拟")
    logger.info(f"上传基础路径: {base_upload_path}")
    logger.info(f"源图片路径: {ocr_text_img_path}")

    # 相机列表
    cameras = ["camera1", "camera2"]
    logger.info(f"目标相机: {cameras}")

    # 时间段配置
    time_periods = [
        {
            "source_img": "TLS_0202_0001.jpg",
            "folder_prefix": "TLS_0202",
            "random_suffixes": ["-random"]
        },
        {
            "source_img": "TLS_0203_0001.jpg",
            "folder_prefix": "TLS_0203",
            "random_suffixes": ["-test123"]
        }
    ]

    logger.info(f"配置时间段数量: {len(time_periods)}")
    for i, period in enumerate(time_periods):
        logger.info(f"时间段{i+1}: {period['folder_prefix']} - 源图片: {period['source_img']}")

    # 检查源图片是否存在
    logger.info("开始检查源图片...")
    for period in time_periods:
        source_path = os.path.join(ocr_text_img_path, period["source_img"])
        if not os.path.exists(source_path):
            logger.error(f"源图片不存在: {source_path}")
            print(f"错误: 源图片不存在 - {source_path}")
            return
        else:
            logger.info(f"源图片检查通过: {source_path}")

    logger.info("=" * 50)
    logger.info("开始模拟图片传输...")
    print("开始模拟图片传输...")

    # 处理每个时间段
    for i, period in enumerate(time_periods):
        source_img = period["source_img"]
        folder_prefix = period["folder_prefix"]

        logger.info(f"=" * 30)
        logger.info(f"开始处理时间段 {i+1}/{len(time_periods)}: {folder_prefix}")
        logger.info(f"源图片: {source_img}")
        print(f"\n=== 开始处理时间段: {folder_prefix} ===")

        # 为每个相机创建时间文件夹并传输图片
        created_folders = {}  # 记录创建的文件夹路径
        for camera in cameras:
            # 随机选择后缀
            suffix = random.choice(period["random_suffixes"])
            time_folder_name = f"{folder_prefix}{suffix}"
            time_folder_path = os.path.join(base_upload_path, camera, time_folder_name)

            # 创建时间文件夹
            try:
                os.makedirs(time_folder_path, exist_ok=True)
                created_folders[camera] = time_folder_name
                logger.info(f"创建文件夹成功: {camera}/{time_folder_name}")
                print(f"创建文件夹: {time_folder_path}")
            except Exception as e:
                logger.error(f"创建文件夹失败: {time_folder_path}, 错误: {e}")
                print(f"错误: 创建文件夹失败 - {time_folder_path}")
                continue

        logger.info("等待2秒后开始图片传输...")
        time.sleep(2)

        # 传输3张递增图片
        total_images = 3
        success_count = 0
        error_count = 0

        for img_num in range(1, total_images + 1):
            # 生成图片文件名
            filename = f"{folder_prefix}_{img_num:04d}.jpg"
            source_path = os.path.join(ocr_text_img_path, period["source_img"])

            logger.info(f"开始传输图片 {img_num}/{total_images}: {filename}")
            print(f"\n传输图片 {img_num}/{total_images}: {filename}")

            # 向每个相机文件夹传输图片
            for camera in cameras:
                try:
                    # 找到该相机的对应时间文件夹
                    camera_path = os.path.join(base_upload_path, camera)
                    time_folders = [f for f in os.listdir(camera_path)
                                    if f.startswith(folder_prefix) and os.path.isdir(os.path.join(camera_path, f))]

                    if time_folders:
                        time_folder = time_folders[0]  # 取第一个匹配的文件夹
                        dest_path = os.path.join(camera_path, time_folder, filename)

                        # 记录文件大小
                        file_size = os.path.getsize(source_path)

                        # 复制图片
                        start_time = time.time()
                        shutil.copy2(source_path, dest_path)
                        copy_time = time.time() - start_time

                        # 验证复制结果
                        if os.path.exists(dest_path):
                            dest_size = os.path.getsize(dest_path)
                            if dest_size == file_size:
                                logger.info(f"✅ {camera}/{time_folder}/{filename} 传输成功 ({file_size} bytes, 耗时 {copy_time:.3f}s)")
                                print(f"  传输到 {camera}/{time_folder}: {filename}")
                                success_count += 1
                            else:
                                logger.warning(f"⚠️ {camera}/{time_folder}/{filename} 文件大小不匹配 (源:{file_size} vs 目标:{dest_size})")
                                error_count += 1
                        else:
                            logger.error(f"❌ {camera}/{time_folder}/{filename} 复制后文件不存在")
                            error_count += 1
                    else:
                        logger.error(f"❌ {camera} 未找到匹配的时间文件夹 (prefix: {folder_prefix})")
                        error_count += 1

                except Exception as e:
                    logger.error(f"❌ {camera} 图片传输异常: {filename}, 错误: {e}")
                    error_count += 1

            # 等待间隔
            if img_num < total_images:  # 最后一张不需要等待
                logger.info("等待15秒后传输下一张图片...")
                print("等待15秒...")
                time.sleep(15)  # 实际使用时为60秒，测试时可改为5-10秒

        # 记录时间段传输统计
        logger.info(f"时间段 {folder_prefix} 传输统计: 成功 {success_count}, 失败 {error_count}")

        # 如果不是最后一个时间段，等待间隔
        if i < len(time_periods) - 1:
            logger.info(f"时间段 {folder_prefix} 完成，等待15秒后处理下一时间段...")
            print(f"\n时间段 {folder_prefix} 完成，等待15秒...")
            time.sleep(15)  # 实际使用时为300秒，测试时可改为15-30秒

    logger.info("=" * 50)
    logger.info("所有图片传输任务完成")
    total_success = success_count * len(time_periods)
    total_error = error_count * len(time_periods)
    logger.info(f"总体统计: 成功 {total_success}, 失败 {total_error}")
    print("\n=== 所有图片传输完成 ===")


if __name__ == "__main__":
    simulate_image_transfer()
