import os

import cv2
import numpy as np
from typing import Tuple, Optional, List
import math
import random


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


def is_square_like(contour: np.ndarray, angle_threshold: float = 15.0) -> bool:
    """
    判断轮廓是否为方形（包括正方形和长方形）

    参数:
    contour: 轮廓点集
    angle_threshold: 角度容差（度）

    返回:
    True: 是方形，False: 不是方形
    """
    if len(contour) < 4:
        return False

    try:
        # 计算最小外接矩形
        rect = cv2.minAreaRect(contour)
        width, height = rect[1]
        angle = rect[2]

        # 调整角度到0-90度范围
        if angle < -45:
            angle += 90
        elif angle > 45:
            angle -= 90

        # 判断角度是否接近0度或90度（方形应该是直角）
        return abs(angle) < angle_threshold
    except Exception:
        return False


def get_top_points_from_contour(contour: np.ndarray, top_percentage: float = 0.3) -> np.ndarray:
    """
    从轮廓中提取顶部点（y坐标最小的前百分比）

    参数:
    contour: 轮廓点集
    top_percentage: 顶部点的百分比（0-1）

    返回:
    top_points: 顶部点集
    """
    pts = contour.reshape(-1, 2)

    if len(pts) == 0:
        return np.array([])

    # 按y坐标排序
    sorted_indices = np.argsort(pts[:, 1])

    # 计算顶部点的数量
    top_count = max(1, int(len(pts) * top_percentage))

    # 提取顶部点
    top_indices = sorted_indices[:top_count]
    top_points = pts[top_indices]

    return top_points


def simple_top_center(contour: np.ndarray, top_percentage: float = 0.3) -> Tuple[int, int]:
    """
    简单方法：使用轮廓点中y最小的指定百分比点的x坐标中位数作为顶部中心

    参数:
    contour: 轮廓点集
    top_percentage: 顶部点的百分比（0-1）

    返回:
    (x, y): 顶部中心坐标
    """
    top_points = get_top_points_from_contour(contour, top_percentage)

    if len(top_points) == 0:
        pts = contour.reshape(-1, 2)
        return (int(np.median(pts[:, 0])), int(np.min(pts[:, 1])))

    # 计算x坐标中位数和y坐标平均值
    x_center = int(np.median(top_points[:, 0]))
    y_center = int(np.mean(top_points[:, 1]))

    return (x_center, y_center)


def square_top_center(contour: np.ndarray) -> Tuple[int, int]:
    """
    计算方形轮廓的顶部中心坐标

    参数:
    contour: 轮廓点集

    返回:
    (x, y): 顶部中心坐标
    """
    try:
        # 方法1：使用最小外接矩形的顶部边
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)

        # 按y坐标排序，找到顶部两个顶点
        sorted_box = box[np.argsort(box[:, 1])]
        top_points = sorted_box[:2]

        # 方法2：使用多边形逼近的顶部边（更精确）
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) == 4:
            # 找到多边形逼近的顶部两个顶点
            sorted_approx = approx.reshape(-1, 2)[np.argsort(approx.reshape(-1, 2)[:, 1])]
            top_approx = sorted_approx[:2]

            # 使用多边形逼近的顶部边（通常更精确）
            x_center = int(np.mean(top_approx[:, 0]))
            y_center = int(np.mean(top_approx[:, 1]))
        else:
            # 回退到最小外接矩形
            x_center = int(np.mean(top_points[:, 0]))
            y_center = int(np.mean(top_points[:, 1]))

        return (x_center, y_center)

    except Exception:
        # 如果失败，使用简单方法
        return simple_top_center(contour)


def parallelogram_top_center(contour: np.ndarray) -> Tuple[int, int]:
    """
    计算平行四边形轮廓的顶部中心坐标

    参数:
    contour: 轮廓点集

    返回:
    (x, y): 顶部中心坐标
    """
    try:
        # 使用多边形逼近得到四边形
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) == 4:
            # 获取四个顶点
            vertices = approx.reshape(-1, 2)

            # 按y坐标排序，找到顶部两个顶点
            sorted_vertices = vertices[np.argsort(vertices[:, 1])]
            top_points = sorted_vertices[:2]

            # 计算顶部中点
            x_center = int(np.mean(top_points[:, 0]))
            y_center = int(np.mean(top_points[:, 1]))

            return (x_center, y_center)
        else:
            # 如果不能得到四边形，使用直线拟合方法
            return parallelogram_top_center_fit(contour)

    except Exception:
        return parallelogram_top_center_fit(contour)


