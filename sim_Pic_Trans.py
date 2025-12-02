import os
import time
import shutil
import random


def simulate_image_transfer():
    """模拟向相机文件夹传输图片的脚本"""

    # 基础路径
    base_upload_path = r"G:\Outdoor_RTCamProc\RT_text\atli_uploads"
    ocr_text_img_path = "ocr_text_img"  # 源图片文件夹

    # 相机列表
    cameras = ["camera1", "camera2"]

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

    # 检查源图片是否存在
    for period in time_periods:
        source_path = os.path.join(ocr_text_img_path, period["source_img"])
        if not os.path.exists(source_path):
            print(f"错误: 源图片不存在 - {source_path}")
            return

    print("开始模拟图片传输...")

    # 处理每个时间段
    for i, period in enumerate(time_periods):
        source_img = period["source_img"]
        folder_prefix = period["folder_prefix"]

        print(f"\n=== 开始处理时间段: {folder_prefix} ===")

        # 为每个相机创建时间文件夹并传输图片
        for camera in cameras:
            # 随机选择后缀
            suffix = random.choice(period["random_suffixes"])
            time_folder_name = f"{folder_prefix}{suffix}"
            time_folder_path = os.path.join(base_upload_path, camera, time_folder_name)

            # 创建时间文件夹
            os.makedirs(time_folder_path, exist_ok=True)
            print(f"创建文件夹: {time_folder_path}")

        time.sleep(2)
        # 传输5张递增图片
        for img_num in range(1, 4):
            # 生成图片文件名
            filename = f"{folder_prefix}_{img_num:04d}.jpg"
            source_path = os.path.join(ocr_text_img_path, period["source_img"])

            print(f"\n传输图片 {img_num}/3: {filename}")

            # 向每个相机文件夹传输图片
            for camera in cameras:
                # 找到该相机的对应时间文件夹
                camera_path = os.path.join(base_upload_path, camera)
                time_folders = [f for f in os.listdir(camera_path)
                                if f.startswith(folder_prefix) and os.path.isdir(os.path.join(camera_path, f))]

                if time_folders:
                    time_folder = time_folders[0]  # 取第一个匹配的文件夹
                    dest_path = os.path.join(camera_path, time_folder, filename)

                    # 复制图片
                    shutil.copy2(source_path, dest_path)
                    print(f"  传输到 {camera}/{time_folder}: {filename}")

            # 等待1分钟（测试时可缩短为几秒）
            if img_num < 5:  # 最后一张不需要等待
                print("等待15秒...")
                time.sleep(15)  # 实际使用时为60秒，测试时可改为5-10秒

        # 如果不是最后一个时间段，等待5分钟
        if i < len(time_periods) - 1:
            print(f"\n时间段 {folder_prefix} 完成，等待15秒...")
            time.sleep(15)  # 实际使用时为300秒，测试时可改为15-30秒

    print("\n=== 所有图片传输完成 ===")


if __name__ == "__main__":
    simulate_image_transfer()