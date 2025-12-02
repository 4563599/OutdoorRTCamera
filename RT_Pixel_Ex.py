# 1.确定ATLI相机在服务器上文件保存路径
# 2.在本地模拟往这种结构的文件夹传输图片
# 3.识别到文件夹中出现新图片，开始处理，包括：
#   解析时间戳，提取像素坐标，将像素坐标文件保存到另一文件夹路径（基于输入路径构建）下，最后将图片备份

import os
import time
import sys
import logging
from datetime import datetime

import cv2
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ocr_Ex_time import ocr_Ex_time
import threading
from Ex_Pixel import ExPixelCoord
from config_loader import load_config

def setup_logging(log_file=None):
    """设置日志配置"""
    if not log_file:
        # 根据环境选择日志文件路径
        import platform
        if platform.system().lower() == 'windows':
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"atli_monitor_{timestamp}.log")
        else:
            log_file = "/var/log/atli_monitor/atli_camera_monitor.log"
            # 确保日志目录存在
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )

    logger = logging.getLogger('atli_monitor')
    logger.info(f"日志系统已启动，日志文件: {log_file}")
    return logger

def Ex_pixel(src_path):
    """
    示例函数：根据图片路径返回单个像素点，实际逻辑由 ExPixelCoord 替换。
    """
    return np.array([[120, 280]])

class CameraMonitor:
    """统一管理多台相机的上传目录监控与事件分发。"""
    def __init__(self, base_upload_path, base_processed_path, camera_configs, ocr_coord=None, wait_time=2, draw_params=None, logger=None):
        """
        初始化顶层监控器，负责为每个相机场景创建事件观察者和像素提取器。

        Args:
            base_upload_path: ATLI 上传目录根路径（监听源）。
            base_processed_path: 处理结果根路径（输出像素与备份）。
            camera_configs: 每台相机的 ROI 配置，用于实例化 ExPixelCoord。
            ocr_coord: OCR 时间戳区域坐标 (x1, y1, x2, y2)。
            wait_time: 文件写入等待时间（秒）。
            draw_params: 图片绘制参数字典。
        """
        self.base_upload_path = base_upload_path
        self.base_processed_path = base_processed_path
        self.camera_configs = camera_configs
        self.cameras = list(camera_configs.keys())
        self.observers = []
        self.ocr_coord = ocr_coord
        self.wait_time = wait_time
        self.draw_params = draw_params
        self.logger = logger or logging.getLogger('atli_monitor.camera_monitor')

        self.logger.info(f"初始化相机监控器 - 相机数量: {len(self.cameras)}")
        self.logger.info(f"监控路径: {base_upload_path}")
        self.logger.info(f"处理路径: {base_processed_path}")
        self.logger.info(f"OCR区域: {ocr_coord}")
        self.logger.info(f"等待时间: {wait_time}秒")

        # 为每个相机创建ExPixelCoord对象
        self.ex_pixel_coord_objects = {}
        for camera_name, config in camera_configs.items():
            polygon_pts = config.get('polygon_pts')
            pre_points = config.get('pre_points', None)
            if polygon_pts is not None:
                self.ex_pixel_coord_objects[camera_name] = ExPixelCoord(polygon_pts, pre_points)
                self.logger.info(f"相机 {camera_name} 像素提取器初始化成功")
            else:
                self.logger.warning(f"相机 {camera_name} 缺少 polygon_pts 配置")

    def start_monitoring(self):
        """
        遍历相机列表，为每个上传目录启动 watchdog 观察者并绑定事件处理器。

        同时确保对应的处理输出目录存在，便于后续写入像素与备份文件。
        """
        for camera in self.cameras:
            camera_upload_path = os.path.join(self.base_upload_path, camera)
            camera_processed_path = os.path.join(self.base_processed_path, camera)

            # 确保处理目录存在
            os.makedirs(camera_processed_path, exist_ok=True)

            # 获取该相机的ExPixelCoord对象
            ex_pixel_coord_obj = self.ex_pixel_coord_objects.get(camera)

            # 为每个相机创建观察者
            event_handler = CameraHandler(
                camera_upload_path,
                camera_processed_path,
                ex_pixel_coord_obj,
                ocr_coord=self.ocr_coord,
                wait_time=self.wait_time,
                draw_params=self.draw_params,
                logger=self.logger
            )
            observer = Observer()
            observer.schedule(event_handler, camera_upload_path, recursive=False)
            observer.start()
            self.observers.append(observer)
            self.logger.info(f"开始监控相机: {camera} - 路径: {camera_upload_path}")

    def stop_monitoring(self):
        """
        停止并回收所有活跃观察者，释放底层线程资源。

        用于脚本退出或键盘中断时的善后工作。
        """
        for observer in self.observers:
            observer.stop()
        for observer in self.observers:
            observer.join()


