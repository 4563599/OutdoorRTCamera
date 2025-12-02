#!/usr/bin/env python3
"""
ATLI 相机监控系统环境检查脚本
检查系统环境是否满足部署要求
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

class EnvironmentChecker:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0

    def check(self, name, func, required=True):
        """执行检查并记录结果"""
        try:
            result = func()
            if result:
                print(f"✅ {name}: 通过")
                self.passed += 1
                return True
            else:
                if required:
                    print(f"❌ {name}: 失败 (必需)")
                    self.failed += 1
                else:
                    print(f"⚠️  {name}: 失败 (可选)")
                return False
        except Exception as e:
            if required:
                print(f"❌ {name}: 错误 - {str(e)} (必需)")
                self.failed += 1
            else:
                print(f"⚠️  {name}: 错误 - {str(e)} (可选)")
            return False

    def check_python_version(self):
        """检查 Python 版本"""
        major, minor = sys.version_info[:2]
        if major == 3 and minor >= 8:
            print(f"   Python 版本: {major}.{minor}")
            return True
        return False

    def check_tesseract(self):
        """检查 Tesseract 安装"""
        try:
            result = subprocess.run(['tesseract', '--version'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                print(f"   {version}")
                return True
        except FileNotFoundError:
            pass
        return False

    def check_required_packages(self):
        """检查必需的 Python 包"""
        packages = [
            'cv2', 'numpy', 'scipy', 'watchdog',
            'matplotlib', 'openpyxl', 'pytesseract', 'yaml'
        ]

        missing = []
        for package in packages:
            try:
                if package == 'cv2':
                    import cv2
                elif package == 'yaml':
                    import yaml
                else:
                    importlib.import_module(package)
                print(f"   ✅ {package}")
            except ImportError:
                print(f"   ❌ {package}")
                missing.append(package)

        return len(missing) == 0

    def check_directories(self):
        """检查必需的目录"""
        try:
            from config_loader import load_config
            config = load_config('config.yaml')

            base_upload = config.get_base_upload_path()
            base_processed = config.get_base_processed_path()

            dirs = [
                base_upload,
                os.path.join(base_upload, 'camera1'),
                os.path.join(base_upload, 'camera2'),
                base_processed
            ]

            all_ok = True
            for dir_path in dirs:
                if os.path.exists(dir_path) and os.access(dir_path, os.W_OK):
                    print(f"   ✅ {dir_path}")
                else:
                    print(f"   ❌ {dir_path} (不存在或无写权限)")
                    all_ok = False

            return all_ok

        except Exception as e:
            print(f"   ❌ 无法检查目录: {e}")
            return False

    def check_config_file(self):
        """检查配置文件"""
        config_path = 'config.yaml'
        if os.path.exists(config_path):
            try:
                from config_loader import load_config
                config = load_config(config_path)
                print(f"   ✅ 配置文件格式正确")
                print(f"   🖥️  运行环境: {config.env}")
                print(f"   📁 上传路径: {config.get_base_upload_path()}")
                print(f"   📁 处理路径: {config.get_base_processed_path()}")
                print(f"   🔧 Tesseract路径: {config.get_tesseract_cmd()}")

                # 检查多环境配置
                if 'environments' in config.config:
                    envs = list(config.config['environments'].keys())
                    print(f"   🌍 支持环境: {', '.join(envs)}")

                return True
            except Exception as e:
                print(f"   ❌ 配置文件格式错误: {e}")
                return False
        else:
            print(f"   ❌ 配置文件不存在: {config_path}")
            return False

    def check_system_resources(self):
        """检查系统资源"""
        # 检查可用内存
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()

            for line in meminfo.split('\n'):
                if 'MemAvailable:' in line:
                    available_kb = int(line.split()[1])
                    available_gb = available_kb / 1024 / 1024
                    print(f"   💾 可用内存: {available_gb:.2f} GB")
                    return available_gb >= 2.0  # 至少需要 2GB

            return False
        except:
            return True  # 如果无法检查，假设通过

    def check_disk_space(self):
        """检查磁盘空间"""
        try:
            stat = os.statvfs('/var/ftp')
            available_bytes = stat.f_bavail * stat.f_frsize
            available_gb = available_bytes / (1024 ** 3)
            print(f"   💿 可用磁盘空间: {available_gb:.2f} GB")
            return available_gb >= 10.0  # 至少需要 10GB
        except:
            return True  # 如果无法检查，假设通过

    def check_permissions(self):
        """检查文件权限"""
        current_user = os.getenv('USER', 'unknown')
        print(f"   👤 当前用户: {current_user}")

        # 检查是否可以创建测试文件
        test_dirs = ['/tmp', '/var/ftp']
        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                test_file = os.path.join(test_dir, 'atli_test_file')
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    print(f"   ✅ {test_dir} 写权限正常")
                except:
                    print(f"   ❌ {test_dir} 无写权限")
                    return False

        return True

    def run_all_checks(self):
        """运行所有检查"""
        print("🔍 ATLI 相机监控系统环境检查")
        print("=" * 50)

        # 必需检查
        self.check("Python 版本 (>= 3.8)", self.check_python_version, True)
        self.check("Tesseract OCR", self.check_tesseract, True)
        self.check("Python 依赖包", self.check_required_packages, True)
        self.check("配置文件", self.check_config_file, True)
        self.check("目录结构", self.check_directories, True)
        self.check("文件权限", self.check_permissions, True)

        # 可选检查
        self.check("系统内存", self.check_system_resources, False)
        self.check("磁盘空间", self.check_disk_space, False)

        print("=" * 50)
        print(f"检查结果: {self.passed} 通过, {self.failed} 失败")

        if self.failed > 0:
            print("\n❌ 环境检查失败！请修复上述问题后重试。")
            return False
        else:
            print("\n✅ 环境检查通过！系统已准备好部署。")
            return True

def main():
    """主函数"""
    checker = EnvironmentChecker()
    success = checker.run_all_checks()

    if not success:
        print("\n📋 修复建议:")
        print("1. 安装缺失的依赖: pip install -r requirements.txt")
        print("2. 创建必要目录: sudo mkdir -p /var/ftp/atli_uploads/{camera1,camera2}")
        print("3. 设置目录权限: sudo chown -R $USER:$USER /var/ftp/")
        print("4. 安装 Tesseract: sudo yum install tesseract (CentOS) 或 sudo apt install tesseract-ocr (Ubuntu)")
        print("5. 检查配置文件: vim config.yaml")

        sys.exit(1)
    else:
        print("\n🚀 可以开始部署了！")
        sys.exit(0)

if __name__ == "__main__":
    main()