def parallelogram_top_center_fit(contour: np.ndarray) -> Tuple[int, int]:
    """
    使用直线拟合方法计算平行四边形顶部中心

    策略：
    1. 提取左侧点和右侧点
    2. 分别拟合左右两条边
    3. 计算两条边的中点连线
    4. 与顶部线的交点即为顶部中心

    参数:
    contour: 轮廓点集

    返回:
    (x, y): 顶部中心坐标
    """
    pts = contour.reshape(-1, 2)

    if len(pts) < 10:
        return simple_top_center(pts)

    # 找到x坐标的最小值和最大值
    x_min = np.min(pts[:, 0])
    x_max = np.max(pts[:, 0])

    # 将点分为左侧和右侧
    x_mid = (x_min + x_max) / 2
    left_points = pts[pts[:, 0] < x_mid]
    right_points = pts[pts[:, 0] >= x_mid]

    if len(left_points) < 5 or len(right_points) < 5:
        # 如果没有足够的点进行拟合，使用简单方法
        return simple_top_center(pts)

    try:
        # 拟合左侧边
        left_fit = np.polyfit(left_points[:, 0], left_points[:, 1], 1)

        # 拟合右侧边
        right_fit = np.polyfit(right_points[:, 0], right_points[:, 1], 1)

        # 找到顶部区域（y最小的点）
        top_points = get_top_points_from_contour(pts, top_percentage=0.3)

        if len(top_points) < 3:
            # 计算两条边的中点
            left_mid_x = (x_min + x_mid) / 2
            left_mid_y = left_fit[0] * left_mid_x + left_fit[1]

            right_mid_x = (x_mid + x_max) / 2
            right_mid_y = right_fit[0] * right_mid_x + right_fit[1]

            # 中点连线的交点与顶部线的交点
            # 这里简化处理：使用中点连线的中心点
            x_center = int((left_mid_x + right_mid_x) / 2)
            y_center = int((left_mid_y + right_mid_y) / 2)

            # 调整y坐标为顶部点的平均y值
            y_center = int(np.min(pts[:, 1])) + 2

        else:
            # 有足够的顶部点，直接使用顶部点的中心
            x_center = int(np.median(top_points[:, 0]))
            y_center = int(np.mean(top_points[:, 1]))

        return (x_center, y_center)

    except Exception:
        # 如果拟合失败，使用简单方法
        return simple_top_center(pts)


def occluded_top_center(contour: np.ndarray) -> Tuple[int, int]:
    """
    计算被遮挡轮廓的顶部中心坐标

    参数:
    contour: 轮廓点集

    返回:
    (x, y): 顶部中心坐标
    """
    try:
        # 使用凸包近似完整轮廓
        hull = cv2.convexHull(contour)
        hull_pts = hull.reshape(-1, 2)

        # 提取顶部点
        top_points = get_top_points_from_contour(hull_pts, top_percentage=0.3)

        if len(top_points) > 0:
            # 使用凸包的顶部点
            x_center = int(np.median(top_points[:, 0]))
            y_center = int(np.mean(top_points[:, 1]))
        else:
            # 如果凸包没有顶部点，使用最小外接矩形的顶部
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = np.int0(box)

            sorted_box = box[np.argsort(box[:, 1])]
            top_points = sorted_box[:2]

            x_center = int(np.mean(top_points[:, 0]))
            y_center = int(np.mean(top_points[:, 1]))

        return (x_center, y_center)

    except Exception:
        # 如果失败，使用简单方法
        return simple_top_center(contour)


def extract_top_centers(contour: np.ndarray,
                        completeness_threshold: float = 0.85,
                        angle_threshold: float = 15.0) -> Tuple[int, int]:
    """
    自适应提取轮廓的顶部中心坐标

    参数:
    contour: 轮廓点集
    completeness_threshold: 轮廓完整性阈值，大于此值认为未被遮挡
    angle_threshold: 方形角度容差（度）

    返回:
    (x, y): 顶部中心坐标
    """
    # 输入验证
    if contour is None or len(contour) < 3:
        raise ValueError("轮廓无效或点太少")

    try:
        # 计算轮廓完整性
        completeness = calculate_completeness(contour)

        # 情况1: 轮廓被遮挡
        if completeness < completeness_threshold:
            return occluded_top_center(contour)

        # 情况2: 轮廓完整
        else:
            # 判断是否为方形
            if is_square_like(contour, angle_threshold):
                return square_top_center(contour)
            else:
                # 情况3: 轮廓完整但不是方形（可能是平行四边形或其他形状）
                return parallelogram_top_center(contour)

    except Exception as e:
        # 如果所有方法都失败，使用简单方法
        print(f"自适应计算失败: {e}")
        return simple_top_center(contour)