class CameraHandler(FileSystemEventHandler):
    """监听单个相机上传目录并动态切换最新批次。"""
    def __init__(self, camera_upload_path, camera_processed_path, ex_pixel_coord_obj, ocr_coord=None, wait_time=2, draw_params=None, logger=None):
        """
        构建相机级观察者，记录上传/处理路径并保留像素提取对象。
        """
        super().__init__()
        self.camera_upload_path = camera_upload_path
        self.camera_processed_path = camera_processed_path
        self.ex_pixel_coord_obj = ex_pixel_coord_obj
        self.ocr_coord = ocr_coord
        self.wait_time = wait_time
        self.draw_params = draw_params
        self.logger = logger or logging.getLogger('atli_monitor.camera_handler')
        self.current_time_folder = None
        self.time_folder_observer = None

        camera_name = os.path.basename(camera_upload_path)
        self.logger.info(f"初始化相机处理器 - {camera_name}")
        self.logger.info(f"监控路径: {camera_upload_path}")
        self.logger.info(f"输出路径: {camera_processed_path}")

        # 初始化时找到最新的时间文件夹
        self.update_current_time_folder()

    def update_current_time_folder(self):
        """
        扫描相机目录下的 TLS_* 子目录，锁定编号最大的时间文件夹并开始监听。

        如检测到新文件夹，会切换到新的 Observer，避免老目录阻塞资源。
        """
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
            self.logger.info(f"更新监控文件夹: {latest_folder}")

            # 开始监控新的时间文件夹
            self.time_folder_observer = Observer()
            time_folder_handler = TimeFolderHandler(
                self.current_time_folder,
                self.camera_processed_path,
                self.ex_pixel_coord_obj,
                ocr_coord=self.ocr_coord,
                wait_time=self.wait_time,
                draw_params=self.draw_params,
                logger=self.logger
            )
            self.time_folder_observer.schedule(
                time_folder_handler,
                self.current_time_folder,
                recursive=False
            )
            self.time_folder_observer.start()

    def on_created(self, event):
        """
        监听 TLS_* 目录的创建事件并触发监控切换。

        通过 watchdog 的回调接口实时响应生成的新批次目录。
        """
        if event.is_directory and event.src_path.startswith(os.path.join(self.camera_upload_path, 'TLS_')):
            self.logger.info(f"检测到新时间文件夹: {os.path.basename(event.src_path)}")
            self.update_current_time_folder()

    def on_deleted(self, event):
        """
        当当前监控的时间目录被删除时，重新扫描以保证处理不会中断。
        """
        if event.is_directory and event.src_path == self.current_time_folder:
            self.logger.warning(f"当前监控的时间文件夹被删除: {os.path.basename(event.src_path)}")
            self.update_current_time_folder()


