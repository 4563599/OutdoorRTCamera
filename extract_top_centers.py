import cv2
import numpy as np
from typing import Tuple


def calculate_completeness(contour: np.ndarray) -> float:
    """
    计算轮廓完整性指标

    参数:
    contour: 轮廓点集

    返回:
    completeness: 0-1之间的值，越接近1表示轮廓越完整
    """
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    contour_area = cv2.contourArea(contour)

    return contour_area / hull_area if hull_area > 0 else 0


def is_quadrilateral(contour: np.ndarray, epsilon_factor: float = 0.02) -> bool:
    """
    判断轮廓是否近似为四边形

    参数:
    contour: 轮廓点集
    epsilon_factor: 多边形逼近精度因子
    angle_threshold: 角度容差（度）

    返回:
    True: 是四边形，False: 不是四边形
    """
    if len(contour) < 4:
        return False

    # 多边形逼近
    epsilon = epsilon_factor * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)

    # 检查是否为四边形
    return len(approx) == 4


def quadrilateral_top_center(contour: np.ndarray, epsilon_factor: float = 0.02) -> Tuple[int, int]:
    """
    计算四边形轮廓的顶部中心坐标

    参数:
    contour: 轮廓点集
    epsilon_factor: 多边形逼近精度因子

    返回:
    (x, y): 顶部中心坐标
    """
    # 多边形逼近获取四边形顶点
    epsilon = epsilon_factor * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)

    # 获取四个顶点
    points = approx.reshape(4, 2)

    # 找到顶部边（y坐标最小的两个点构成的边）
    # 按y坐标排序，取前两个点
    sorted_points = points[np.argsort(points[:, 1])]
    top_points = sorted_points[:2]

    # 计算顶部边中点
    x_center = int(np.mean(top_points[:, 0]))
    y_center = int(np.min(top_points[:, 1]))  # 使用最小y坐标作为顶部高度

    return x_center, y_center

def simple_top_center(contour: np.ndarray, top_percentage: float = 0.2) -> Tuple[int, int]:
    """
    简单方法：使用轮廓点中y最小的指定百分比点的x坐标中位数作为顶部中心

    参数:
    contour: 轮廓点集
    top_percentage: 顶部点的百分比（0-1）

    返回:
    (x, y): 顶部中心坐标
    """
    # 将轮廓点转换为一维数组
    pts = contour.reshape(-1, 2)

    if len(pts) == 0:
        return 0, 0

    # 计算顶部点的数量
    top_count = max(1, int(len(pts) * top_percentage))

    # 获取顶部点（y坐标最小的点）
    top_indices = np.argsort(pts[:, 1])[:top_count]
    top_points = pts[top_indices]
    print(top_points)

    # 计算顶部中心
    x_center = int(np.mean(top_points[:, 0]))
    y_center = int(np.min(top_points[:, 1]))

    return x_center, y_center


def extract_top_centers(contour: np.ndarray,
                       completeness_threshold: float = 0.85,
                       epsilon_factor: float = 0.02,) -> Tuple[int, int]:
    """
    自适应提取轮廓的顶部中心坐标

    参数:
    contour: 轮廓点集
    completeness_threshold: 轮廓完整性阈值，大于此值认为未被遮挡
    epsilon_factor: 多边形逼近精度因子
    angle_threshold: 角度容差（度）

    返回:
    (x, y): 顶部中心坐标
    """
    # 输入验证
    if contour is None or len(contour) < 3:
        return 0, 0

    # 计算轮廓完整性
    completeness = calculate_completeness(contour)

    # 情况1: 轮廓完整且为四边形
    if completeness >= completeness_threshold:
        if is_quadrilateral(contour, epsilon_factor):
            return quadrilateral_top_center(contour, epsilon_factor)
    return simple_top_center(contour)
