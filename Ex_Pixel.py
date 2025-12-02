import cv2
import numpy as np
import Ex_center_yuan as ecy


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

    def sort_with_previous(self, centers):
        """
        基于上一帧的坐标结果进行匹配，维持点位顺序并剔除离群值。

        对每个历史点遍历未被占用的新点，限制 dx/dy 合理范围后按距离选出最佳匹配，
        若找不到候选则沿用历史值，确保输出长度和顺序稳定。
        """
        sorted_points = []
        used_centers = [False] * len(centers)

        for px, py in self.pre_points:
            found = False
            best_match = None
            best_distance = float("inf")

            for j, (cx, cy) in enumerate(centers):
                if used_centers[j]:
                    continue

                dy_val = cy - py
                dx = abs(cx - px)

                if abs(cy - py) <= 100 and -40 <= cx - px <= 180:
                    distance = dx ** 2 + dy_val ** 2
                    if distance < best_distance:
                        best_match = j
                        best_distance = distance
                        found = True

            if found:
                cx, cy = centers[best_match]
                sorted_points.append((cx, cy))
                used_centers[best_match] = True
            else:
                sorted_points.append((px, py))

        return sorted_points

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

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        lower_blue = np.array([70, 70, 70])
        upper_blue = np.array([140, 255, 255])
        # TODO: 允许通过配置或构造函数注入 HSV 阈值，减少硬编码。

        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

        mask_poly = np.zeros_like(mask_blue)
        cv2.fillPoly(mask_poly, [self.polygon_pts], 255)

        mask_combined = cv2.bitwise_and(mask_blue, mask_poly)

        contours, _ = cv2.findContours(
            mask_combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        centers = []
        min_area = 50
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            center = ecy.adaptive_contour_center(contour)
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