# 辅助函数：用于批量处理轮廓
def extract_top_centers_batch(contours: List[np.ndarray],
                              min_area: int = 50,
                              completeness_threshold: float = 0.85,
                              angle_threshold: float = 15.0) -> List[Tuple[int, int]]:
    """
    批量提取多个轮廓的顶部中心坐标

    参数:
    contours: 轮廓列表
    min_area: 最小面积阈值
    completeness_threshold: 轮廓完整性阈值
    angle_threshold: 方形角度容差

    返回:
    centers: 顶部中心坐标列表
    """
    centers = []

    for contour in contours:
        # 过滤小轮廓
        if cv2.contourArea(contour) < min_area:
            continue

        try:
            center = extract_top_centers(contour, completeness_threshold, angle_threshold)
            centers.append(center)
        except Exception as e:
            print(f"处理轮廓失败: {e}")
            continue

    return centers


# 可视化函数（用于调试和验证）
def visualize_top_centers(image: np.ndarray, contours: List[np.ndarray], centers: List[Tuple[int, int]]) -> np.ndarray:
    """
    在图像上可视化轮廓和顶部中心

    参数:
    image: 原始图像
    contours: 轮廓列表
    centers: 顶部中心坐标列表

    返回:
    result: 可视化结果图像
    """
    result = image.copy()

    # 绘制所有轮廓
    cv2.drawContours(result, contours, -1, (0, 255, 0), 2)

    # 绘制顶部中心点
    for i, (x, y) in enumerate(centers):
        cv2.circle(result, (x, y), 5, (0, 0, 255), -1)
        cv2.putText(result, f'Top{i}', (x + 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    return result


# ===================== 生成测试图像函数 =====================

def create_occluded_shape(base_shape: np.ndarray, occlusion_rate: float = 0.1) -> np.ndarray:
    """
    创建一个被遮挡的图形
    """
    # 复制基本形状
    shape = base_shape.copy()

    # 找到图形的边界
    x_min, y_min = np.min(shape, axis=0)
    x_max, y_max = np.max(shape, axis=0)
    width = x_max - x_min
    height = y_max - y_min

    # 随机选择遮挡区域（顶部或侧边）
    occlusion_type = random.choice(['top', 'right', 'left', 'corner'])

    if occlusion_type == 'top':
        # 遮挡顶部
        occlusion_height = int(height * occlusion_rate)
        mask = shape[:, 1] > y_min + occlusion_height
        shape = shape[mask]
    elif occlusion_type == 'right':
        # 遮挡右侧
        occlusion_width = int(width * occlusion_rate)
        mask = shape[:, 0] < x_max - occlusion_width
        shape = shape[mask]
    elif occlusion_type == 'left':
        # 遮挡左侧
        occlusion_width = int(width * occlusion_rate)
        mask = shape[:, 0] > x_min + occlusion_width
        shape = shape[mask]
    else:  # 'corner'
        # 遮挡一个角
        occlusion_size = int(min(width, height) * occlusion_rate)
        # 随机选择一个角
        corner = random.choice(['top_left', 'top_right', 'bottom_left', 'bottom_right'])

        if corner == 'top_left':
            mask = ~((shape[:, 0] < x_min + occlusion_size) & (shape[:, 1] < y_min + occlusion_size))
        elif corner == 'top_right':
            mask = ~((shape[:, 0] > x_max - occlusion_size) & (shape[:, 1] < y_min + occlusion_size))
        elif corner == 'bottom_left':
            mask = ~((shape[:, 0] < x_min + occlusion_size) & (shape[:, 1] > y_max - occlusion_size))
        else:  # bottom_right
            mask = ~((shape[:, 0] > x_max - occlusion_size) & (shape[:, 1] > y_max - occlusion_size))

        shape = shape[mask]

    return shape


def create_test_image():
    """
    创建测试图像，包含9个标志物：
    - 3个被遮挡的不规则图形
    - 3个长方形
    - 3个平行四边形
    """
    # 创建黑色背景图像
    img_size = (800, 600)
    img = np.zeros((img_size[1], img_size[0], 3), dtype=np.uint8)

    # 定义蓝色
    blue_color = (255, 0, 0)  # BGR格式

    # 存储所有标志物的轮廓点（用于后续处理）
    all_shapes = []

    # 1. 创建3个被遮挡的不规则图形（基于平行四边形遮挡）
    print("创建被遮挡的不规则图形...")
    for i in range(3):
        # 基本平行四边形
        width = random.randint(20, 40)
        height = random.randint(10, 20)
        x = 100 + i * 200
        y = 100

        # 创建平行四边形顶点
        shear = random.randint(10, 20)
        pts = np.array([
            [x, y],
            [x + width, y],
            [x + width + shear, y + height],
            [x + shear, y + height]
        ], dtype=np.int32)

        # 创建被遮挡的图形
        occluded_pts = create_occluded_shape(pts, occlusion_rate=0.1)

        # 绘制填充的多边形
        if len(occluded_pts) >= 3:
            cv2.fillPoly(img, [occluded_pts], blue_color)
            all_shapes.append(occluded_pts)

    # 2. 创建3个长方形
    print("创建长方形...")
    for i in range(3):
        width = random.randint(20, 40)
        height = random.randint(10, 20)
        x = 120 + i * 200
        y = 250

        # 创建长方形顶点
        pts = np.array([
            [x, y],
            [x + width, y],
            [x + width, y + height],
            [x, y + height]
        ], dtype=np.int32)

        # 绘制填充的长方形
        cv2.fillPoly(img, [pts], blue_color)
        all_shapes.append(pts)

    # 3. 创建3个平行四边形
    print("创建平行四边形...")
    for i in range(3):
        width = random.randint(20, 40)
        height = random.randint(10, 20)
        x = 140 + i * 200
        y = 400

        # 创建平行四边形顶点（有一定倾斜）
        shear = random.randint(15, 25)
        pts = np.array([
            [x, y],
            [x + width, y],
            [x + width + shear, y + height],
            [x + shear, y + height]
        ], dtype=np.int32)

        # 绘制填充的平行四边形
        cv2.fillPoly(img, [pts], blue_color)
        all_shapes.append(pts)

    return img, all_shapes


# ===================== 主函数 =====================

if __name__ == '__main__':
    # 1. 创建RT_text文件夹（如果不存在）
    output_dir = "RT_text"
    os.makedirs(output_dir, exist_ok=True)

    # 2. 生成测试图像
    print("生成测试图像...")
    test_img, all_shapes = create_test_image()

    # 3. 保存测试图像
    test_img_path = os.path.join(output_dir, "top_ex_text.jpg")
    cv2.imwrite(test_img_path, test_img)
    print(f"测试图像已保存到: {test_img_path}")

    # # 4. 读取测试图像并进行处理
    # print("读取并处理测试图像...")
    # img = cv2.imread(test_img_path)
    #
    # # 转换为灰度图
    # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #
    # # 二值化处理（因为我们的图形是蓝色的，背景是黑色的）
    # _, binary = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    #
    # # 查找轮廓
    # contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #
    # print(f"找到 {len(contours)} 个轮廓")
    #
    # # 存储所有顶部中心点
    # top_centers = []
    #
    # # 5. 对每个轮廓提取顶部中心
    # for i, contour in enumerate(contours):
    #     try:
    #         # 过滤太小的轮廓
    #         if cv2.contourArea(contour) < 20:
    #             continue
    #
    #         # 提取顶部中心
    #         top_center = extract_top_centers(contour, completeness_threshold=0.85, angle_threshold=15.0)
    #         top_centers.append(top_center)
    #
    #         print(f"轮廓 {i}: 面积={cv2.contourArea(contour):.1f}, 顶部中心={top_center}")
    #
    #     except Exception as e:
    #         print(f"处理轮廓 {i} 时出错: {e}")
    #
    # # 6. 在原图上绘制结果
    # result_img = img.copy()
    #
    # # 绘制所有轮廓（绿色）
    # cv2.drawContours(result_img, contours, -1, (0, 255, 0), 2)
    #
    # # 绘制顶部中心点（红色）
    # for i, (x, y) in enumerate(top_centers):
    #     cv2.circle(result_img, (x, y), 5, (0, 0, 255), -1)
    #     cv2.putText(result_img, f'Top{i}', (x + 10, y - 10),
    #                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    #
    # # 7. 保存结果图像
    # result_img_path = os.path.join(output_dir, "top_ex_text_result.jpg")
    # cv2.imwrite(result_img_path, result_img)
    #
    # # 8. 显示结果
    # cv2.imshow("原始图像", img)
    # cv2.imshow("二值化图像", binary)
    # cv2.imshow("检测结果", result_img)
    #
    # print(f"结果图像已保存到: {result_img_path}")
    # print(f"检测到 {len(top_centers)} 个标志物的顶部中心")
    #
    # # 等待按键关闭窗口
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    #
    # # 9. 输出详细报告
    # print("\n=== 检测报告 ===")
    # for i, (x, y) in enumerate(top_centers):
    #     contour = contours[i] if i < len(contours) else None
    #     if contour is not None:
    #         area = cv2.contourArea(contour)
    #         completeness = calculate_completeness(contour)
    #         is_square = is_square_like(contour, angle_threshold=15.0)
    #         shape_type = "方形" if is_square else "平行四边形/其他"
    #
    #         if completeness < 0.85:
    #             shape_type = "被遮挡图形"
    #
    #         print(f"标志物 {i}: {shape_type}, 面积={area:.1f}, 完整性={completeness:.2f}, 顶部中心=({x}, {y})")