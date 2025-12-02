import pytesseract
import cv2
import re
from datetime import datetime
import numpy as np

# 设置Tesseract路径
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract-OCR\tesseract.exe'


def extract_timestamp_from_image(image_path, coord):
    """
    从图片的指定区域提取时间戳

    参数:
    image_path: 图片路径
    coord: 时间戳区域的坐标 (x1, y1, x2, y2)

    返回:
    识别到的时间戳字符串或None(识别失败时)
    """
    try:
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            print(f"无法读取图片: {image_path}")
            return None

        # 裁剪时间戳区域
        x1, y1, x2, y2 = coord
        timestamp_region = img[y1:y2, x1:x2]

        if timestamp_region.size == 0:
            print("裁剪区域为空，请检查坐标参数")
            return None

        # 图像预处理
        processed_img = preprocess_image(timestamp_region)

        # 使用Tesseract进行OCR识别
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789-: tessedit_char_blacklist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        text = pytesseract.image_to_string(processed_img, config=custom_config)

        return text.strip() if text.strip() else None

    except Exception as e:
        print(f"提取时间戳时发生错误: {e}")
        return None


def preprocess_image(img):
    """
    优化的图像预处理函数
    专门针对白色时间戳，基于HSV颜色空间提取白色，结合形态学操作和图片放大
    """
    # 转换为HSV颜色空间，便于提取白色
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 定义白色的HSV范围（白色在HSV中表现为低饱和度，高亮度）
    # 宽范围提取白色和近白色文字
    lower_white = np.array([0, 0, 180])  # 低饱和度，高亮度
    upper_white = np.array([180, 40, 255])  # 略放宽饱和度上限

    # 创建掩码，提取白色区域
    white_mask = cv2.inRange(hsv, lower_white, upper_white)

    # 形态学操作：先闭运算连接断开的字符，后开运算去除小噪点
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)  # 连接断开部分
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)  # 去除小噪点

    # 检查白色像素比例，如果白色像素太少，回退到常规二值化
    white_pixel_ratio = np.sum(white_mask > 0) / white_mask.size
    if white_pixel_ratio < 0.005:  # 如果白色像素占比不足0.5%
        # 回退到常规灰度二值化
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, white_mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 将白色区域设置为前景（黑色背景上的白色文字更适合Tesseract）
    processed = cv2.bitwise_not(white_mask)

    # 放大图片，提高Tesseract识别精度（放大2倍）
    height, width = processed.shape
    new_size = (width * 2, height * 2)
    processed = cv2.resize(processed, new_size, interpolation=cv2.INTER_CUBIC)

    # 轻微高斯模糊，平滑边缘
    processed = cv2.GaussianBlur(processed, (1, 1), 0)

    return processed


def format_timestamp(timestamp_str):
    """
    格式化时间戳字符串为标准的 datetime 对象

    参数:
    timestamp_str: 从图片中提取的时间戳字符串

    返回:
    datetime 对象或 None (如果解析失败)
    """
    if not timestamp_str:
        print("时间戳字符串为空")
        return None

    # 清理字符串：只保留数字
    clean_str = re.sub(r'[^\d]', '', timestamp_str)

    # 验证基本格式
    if not clean_str.startswith('2025'):
        print(f"无法解析时间戳: {timestamp_str} (格式不符合要求，期望: 14位数字且以2025开头)")
        return None

    try:
        # 直接使用datetime验证日期时间有效性
        datetime.strptime(clean_str[:14], '%Y%m%d%H%M%S')
        return clean_str[:14]

    except ValueError as e:
        print(f"无法解析时间戳: {timestamp_str} (日期时间无效: {e})")
        return None


# 使用示例
def ocr_Ex_time(image_path, coord):
    """完整的时间戳处理流程"""
    # 提取时间戳
    timestamp_str = extract_timestamp_from_image(image_path, coord)
    if not timestamp_str:
        print("未能从图片中提取时间戳")
        return None

    print(f"提取到的时间戳字符串: {timestamp_str}")

    # 格式化时间戳
    timestamp_dt = format_timestamp(timestamp_str)
    if timestamp_dt:
        print(f"格式化后的时间戳: {timestamp_dt}")
        return timestamp_dt
    else:
        print("时间戳格式化失败")
        return None

if __name__ == "__main__":
    image_path=r'ocr_text_img/TLS_0203_0001.jpg'
    coord=(182, 1893, 810, 1962)
    timestamp=ocr_Ex_time(image_path, coord)
    print(timestamp)