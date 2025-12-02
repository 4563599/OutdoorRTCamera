import pytesseract
import cv2
import re
from datetime import datetime
import numpy as np
import os

# 设置Tesseract路径 - 优先从环境变量读取，否则使用默认值
def _get_tesseract_cmd():
    """获取 Tesseract 可执行文件路径"""
    # 优先使用环境变量
    env_path = os.environ.get('TESSERACT_CMD')
    if env_path and os.path.exists(env_path):
        return env_path

    # 尝试从配置文件加载
    try:
        from config_loader import load_config
        config = load_config('config.yaml')
        return config.get_tesseract_cmd()
    except:
        pass

    # 根据操作系统返回默认路径
    if os.name == 'nt':  # Windows
        default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    else:  # Linux/Unix
        default_path = '/usr/bin/tesseract'

    return default_path

pytesseract.pytesseract.tesseract_cmd = _get_tesseract_cmd()


def extract_timestamp_from_image(image_path, coord):
    """
    读取整张图片、裁剪目标区域、执行 OCR 并返回原始时间戳字符串。

    coord 为 (x1, y1, x2, y2) 像素坐标；函数内部会调用 preprocess_image 提升 OCR 成功率。
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"无法读取图片: {image_path}")
            return None

        x1, y1, x2, y2 = coord
        timestamp_region = img[y1:y2, x1:x2]

        if timestamp_region.size == 0:
            print("裁剪区域为空，请检查坐标参数")
            return None

        processed_img = preprocess_image(timestamp_region)

        custom_config = (
            r'--oem 3 --psm 7 -c '
            r'tessedit_char_whitelist=0123456789-: '
            r'tessedit_char_blacklist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        )
        text = pytesseract.image_to_string(processed_img, config=custom_config)

        return text.strip() if text.strip() else None

    except Exception as e:
        print(f"提取时间戳时发生错误: {e}")
        return None


def preprocess_image(img):
    """
    针对白色时间戳的特点，执行 HSV 颜色提取、形态学去噪和缩放增强。

    视白色像素占比自动回退到 OTSU 二值化，保证在光照变化下也能给 OCR 稳定的输入。
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower_white = np.array([0, 0, 180])
    upper_white = np.array([180, 40, 255])

    white_mask = cv2.inRange(hsv, lower_white, upper_white)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)

    white_pixel_ratio = np.sum(white_mask > 0) / white_mask.size
    if white_pixel_ratio < 0.005:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, white_mask = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

    processed = cv2.bitwise_not(white_mask)

    height, width = processed.shape
    new_size = (width * 2, height * 2)
    processed = cv2.resize(processed, new_size, interpolation=cv2.INTER_CUBIC)

    processed = cv2.GaussianBlur(processed, (1, 1), 0)

    return processed


def format_timestamp(timestamp_str):
    """
    清理 OCR 输出并验证格式，返回 14 位时间戳（YYYYMMDDhhmmss）。

    主要步骤：剔除非数字字符、校验是否以 2025 开头、使用 datetime 验证合法性。
    """
    if not timestamp_str:
        print("时间戳字符串为空")
        return None

    clean_str = re.sub(r'[^\d]', '', timestamp_str)

    if not clean_str.startswith('2025'):
        print(f"无法解析时间：{timestamp_str} (期望以 2025 开头且为 14 位数字)")
        return None

    try:
        datetime.strptime(clean_str[:14], '%Y%m%d%H%M%S')
        return clean_str[:14]

    except ValueError as e:
        print(f"无法解析时间：{timestamp_str} (日期时间无效: {e})")
        return None


def ocr_Ex_time(image_path, coord):
    """
    端到端执行时间戳提取流程，成功则返回格式化后的 14 位字符串。

    包含三个阶段：裁剪+OCR、格式校验、输出；并打印中间结果辅助排查。
    """
    timestamp_str = extract_timestamp_from_image(image_path, coord)
    if not timestamp_str:
        print("未能从图片中提取时间")
        return None

    print(f"提取到的时间戳字符串: {timestamp_str}")

    timestamp_dt = format_timestamp(timestamp_str)
    if timestamp_dt:
        print(f"格式化后的时间戳: {timestamp_dt}")
        return timestamp_dt

    print("时间戳格式化失败")
    return None


if __name__ == "__main__":
    image_path = r'D:\code\camera\ocr_text_img\TLS_0202_0001.jpg'
    coord = (182, 1893, 810, 1962)
    timestamp = ocr_Ex_time(image_path, coord)
    print(timestamp)
