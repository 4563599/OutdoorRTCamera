"""
配置文件加载模块
支持从 YAML 文件加载系统配置，并提供默认值
"""

import yaml
import os
import platform
import numpy as np


class ConfigLoader:
    """配置加载器，负责读取和解析 YAML 配置文件"""

    def __init__(self, config_path='config.yaml', env=None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径，默认为当前目录下的 config.yaml
            env: 强制指定环境类型 ('windows' 或 'linux')，None时自动检测
        """
        self.config_path = config_path
        self.env = env or self._detect_environment()
        self.config = self._load_config()

        # 可以通过日志级别控制这些信息的显示
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"检测到运行环境: {self.env}")
        if 'environments' in self.config and self.env in self.config['environments']:
            logger.info(f"使用 {self.env} 环境配置")

    def _detect_environment(self):
        """自动检测运行环境"""
        system = platform.system().lower()
        if system == 'windows':
            return 'windows'
        elif system in ['linux', 'darwin']:  # darwin是macOS，但这里归类为linux配置
            return 'linux'
        else:
            import logging
            logging.getLogger(__name__).warning(f"未知操作系统: {system}，使用默认配置")
            return 'linux'  # 默认使用linux配置

    def _load_config(self):
        """从 YAML 文件加载配置"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            raise Exception(f"加载配置文件失败: {e}")

    def _get_env_config(self, key, default_value=None):
        """
        根据当前环境获取配置值

        Args:
            key: 配置键，支持嵌套，如 'paths.base_upload_path'
            default_value: 默认值

        Returns:
            配置值或默认值
        """
        # 首先尝试从环境特定配置获取
        if 'environments' in self.config and self.env in self.config['environments']:
            env_config = self.config['environments'][self.env]
            keys = key.split('.')
            current = env_config

            try:
                for k in keys:
                    current = current[k]
                return current
            except (KeyError, TypeError):
                pass

        # 如果环境特定配置不存在，使用默认配置
        keys = key.split('.')
        current = self.config

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default_value

    def get_base_upload_path(self):
        """获取上传目录根路径"""
        return self._get_env_config('paths.base_upload_path')

    def get_base_processed_path(self):
        """获取处理结果根路径"""
        return self._get_env_config('paths.base_processed_path')

    # 修改，增加静态方法
    @staticmethod
    def load_init_points(init_path):
        """从init.txt加载初始点坐标"""
        points = []
        with open(init_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    x, y = float(parts[1]), float(parts[2])
                    points.append([x, y])
        return np.array(points, dtype=np.float32)

    def get_camera_configs(self):
        """
        获取所有相机的配置信息

        Returns:
            dict: 相机配置字典，格式为 {camera_name: config}
        """
        cameras = self.config['cameras']
        camera_configs = {}

        for camera_name, camera_info in cameras.items():
            if not camera_info.get('enabled', True):
                continue

            # 修改，增加初始像素点坐标
            polygon_pts = np.array(camera_info['polygon_pts'], dtype=np.int32)
            init_points_path= camera_info['init_points_path']
            camera_configs[camera_name] = {
                'polygon_pts': polygon_pts,
                'pre_points': ConfigLoader.load_init_points(init_points_path)
            }

        return camera_configs

    def get_file_wait_time(self):
        """获取文件写入等待时间"""
        return self.config['processing'].get('file_wait_time', 2)

    def get_log_config(self):
        """
        获取日志配置

        Returns:
            dict: 日志配置字典
        """
        return self.config.get('logging', {
            'level': 'INFO',
            'log_file': '/var/log/atli_camera_monitor.log',
            'console_output': True
        })

    def ensure_directories(self):
        """确保所有必要的目录存在"""
        base_upload = self.get_base_upload_path()
        base_processed = self.get_base_processed_path()

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"当前环境: {self.env}")
        logger.info(f"上传目录: {base_upload}")
        logger.info(f"处理目录: {base_processed}")

        # 创建上传目录
        for camera_name in self.config['cameras'].keys():
            if self.config['cameras'][camera_name].get('enabled', True):
                upload_dir = os.path.join(base_upload, camera_name)
                try:
                    os.makedirs(upload_dir, exist_ok=True)
                    logger.info(f"确保目录存在: {upload_dir}")
                except Exception as e:
                    logger.error(f"创建目录失败: {upload_dir} - {e}")

        # 创建处理目录
        try:
            os.makedirs(base_processed, exist_ok=True)
            logger.info(f"确保目录存在: {base_processed}")
        except Exception as e:
            logger.error(f"创建目录失败: {base_processed} - {e}")

        # 创建日志目录
        log_config = self.get_log_config()
        log_file = log_config.get('log_file')
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir:
                try:
                    os.makedirs(log_dir, exist_ok=True)
                    logger.info(f"确保日志目录存在: {log_dir}")
                except Exception as e:
                    logger.error(f"创建日志目录失败: {log_dir} - {e}")


def load_config(config_path='config.yaml', env=None):
    """
    便捷函数：加载配置文件

    Args:
        config_path: 配置文件路径
        env: 强制指定环境类型 ('windows' 或 'linux')，None时自动检测

    Returns:
        ConfigLoader: 配置加载器实例
    """
    return ConfigLoader(config_path, env)


if __name__ == "__main__":
    # 测试配置加载
    try:
        config = load_config()
        print("配置加载成功！")
        print(f"上传路径: {config.get_base_upload_path()}")
        print(f"处理路径: {config.get_base_processed_path()}")
        print(f"相机配置: {list(config.get_camera_configs().keys())}")

        # 确保目录存在
        config.ensure_directories()

    except Exception as e:
        print(f"错误: {e}")

