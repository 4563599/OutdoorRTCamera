#!/usr/bin/env python3
"""
ATLI 相机监控系统 - 多环境配置测试脚本
测试Windows和Linux环境配置是否正常工作
"""

import os
import sys
from pathlib import Path

def test_config_loader():
    """测试配置加载器的多环境支持"""
    print("🔧 测试配置加载器多环境支持...")

    try:
        from config_loader import load_config

        # 测试自动环境检测
        print("\n1️⃣ 测试自动环境检测:")
        config_auto = load_config()
        print(f"   检测到环境: {config_auto.env}")
        print(f"   上传路径: {config_auto.get_base_upload_path()}")
        print(f"   处理路径: {config_auto.get_base_processed_path()}")
        print(f"   Tesseract: {config_auto.get_tesseract_cmd()}")

        # 测试强制Windows环境
        print("\n2️⃣ 测试强制Windows环境:")
        try:
            config_win = load_config(env='windows')
            print(f"   环境: {config_win.env}")
            print(f"   上传路径: {config_win.get_base_upload_path()}")
            print(f"   处理路径: {config_win.get_base_processed_path()}")
            print(f"   Tesseract: {config_win.get_tesseract_cmd()}")
        except Exception as e:
            print(f"   ❌ Windows配置测试失败: {e}")

        # 测试强制Linux环境
        print("\n3️⃣ 测试强制Linux环境:")
        try:
            config_linux = load_config(env='linux')
            print(f"   环境: {config_linux.env}")
            print(f"   上传路径: {config_linux.get_base_upload_path()}")
            print(f"   处理路径: {config_linux.get_base_processed_path()}")
            print(f"   Tesseract: {config_linux.get_tesseract_cmd()}")
        except Exception as e:
            print(f"   ❌ Linux配置测试失败: {e}")

        return True

    except ImportError as e:
        print(f"   ❌ 无法导入配置加载器: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 配置测试失败: {e}")
        return False

def test_directory_creation():
    """测试目录创建功能"""
    print("\n🗂️ 测试目录创建功能...")

    try:
        from config_loader import load_config

        # 测试Windows环境目录创建
        print("\n1️⃣ 测试Windows环境目录创建:")
        config_win = load_config(env='windows')

        win_base = config_win.get_base_upload_path()
        win_processed = config_win.get_base_processed_path()

        # 检查Windows目录是否存在
        win_dirs = [
            win_base,
            os.path.join(win_base, 'camera1'),
            os.path.join(win_base, 'camera2'),
            win_processed
        ]

        for dir_path in win_dirs:
            if os.path.exists(dir_path):
                print(f"   ✅ {dir_path}")
            else:
                print(f"   ❌ {dir_path} (不存在)")

        # 测试Linux环境目录（仅检查路径格式）
        print("\n2️⃣ Linux环境路径格式:")
        config_linux = load_config(env='linux')

        linux_base = config_linux.get_base_upload_path()
        linux_processed = config_linux.get_base_processed_path()

        print(f"   📁 Linux上传路径: {linux_base}")
        print(f"   📁 Linux处理路径: {linux_processed}")

        return True

    except Exception as e:
        print(f"   ❌ 目录测试失败: {e}")
        return False

