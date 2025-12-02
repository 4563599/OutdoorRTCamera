import cv2
import numpy as np
from typing import Tuple, Optional


def centroid_center(contour: np.ndarray) -> Tuple[int, int]:
    """计算轮廓的质心"""
    M = cv2.moments(contour)
    if M["m00"] != 0:
        return int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])

    # 如果无法计算质心，使用轮廓点的平均值
    pts = contour.reshape(-1, 2)
    return int(pts[:, 0].mean()), int(pts[:, 1].mean())


def min_enclosing_circle_center(contour: np.ndarray) -> Tuple[int, int]:
    """计算最小外接圆中心"""
    (x, y), _ = cv2.minEnclosingCircle(contour)
    return int(x), int(y)


def calculate_ellipticity(contour: np.ndarray) -> Tuple[float, Optional[Tuple[int, int]]]:
    """计算轮廓的椭圆度和椭圆中心"""
    if len(contour) < 5:
        return 1.0, None

    try:
        ellipse = cv2.fitEllipse(contour)
        (x, y), (ma, Ma), _ = ellipse
        ellipticity = min(ma, Ma) / max(ma, Ma) if max(ma, Ma) > 0 else 1.0
        return ellipticity, (int(x), int(y))
    except:
        # 椭圆拟合失败，使用最小外接矩形估算椭圆度
        rect = cv2.minAreaRect(contour)
        width, height = rect[1]
        ellipticity = min(width, height) / max(width, height) if max(width, height) > 0 else 1.0
        return ellipticity, None


def adaptive_contour_center(contour: np.ndarray, image_shape: Optional[Tuple[int, int]] = None) -> Tuple[int, int]:
    """
    自适应选择轮廓中心计算方法

    参数:
    contour: 轮廓点集
    image_shape: 图像形状 (可选)

    返回:
    center: 轮廓中心坐标 (x, y)
    """
    # 输入验证
    if contour is None or len(contour) == 0:
        raise ValueError("轮廓不能为空")

    # 如果轮廓点太少，直接使用简单平均
    if len(contour) < 5:
        pts = contour.reshape(-1, 2)
        return int(pts[:, 0].mean()), int(pts[:, 1].mean())

    try:
        # 计算轮廓完整性指标
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(contour)

        completeness = contour_area / hull_area if hull_area > 0 else 0

        # 计算椭圆度和椭圆中心
        ellipticity, ellipse_center = calculate_ellipticity(contour)

        # 根据轮廓特性选择方法
        if completeness > 0.85:  # 轮廓较完整
            if ellipticity < 0.8 and ellipse_center is not None:  # 明显椭圆形且椭圆拟合成功
                return ellipse_center
            else:  # 接近圆形或椭圆拟合失败
                return centroid_center(contour)
        else:  # 轮廓不完整（有遮挡）
            return min_enclosing_circle_center(contour)

    except Exception:
        # 如果任何计算失败，回退到质心计算
        return centroid_center(contour)

#
# # 使用示例
# if __name__ == "__main__":
#     # 假设 contours 是从 cv2.findContours 获取的轮廓列表
#     contours = []  # 这里应该是实际的轮廓数据
#     centers = []
#
#     for contour in contours:
#         center = adaptive_contour_center(contour)
#         centers.append(center)