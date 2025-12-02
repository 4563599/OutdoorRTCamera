# 1.确定ATLI相机在服务器上文件保存路径
# 2.在本地模拟往这种结构的文件夹传输图片
# 3.识别到文件夹中出现新图片，开始处理，包括：
#   解析时间戳，提取像素坐标，将像素坐标文件保存到另一文件夹路径（基于输入路径构建）下，最后将图片备份

import os
import time

import cv2
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ocr_Ex_time import ocr_Ex_time
import threading
import shutil
from Ex_Pixel import ExPixelCoord

def Ex_pixel(src_path):
    return np.array([[120, 280]])

class CameraMonitor:
    def __init__(self, base_upload_path, base_processed_path, camera_configs):
        """
        初始化相机监控器
        Args:
            base_upload_path: 基础上传路径
            base_processed_path: 基础处理路径
            camera_configs: 相机配置字典，格式为：
                {
                    'camera1': {
                        'polygon_pts': np.array([...]),  # 多边形区域坐标
                        'pre_points': None  # 初始化的前一点，可为None
                    },
                    'camera2': {
                        'polygon_pts': np.array([...]),
                        'pre_points': None
                    }
                }
        """
        self.base_upload_path = base_upload_path
        self.base_processed_path = base_processed_path
        self.camera_configs = camera_configs
        self.cameras = list(camera_configs.keys())
        self.observers = []

        # 为每个相机创建ExPixelCoord对象
        self.ex_pixel_coord_objects = {}
        for camera_name, config in camera_configs.items():
            polygon_pts = config.get('polygon_pts')
            pre_points = config.get('pre_points', None)
            if polygon_pts is not None:
                self.ex_pixel_coord_objects[camera_name] = ExPixelCoord(polygon_pts, pre_points)
            else:
                print(f"警告: 相机 {camera_name} 缺少 polygon_pts 配置")

    def start_monitoring(self):
        """开始监控所有相机"""
        for camera in self.cameras:
            camera_upload_path = os.path.join(self.base_upload_path, camera)
            camera_processed_path = os.path.join(self.base_processed_path, camera)

            # 确保处理目录存在
            os.makedirs(camera_processed_path, exist_ok=True)

            # 获取该相机的ExPixelCoord对象
            ex_pixel_coord_obj = self.ex_pixel_coord_objects.get(camera)

            # 为每个相机创建观察者
            event_handler = CameraHandler(camera_upload_path, camera_processed_path, ex_pixel_coord_obj)
            observer = Observer()
            observer.schedule(event_handler, camera_upload_path, recursive=False)
            observer.start()
            self.observers.append(observer)
            print(f"开始监控相机: {camera}")

    def stop_monitoring(self):
        """停止所有监控"""
        for observer in self.observers:
            observer.stop()
        for observer in self.observers:
            observer.join()


class CameraHandler(FileSystemEventHandler):
    def __init__(self, camera_upload_path, camera_processed_path, ex_pixel_coord_obj):
        super().__init__()
        self.camera_upload_path = camera_upload_path
        self.camera_processed_path = camera_processed_path
        self.ex_pixel_coord_obj = ex_pixel_coord_obj
        self.current_time_folder = None
        self.time_folder_observer = None

        # 初始化时找到最新的时间文件夹
        self.update_current_time_folder()

    def update_current_time_folder(self):
        """更新当前监控的最新时间文件夹"""
        time_folders = [f for f in os.listdir(self.camera_upload_path)
                        if f.startswith('TLS_') and os.path.isdir(os.path.join(self.camera_upload_path, f))]

        if not time_folders:
            return

        def extract_number(folder_name):
            # 假设格式为 TLS_0206-xxxx，提取0206这部分
            if len(folder_name) >= 8 and folder_name.startswith('TLS_'):
                number_str = folder_name[4:8]  # 提取第5-8个字符
                try:
                    return int(number_str)
                except ValueError:
                    return 0
            return 0

        # 找到数字最大的文件夹（最新的）
        latest_folder = max(time_folders, key=extract_number)
        new_time_folder = os.path.join(self.camera_upload_path, latest_folder)

        # 如果时间文件夹发生变化，更新监控
        if new_time_folder != self.current_time_folder:
            # 停止旧的观察者
            if self.time_folder_observer:
                self.time_folder_observer.stop()
                self.time_folder_observer.join()

            self.current_time_folder = new_time_folder
            print(f"更新监控文件夹: {latest_folder}")

            # 开始监控新的时间文件夹
            self.time_folder_observer = Observer()
            time_folder_handler = TimeFolderHandler(
                self.current_time_folder,
                self.camera_processed_path,
                self.ex_pixel_coord_obj
            )
            self.time_folder_observer.schedule(
                time_folder_handler,
                self.current_time_folder,
                recursive=False
            )
            self.time_folder_observer.start()

    def on_created(self, event):
        """处理新创建的时间文件夹"""
        if event.is_directory and event.src_path.startswith(os.path.join(self.camera_upload_path, 'TLS_')):
            print(f"检测到新时间文件夹: {os.path.basename(event.src_path)}")
            self.update_current_time_folder()

    def on_deleted(self, event):
        """处理删除的时间文件夹"""
        if event.is_directory and event.src_path == self.current_time_folder:
            print(f"当前监控的时间文件夹被删除: {os.path.basename(event.src_path)}")
            self.update_current_time_folder()