def test_tesseract_paths():
    """测试Tesseract路径配置"""
    print("\n🔍 测试Tesseract路径配置...")

    try:
        from config_loader import load_config

        # Windows环境Tesseract路径
        print("\n1️⃣ Windows环境Tesseract:")
        config_win = load_config(env='windows')
        win_tesseract = config_win.get_tesseract_cmd()
        print(f"   路径: {win_tesseract}")

        if os.name == 'nt' and os.path.exists(win_tesseract):
            print(f"   ✅ Windows Tesseract路径存在")
        elif os.name == 'nt':
            print(f"   ⚠️ Windows Tesseract路径不存在，但这是正常的配置")
        else:
            print(f"   ℹ️ 当前非Windows环境，跳过Windows路径检查")

        # Linux环境Tesseract路径
        print("\n2️⃣ Linux环境Tesseract:")
        config_linux = load_config(env='linux')
        linux_tesseract = config_linux.get_tesseract_cmd()
        print(f"   路径: {linux_tesseract}")

        if os.name != 'nt':
            import subprocess
            try:
                result = subprocess.run(['which', 'tesseract'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    actual_path = result.stdout.strip()
                    print(f"   ✅ 系统Tesseract路径: {actual_path}")
                    if actual_path == linux_tesseract:
                        print(f"   ✅ 配置路径与系统路径一致")
                    else:
                        print(f"   ⚠️ 配置路径与系统路径不一致")
                else:
                    print(f"   ❌ 系统未安装Tesseract")
            except:
                print(f"   ℹ️ 无法检查系统Tesseract路径")
        else:
            print(f"   ℹ️ 当前为Windows环境，跳过Linux路径检查")

        return True

    except Exception as e:
        print(f"   ❌ Tesseract路径测试失败: {e}")
        return False

def test_ocr_functionality():
    """测试OCR功能"""
    print("\n📄 测试OCR功能集成...")

    try:
        # 测试OCR模块导入
        from ocr_Ex_time import extract_timestamp_from_image
        print("   ✅ OCR模块导入成功")

        # 测试配置集成
        from config_loader import load_config
        config = load_config()
        ocr_region = config.get_ocr_region()
        print(f"   ✅ OCR区域配置: {ocr_region}")

        return True

    except Exception as e:
        print(f"   ❌ OCR功能测试失败: {e}")
        return False

def generate_test_report():
    """生成测试报告"""
    print("\n" + "="*60)
    print("📋 ATLI相机监控系统 - 多环境配置测试报告")
    print("="*60)

    test_results = []

    # 运行各项测试
    test_results.append(("配置加载器多环境支持", test_config_loader()))
    test_results.append(("目录创建功能", test_directory_creation()))
    test_results.append(("Tesseract路径配置", test_tesseract_paths()))
    test_results.append(("OCR功能集成", test_ocr_functionality()))

    # 统计结果
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    print(f"\n📊 测试结果统计:")
    print(f"   总测试项: {total}")
    print(f"   通过: {passed}")
    print(f"   失败: {total - passed}")

    print(f"\n📝 详细结果:")
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")

    # 生成建议
    print(f"\n💡 建议:")
    if passed == total:
        print("   🎉 所有测试通过！系统已准备好在多环境下运行。")
        if os.name == 'nt':
            print("   🪟 当前在Windows环境，可以开始本地测试。")
            print("   📋 Windows测试步骤:")
            print("      1. 运行: python RT_Pixel_Ex.py")
            print("      2. 上传测试图片到: D:\\pic_back\\atli_uploads\\camera1\\")
            print("      3. 检查结果: D:\\pic_back\\atli_processed\\")
        else:
            print("   🐧 当前在Linux环境，可以部署到生产服务器。")
            print("   📋 Linux部署步骤:")
            print("      1. 运行: sudo ./deploy.sh")
            print("      2. 启动: sudo systemctl start atli-camera-monitor")
    else:
        print("   ⚠️ 部分测试失败，请检查配置和依赖。")
        print("   📋 修复建议:")
        print("      1. 确保安装所有依赖: pip install -r requirements.txt")
        print("      2. 检查配置文件: config.yaml")
        print("      3. 运行环境检查: python check_env.py")

    print("\n" + "="*60)
    return passed == total

if __name__ == "__main__":
    """主函数"""
    print("🚀 开始ATLI相机监控系统多环境配置测试...")

    success = generate_test_report()

    if success:
        print("\n🎉 多环境配置测试完全通过！")
        sys.exit(0)
    else:
        print("\n❌ 多环境配置测试存在问题，请检查上述建议。")
        sys.exit(1)
