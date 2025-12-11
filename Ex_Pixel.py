import cv2
import numpy as np
import extract_top_centers as etc
# 修改，替换标志物中心提取方法

class ExPixelCoord:
    """
    封装标志物的筛选、排序和记忆逻辑，便于连续帧提取像素坐标。

    polygon_pts 定义 ROI 多边形，pre_points 缓存上一帧结果以保持编号一致。
    """

    def __init__(self, polygon_pts, pre_points=None):
        self.pre_points = pre_points
        self.polygon_pts = polygon_pts

    def smart_sort_cross(self, points):
        """
        通过“逐行扫描”思路对检测到的点排序，保证初次加载时编号稳定。

        每次选择 y 最小的点作为行参考，收集同一行内的点并按 x 排序，直至所有点被取走。
        """
        remaining = points.copy()
        sorted_points = []

        while remaining:
            ref_point = min(remaining, key=lambda p: p[1])

            # TODO: 将固定的 30px 行阈值暴露给调用者以匹配不同分辨率。
            row_points = [p for p in remaining if abs(p[1] - ref_point[1]) <= 30]
            sorted_row = sorted(row_points, key=lambda p: p[0])

            sorted_points.extend(sorted_row)
            remaining = [p for p in remaining if p not in row_points]

        return sorted_points

    # 修改，增加多数点稳定原则
    def sort_with_previous(self, centers):
        """
        基于上一帧的坐标结果进行匹配，维持点位顺序并剔除离群值。

        对每个历史点遍历未被占用的新点，限制 dx/dy 合理范围后按距离选出最佳匹配，
        若找不到候选则沿用历史值，确保输出长度和顺序稳定。
        """
        sorted_points = []
        # 创建新点使用状态标记数组
        used_centers = [False] * len(centers)  # 标记新点是否已被匹配
        # 记录每个点的移动距离
        distances = []

        # 为每个历史点寻找匹配的新点
        for i, (px, py) in enumerate(self.pre_points):
            found = False
            best_match = None
            best_distance = float('inf')  # 初始化为无穷大

            # 遍历所有新点，寻找最佳匹配
            for j, (cx, cy) in enumerate(centers):
                if used_centers[j]:  # 跳过已使用的新点
                    continue

                dy_val = cy - py  # y方向差值
                dx = abs(cx - px)  # x方向绝对差值

                # 检查坐标差值条件
                if -20 <= cy - py <= 45 and -50 <= cx - px <= 50:
                    distance = dx ** 2 + dy_val ** 2  # 计算欧氏距离平方

                    # 记录距离最小的匹配点
                    if distance < best_distance:
                        best_match = j
                        best_distance = distance
                        found = True  # 标记找到至少一个候选点

            # 如果找到匹配点，使用该点
            if found:
                cx, cy = centers[best_match]
                sorted_points.append((cx, cy))
                used_centers[best_match] = True  # 标记该新点已被使用
                # 记录实际距离
                actual_distance = ((cx - px) ** 2 + (cy - py) ** 2) ** 0.5
                distances.append(actual_distance)
            else:
                # 未找到匹配点时，使用历史点
                sorted_points.append((px, py))
                distances.append(0)  # 距离为0

        # 变化检测和纠正逻辑
        if len(sorted_points) == len(self.pre_points):
            # 定义变化阈值（可根据实际情况调整）
            change_threshold = 50.0

            # 统计变化不大的点数量
            small_change_count = sum(1 for d in distances if d < change_threshold)
            change_ratio = small_change_count / len(distances)

            # 如果超过60%的点变化不大，但存在少数变化大的点，则进行纠正
            if change_ratio >= 0.75:
                for i in range(len(sorted_points)):
                    if distances[i] >= change_threshold:
                        # 重置为历史点中对应下标的值
                        sorted_points[i] = self.pre_points[i]

        return sorted_points

    # 修改，增加is_image_too_dark方法
    def is_image_too_dark(self,img_path, dark_threshold=60):
        """
        判断图像是否过暗

        参数:
        - img_path: 图像路径
        - dark_threshold: 亮度阈值（0-255）
        - dark_pixel_ratio: 暗像素比例阈值

        返回:
        - True: 图像过暗
        - False: 图像亮度正常
        """
        img = cv2.imread(img_path)
        if img is None:
            return True  # 如果无法读取，也跳过

        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 计算统计信息
        mean_val = np.mean(gray)
        std_val = np.std(gray)  # 标准差，用于判断对比度

        # 计算直方图
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        total_pixels = gray.size

        # 计算不同亮度区间的像素比例
        very_dark = np.sum(hist[:30]) / total_pixels  # 极暗像素比例
        dark = np.sum(hist[:60]) / total_pixels  # 较暗像素比例
        mid = np.sum(hist[60:180]) / total_pixels  # 中等亮度像素比例
        bright = np.sum(hist[180:]) / total_pixels  # 明亮像素比例

        # 多个判断条件（可调整）
        conditions = [
            mean_val < dark_threshold,  # 平均亮度太低
            very_dark > 0.4,  # 太多极暗像素
            (dark > 0.7 and std_val < 30),  # 大部分像素暗且对比度低
            bright < 0.05 and mean_val < 60,  # 几乎没有明亮像素且平均亮度低
        ]

        return any(conditions)

    def mark_pixel_coords_ex(self, img_file):
        """
        读取图片、在 ROI 内提取蓝色标志物轮廓、计算中心并返回排序后的坐标列表。

        流程：
        1. HSV 阈值提取蓝色区域；
        2. 应用多边形掩膜限定区域；
        3. 查找轮廓 -> 过滤面积 -> 使用 adaptive_contour_center 求中心；
        4. 基于历史或初次排序策略输出最终像素坐标。
        """
        img = cv2.imread(img_file)
        if img is None:
            print("Error: 无法读取图像文件")
            return

        # 转换为HSV颜色空间
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # 修改，调整了hsv阈值范围
        if self.is_image_too_dark(img_file):
            lower_red1 = np.array([0, 180, 50])  # 红色低区间（H: 0-10）
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([140, 180, 50])  # 红色高区间（H: 160-180）
            upper_red2 = np.array([180, 255, 255])
        else:
            lower_red1 = np.array([0, 150, 180])  # 红色低区间（H: 0-10）
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 90, 180])  # 红色高区间（H: 160-180）
            upper_red2 = np.array([180, 255, 255])

        # 创建红色掩膜（需要组合两个范围）
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        # 创建多边形区域掩膜
        mask_poly = np.zeros_like(mask_red)
        cv2.fillPoly(mask_poly, [self.polygon_pts], 255)

        # 联合掩膜：只在多边形区域内检测红色
        mask_combined = cv2.bitwise_and(mask_red, mask_poly)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_closed = cv2.morphologyEx(mask_combined, cv2.MORPH_CLOSE, kernel)

        # 查找轮廓
        contours, _ = cv2.findContours(mask_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        centers = []
        min_area = 40

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            center = etc.extract_top_centers(contour)
            centers.append(center)

        if not centers:
            print("未找到有效标志物")
            return

        if self.pre_points is None:
            sorted_points = self.smart_sort_cross(centers)
        else:
            sorted_points = self.sort_with_previous(centers)

        self.pre_points = np.array(sorted_points, dtype=np.float32)

        return self.pre_points


if __name__ == "__main__":
    process = ExPixelCoord(
        polygon_pts=np.array(
            [(1059, 841), (2689, 831), (2635, 1645), (1093, 1611)], dtype=np.int32
        )
    )
    img_path = r"ocr_text_img/TLS_0202_0001.jpg"
    pixel = process.mark_pixel_coords_ex(img_path)
    img_backup_path = r"ocr_text_img/text.jpg"
    img = cv2.imread(img_path)
    img_draw = img.copy()
    for idx, (x, y) in enumerate(pixel, 1):
        cv2.circle(img_draw, (int(x), int(y)), 2, (0, 255, 0), -1)
        cv2.putText(
            img_draw,
            str(idx),
            (int(x + 10), int(y - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            3,
            (0, 255, 0),
            2,
        )
    cv2.imwrite(img_backup_path, img_draw)
    del img_draw
    del img