class TimeFolderHandler(FileSystemEventHandler):
    """针对特定时间批次的图片事件处理器，负责 OCR 与像素提取。"""
    def __init__(self, time_folder_path, camera_processed_path:str, ex_pixel_coord_obj, ocr_coord=None, wait_time=2, draw_params=None, logger=None):
        """
        缓存批次目录、目标输出目录及 ExPixelCoord，供后续事件调用。
        """
        super().__init__()
        self.time_folder_path = time_folder_path
        self.camera_processed_path = camera_processed_path
        self.ex_pixel_coord_obj = ex_pixel_coord_obj
        self.time_stamp = None
        self.processed_files = set()
        self.processed_dir_created = False
        self.pixel_dir = None
        self.img_dir = None
        self.ocr_coord = ocr_coord if ocr_coord else (182, 1893, 810, 1962)
        self.wait_time = wait_time
        self.draw_params = draw_params if draw_params else {
            'circle_radius': 2,
            'circle_color': [0, 255, 0],
            'font_scale': 3,
            'font_thickness': 2,
            'font_color': [0, 255, 0]
        }
        self.logger = logger or logging.getLogger('atli_monitor.time_folder_handler')
        self.processing_lock = threading.Lock()

        folder_name = os.path.basename(time_folder_path)
        camera_name = os.path.basename(os.path.dirname(time_folder_path))
        self.logger.info(f"初始化时间文件夹处理器 - {camera_name}/{folder_name}")
        self.logger.info(f"监控路径: {time_folder_path}")
        self.logger.info(f"OCR区域: {ocr_coord}")
        self.logger.info(f"等待时间: {wait_time}秒")

    def get_time_stamp_from_image(self, image_path):
        """
        针对 _0001 首帧执行 OCR，成功后缓存批次时间戳。
        """
        try:
            # 调用您提供的方法
            return ocr_Ex_time(image_path,self.ocr_coord)
        except Exception as e:

            return None

    def create_processed_directory(self, time_stamp):
        """
        根据时间戳创建 pixel/img 子目录，并标记目录已准备好。
        """
        processed_dir = os.path.join(self.camera_processed_path, time_stamp)
        pixel_dir = os.path.join(processed_dir, 'pixel')
        img_dir = os.path.join(processed_dir, 'img')  # 新增img目录

        os.makedirs(pixel_dir, exist_ok=True)
        os.makedirs(img_dir, exist_ok=True)  # 创建img目录
        self.processed_dir_created = True
        return pixel_dir, img_dir  # 返回两个目录路径

    def on_created(self, event):
        """
        监听批次内 JPG/PNG 的创建，串行处理文件并触发时间戳抽取。
        """
        if not event.is_directory and event.src_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            filename = os.path.basename(event.src_path)

            # 使用线程锁确保每个文件的处理是串行的
            with self.processing_lock:
                # 检查是否为0001图片
                if filename.endswith('_0001.jpg') or filename.endswith('_0001.png'):
                    self.logger.info(f"检测到0001图片: {filename}")
                    print(f"检测到0001图片: {filename}")

                    self.logger.info(f"等待 {self.wait_time} 秒确保文件完全写入...")
                    time.sleep(self.wait_time)  # 等待文件完全写入

                    # 提取时间戳
                    self.logger.info(f"开始从图片提取时间戳: {filename}")
                    self.time_stamp = self.get_time_stamp_from_image(event.src_path)
                    if self.time_stamp:
                        self.logger.info(f"成功提取时间戳: {self.time_stamp}")
                        print(f"提取到时间戳: {self.time_stamp}")
                        self.create_processed_directory(self.time_stamp)
                    else:
                        self.logger.warning(f"时间戳提取失败: {filename}")

                # 处理所有图片文件（包括0001图片）
                if filename not in self.processed_files:
                    self.logger.info(f"新图片待处理: {filename}")
                    time.sleep(self.wait_time)
                    self.processed_files.add(filename)
                    self.process_image(event.src_path, filename)
                else:
                    self.logger.debug(f"图片已处理，跳过: {filename}")

    def process_image(self, src_path, filename):
        """
        对新图片执行业务流程：提取像素->落盘->备份绘制->删除源文件。
        """
        self.logger.info(f"开始处理图片: {filename}")
        print(f"处理图片: {src_path}")

        # 记录文件信息
        try:
            file_size = os.path.getsize(src_path)
            self.logger.info(f"图片文件信息 - 大小: {file_size} bytes")
        except Exception as e:
            self.logger.warning(f"无法获取文件信息: {e}")

        # 如果时间戳不存在，尝试从0001图片重新提取
        if not self.time_stamp:
            self.logger.warning("时间戳未设置，尝试重新提取...")
            time_stamp = self.get_time_stamp_from_0001_image()
            if time_stamp:
                self.time_stamp = time_stamp
                self.create_processed_directory(self.time_stamp)
                self.logger.info(f"重新提取时间戳成功: {self.time_stamp}")
            else:
                self.logger.error("重新提取时间戳失败")
                self.logger.warning(f"尚未提取到时间戳，跳过处理: {filename}")
                print(f"警告: 尚未提取到时间戳，跳过处理 {filename}")
                return

        try:
            # 开始像素坐标提取
            self.logger.info(f"开始提取像素坐标: {filename}")
            start_time = time.time()
            pixelpoints = self.ex_pixel_coord_obj.mark_pixel_coords_ex(src_path)
            extract_time = time.time() - start_time

            if pixelpoints is None:
                self.logger.warning(f"像素坐标提取失败: {filename}")
                print(f"警告: 无法提取像素坐标，跳过处理 {filename}")
                return

            self.logger.info(f"像素坐标提取成功 - 点数: {len(pixelpoints)}, 耗时: {extract_time:.3f}秒")

            if not self.processed_dir_created and self.time_stamp:
                self.pixel_dir, self.img_dir = self.create_processed_directory(self.time_stamp)
            elif self.time_stamp:
                self.pixel_dir = os.path.join(self.camera_processed_path, self.time_stamp, 'pixel')
                self.img_dir = os.path.join(self.camera_processed_path, self.time_stamp, 'img')

            # 保存像素坐标结果
            base_name = os.path.splitext(filename)[0]
            pixel_result_path = os.path.join(self.pixel_dir, f"{base_name}.txt")

            # 将pixelpoints转换为排序后的列表
            sorted_points = pixelpoints.tolist() if hasattr(pixelpoints, 'tolist') else list(pixelpoints)
            self.logger.info(f"保存像素坐标文件: {pixel_result_path} - {len(sorted_points)}个点")

            start_time = time.time()
            with open(pixel_result_path, 'w') as f:
                for idx, (x, y) in enumerate(sorted_points, 1):
                    f.write(f"{idx} {x} {y}\n")
            save_time = time.time() - start_time
            self.logger.info(f"像素坐标文件保存完成，耗时: {save_time:.3f}秒")

            # 备份图片并绘制坐标点
            img_backup_path = os.path.join(self.img_dir, filename)
            self.logger.info(f"开始生成标注图片: {img_backup_path}")

            start_time = time.time()
            img = cv2.imread(src_path)
            if img is None:
                self.logger.error(f"无法读取源图片进行标注: {src_path}")
                raise Exception("图片读取失败")

            # 绘制编号和坐标点
            img_draw = img.copy()
            circle_radius = self.draw_params.get('circle_radius', 2)
            circle_color = self.draw_params.get('circle_color', [0, 255, 0])
            font_scale = self.draw_params.get('font_scale', 3)
            font_thickness = self.draw_params.get('font_thickness', 2)
            font_color = self.draw_params.get('font_color', [0, 255, 0])

            for idx, (x, y) in enumerate(sorted_points, 1):
                cv2.circle(img_draw, (int(x), int(y)), circle_radius, circle_color, -1)
                cv2.putText(img_draw, str(idx), (int(x + 10), int(y - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_color, font_thickness)

            cv2.imwrite(img_backup_path, img_draw)
            draw_time = time.time() - start_time
            self.logger.info(f"标注图片生成完成，耗时: {draw_time:.3f}秒")

            del img_draw
            del img

            # 删除原始图片
            original_size = os.path.getsize(src_path)
            os.remove(src_path)
            self.logger.info(f"原始图片已删除: {src_path} ({original_size} bytes)")
            self.logger.info(f"图片处理完成: {filename} -> 坐标文件: {base_name}.txt, 标注图片: {filename}")
            # TODO: 为 os.remove 增加异常回退，比如移动到 quarantine 目录。

        except Exception as e:
            self.logger.error(f"处理图片异常: {filename} - 错误: {str(e)}")
            print(f"处理图片 {filename} 时出错: {str(e)}")

            # 记录异常详情
            import traceback
            self.logger.error(f"异常堆栈: {traceback.format_exc()}")

    def get_time_stamp_from_0001_image(self):
        """
        搜索当前批次下的 0001 图片并再次尝试 OCR，避免时间戳缺失。
        """
        for f in os.listdir(self.time_folder_path):
            if f.endswith(('_0001.jpg', '_0001.png')):
                filepath = os.path.join(self.time_folder_path, f)
                return self.get_time_stamp_from_image(filepath)
        return None


# 使用示例
if __name__ == "__main__":
    # 从配置文件加载配置
    try:
        # 初始化日志系统
        logger = setup_logging()
        logger.info("=== ATLI 相机监控系统启动 ===")

        print("=== ATLI 相机监控系统启动 ===")

        config = load_config('config.yaml')

        # 从配置获取路径
        base_upload_path = config.get_base_upload_path()
        base_processed_path = config.get_base_processed_path()
        tesseract_cmd = config.get_tesseract_cmd()

        # 从配置获取相机配置
        camera_configs = config.get_camera_configs()

        # 从配置获取 OCR 区域
        ocr_coord = config.get_ocr_region()

        # 从配置获取处理参数
        wait_time = config.get_file_wait_time()
        draw_params = config.get_draw_params()

        # 确保必要的目录存在
        config.ensure_directories()

        # 控制台显示关键信息
        print(f"运行环境: {config.env}")
        print(f"监控目录: {base_upload_path}")
        print(f"相机数量: {len(camera_configs)} ({', '.join(camera_configs.keys())})")
        print("="*50)

        # 记录到日志
        logger.info("=" * 40)
        logger.info("系统配置信息")
        logger.info(f"运行环境: {config.env}")
        logger.info(f"监控上传目录: {base_upload_path}")
        logger.info(f"输出处理目录: {base_processed_path}")
        logger.info(f"Tesseract路径: {tesseract_cmd}")
        logger.info(f"OCR区域: {ocr_coord}")
        logger.info(f"等待时间: {wait_time}秒")
        logger.info(f"相机数量: {len(camera_configs)}")
        for camera_name in camera_configs.keys():
            logger.info(f"  - {camera_name}")
        logger.info("=" * 40)

        monitor = CameraMonitor(
            base_upload_path,
            base_processed_path,
            camera_configs=camera_configs,
            ocr_coord=ocr_coord,
            wait_time=wait_time,
            draw_params=draw_params,
            logger=logger
        )

        logger.info("开始启动监控服务...")
        monitor.start_monitoring()
        logger.info("所有相机监控已启动成功")
        print("✅ 监控系统已启动，按 Ctrl+C 停止...")

        # 主循环
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("接收到停止信号...")
            raise

    except FileNotFoundError as e:
        error_msg = f"配置文件不存在: {e}"
        if 'logger' in locals():
            logger.error(error_msg)
        print(f"❌ 错误: {error_msg}")
        print("请确保 config.yaml 文件存在于当前目录")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n停止监控...")
        if 'logger' in locals():
            logger.info("用户手动停止监控")
        if 'monitor' in locals():
            monitor.stop_monitoring()
            logger.info("监控服务已停止")
        print("监控已停止")
    except Exception as e:
        error_msg = f"系统运行异常: {str(e)}"
        if 'logger' in locals():
            logger.error(error_msg)
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
        print(f"❌ 系统异常: {error_msg}")
        print("详细错误信息已记录到日志文件")
        sys.exit(1)
