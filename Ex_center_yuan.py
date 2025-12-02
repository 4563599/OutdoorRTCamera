import cv2
import numpy as np
from typing import Tuple, Optional


def centroid_center(contour: np.ndarray) -> Tuple[int, int]:
    """
    根据几何矩计算轮廓质心，当 m00 为 0 时退回到所有点的算术平均值。

    质心方案对完整、规则的目标响应最快，所以优先尝试该方法以覆盖大多数场景。
    """
    M = cv2.moments(contour)
    if M["m00"] != 0:
        return int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])

    pts = contour.reshape(-1, 2)
    return int(pts[:, 0].mean()), int(pts[:, 1].mean())


def min_enclosing_circle_center(contour: np.ndarray) -> Tuple[int, int]:
    """
    使用最小外接圆得到圆心，对缺口明显或更接近圆形的轮廓更加稳健。

    最小外接圆能够缓和局部噪声影响，适合作为遮挡情况下的后备方案。
    """
    (x, y), _ = cv2.minEnclosingCircle(contour)
    return int(x), int(y)


def calculate_ellipticity(contour: np.ndarray) -> Tuple[float, Optional[Tuple[int, int]]]:
    """
    拟合椭圆以求得椭圆度（短轴 / 长轴）及椭圆中心，用于识别椭圆形标志物。

    当拟合失败时退化为最小外接矩形估算椭圆度，返回 None 表明中心不可用。
    """
    if len(contour) < 5:
        return 1.0, None

    try:
        ellipse = cv2.fitEllipse(contour)
        (x, y), (ma, Ma), _ = ellipse
        ellipticity = min(ma, Ma) / max(ma, Ma) if max(ma, Ma) > 0 else 1.0
        return ellipticity, (int(x), int(y))
    except Exception:
        # TODO: 捕获更具体的异常并附带 contour id 以定位拟合失败原因。
        rect = cv2.minAreaRect(contour)
        width, height = rect[1]
        ellipticity = min(width, height) / max(width, height) if max(width, height) > 0 else 1.0
        return ellipticity, None


def adaptive_contour_center(contour: np.ndarray, image_shape: Optional[Tuple[int, int]] = None) -> Tuple[int, int]:
    """
    结合轮廓完整度与椭圆度，自适应选择质心、椭圆中心或外接圆中心。

    - 轮廓点 < 5 直接返回平均值，避免计算不稳定；
    - 完整轮廓优先采用椭圆拟合中心；
    - 缺口或遮挡严重时退回到外接圆中心；
    - image_shape 预留给后续基于图像大小的策略，可用于归一化阈值。
    """
    if contour is None or len(contour) == 0:
        raise ValueError("轮廓不能为空")

    if len(contour) < 5:
        pts = contour.reshape(-1, 2)
        return int(pts[:, 0].mean()), int(pts[:, 1].mean())

    try:
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(contour)

        completeness = contour_area / hull_area if hull_area > 0 else 0

        ellipticity, ellipse_center = calculate_ellipticity(contour)

        if completeness > 0.85:
            if ellipticity < 0.8 and ellipse_center is not None:
                return ellipse_center
            return centroid_center(contour)
        else:
            return min_enclosing_circle_center(contour)

    except Exception:
        return centroid_center(contour)