class TimeFolderHandler(FileSystemEventHandler):
    def __init__(self, time_folder_path, camera_processed_path:str,ex_pixel_coord_obj):
        super().__init__()
        self.time_folder_path = time_folder_path
        self.camera_processed_path = camera_processed_path
        self.ex_pixel_coord_obj = ex_pixel_coord_obj
        self.time_stamp = None
        self.processed_files = set()
        self.processed_dir_created = False
        self.pixel_dir=None
        self.img_dir = None
        self.ocr_coord=(182, 1893, 810, 1962)
        self.processing_lock = threading.Lock()

    def get_time_stamp_from_image(self, image_path):
        """从0001图片中提取时间戳"""
        try:
            # 调用您提供的方法
            return ocr_Ex_time(image_path,self.ocr_coord)
        except Exception as e:
            print(f"提取时间戳失败: {str(e)}")
            return None

    def create_processed_directory(self, time_stamp):
        """创建处理结果目录结构"""
        processed_dir = os.path.join(self.camera_processed_path, time_stamp)
        pixel_dir = os.path.join(processed_dir, 'pixel')
        img_dir = os.path.join(processed_dir, 'img')  # 新增img目录

        os.makedirs(pixel_dir, exist_ok=True)
        os.makedirs(img_dir, exist_ok=True)  # 创建img目录
        self.processed_dir_created = True
        return pixel_dir, img_dir  # 返回两个目录路径

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            filename = os.path.basename(event.src_path)

            # 使用线程锁确保每个文件的处理是串行的
            with self.processing_lock:
                # 检查是否为0001图片
                if filename.endswith('_0001.jpg') or filename.endswith('_0001.png'):
                    print(f"检测到0001图片: {filename}")
                    time.sleep(2)  # 等待文件完全写入

                    # 提取时间戳
                    self.time_stamp = self.get_time_stamp_from_image(event.src_path)
                    if self.time_stamp:
                        print(f"提取到时间戳: {self.time_stamp}")
                        self.create_processed_directory(self.time_stamp)

                # 处理所有图片文件（包括0001图片）
                if filename not in self.processed_files:
                    time.sleep(2)
                    self.processed_files.add(filename)
                    self.process_image(event.src_path, filename)

    def process_image(self, src_path, filename):
        """处理单个图片的独立方法"""
        print(f"处理图片: {src_path}")

        # 如果时间戳不存在，尝试从0001图片重新提取
        if not self.time_stamp:
            time_stamp = self.get_time_stamp_from_0001_image()
            if time_stamp:
                self.time_stamp = time_stamp
                self.create_processed_directory(self.time_stamp)
            else:
                print(f"警告: 尚未提取到时间戳，跳过处理 {filename}")
                return

        try:
            # 处理图像逻辑
            pixelpoints = self.ex_pixel_coord_obj.mark_pixel_coords_ex(src_path)

            if pixelpoints is None:
                print(f"警告: 无法提取像素坐标，跳过处理 {filename}")
                return

            if not self.processed_dir_created and self.time_stamp:
                self.pixel_dir, self.img_dir = self.create_processed_directory(self.time_stamp)
            elif self.time_stamp:
                self.pixel_dir = os.path.join(self.camera_processed_path, self.time_stamp, 'pixel')
                self.img_dir = os.path.join(self.camera_processed_path, self.time_stamp, 'img')

            # 保存结果
            base_name = os.path.splitext(filename)[0]
            pixel_result_path = os.path.join(self.pixel_dir, f"{base_name}.txt")

            # 将pixelpoints转换为排序后的列表
            sorted_points = pixelpoints.tolist() if hasattr(pixelpoints, 'tolist') else list(pixelpoints)
            with open(pixel_result_path, 'w') as f:
                for idx, (x, y) in enumerate(sorted_points, 1):
                    f.write(f"{idx} {x} {y}\n")

            # 备份和删除
            img_backup_path = os.path.join(self.img_dir, filename)
            # shutil.copy2(src_path, img_backup_path)
            img = cv2.imread(src_path)
            # 绘制编号和坐标点
            img_draw = img.copy()
            for idx, (x, y) in enumerate(sorted_points, 1):
                cv2.circle(img_draw, (int(x), int(y)), 2, (0, 255, 0), -1)
                cv2.putText(img_draw, str(idx), (int(x + 10), int(y - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 2)
            cv2.imwrite(img_backup_path, img_draw)
            del img_draw
            del img

            os.remove(src_path)

        except Exception as e:
            print(f"处理图片 {filename} 时出错: {str(e)}")

    def get_time_stamp_from_0001_image(self):
        """尝试从现有的0001图片重新提取时间戳"""
        for f in os.listdir(self.time_folder_path):
            if f.endswith(('_0001.jpg', '_0001.png')):
                filepath = os.path.join(self.time_folder_path, f)
                return self.get_time_stamp_from_image(filepath)
        return None


# 使用示例
if __name__ == "__main__":
    base_upload_path = r"G:\Outdoor_RTCamProc\RT_text\atli_uploads"
    base_processed_path = r"G:\Outdoor_RTCamProc\RT_text\atli_processed"
    camera_configs = {
        'camera1': {
            'polygon_pts': np.array([(1099, 1608), (1101, 825), (2925, 835), (2925, 1667)], dtype=np.int32),
            'pre_points': None  # 初始化为None
        },
        'camera2': {
            'polygon_pts': np.array([(1099, 1608), (1101, 825), (2925, 835), (2925, 1667)], dtype=np.int32),
            'pre_points': None
        }
    }

    monitor = CameraMonitor(base_upload_path, base_processed_path,camera_configs=camera_configs)

    try:
        monitor.start_monitoring()
        print("监控已启动...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n停止监控...")
        monitor.stop_monitoring()