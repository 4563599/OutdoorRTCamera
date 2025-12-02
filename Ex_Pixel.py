import cv2
import numpy as np
import  Ex_center_yuan as ecy

class ExPixelCoord:
    def __init__(self,polygon_pts,pre_points=None):
        self.pre_points = pre_points
        self.polygon_pts = polygon_pts

    def smart_sort_cross(self,points):
        # 初始化未处理点集
        remaining = points.copy()
        sorted_points = []

        while remaining:
            # 第一步：找到y坐标最小的点作为当前行参考点
            ref_point = min(remaining, key=lambda p: p[1])

            # 第二步：提取该行所有点（y坐标差值在30像素以内）
            row_points = [p for p in remaining if abs(p[1] - ref_point[1]) <= 30]

            # 按x坐标排序，确定起始点和终止点
            sorted_row = sorted(row_points, key=lambda p: p[0])

            # 第三步：更新结果集和剩余点集
            sorted_points.extend(sorted_row)
            remaining = [p for p in remaining if p not in row_points]

        return sorted_points

    def sort_with_previous(self, centers):
        """基于历史点的智能排序（结合最近距离法和使用标记）"""
        sorted_points = []
        # 创建新点使用状态标记数组
        used_centers = [False] * len(centers)  # 标记新点是否已被匹配

        # 为每个历史点寻找匹配的新点
        for px, py in self.pre_points:
            found = False
            best_match = None
            best_distance = float('inf')  # 初始化为无穷大

            # 遍历所有新点，寻找最佳匹配
            for j, (cx, cy) in enumerate(centers):
                if used_centers[j]:  # 跳过已使用的新点
                    continue

                dy_val = cy - py  # y方向差值
                dx = abs(cx - px)  # x方向绝对差值
                dx_val = cx - px

                # 检查坐标差值条件
                # 293
                if abs(cy - py) <= 100 and -40 <= cx - px <= 180:
                    distance = dx ** 2 + dy_val ** 2  # 计算欧氏距离平方（避免开方运算）

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
            else:
                # 未找到匹配点时，使用历史点
                sorted_points.append((px, py))

        return sorted_points

    def mark_pixel_coords_ex(self, img_file):
        # 读取图像
        img = cv2.imread(img_file)
        if img is None:
            print("Error: 无法读取图像文件")
            return

        # 转换为HSV颜色空间
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # 定义蓝色的HSV阈值范围（注意：需根据实际蓝色调整）
        lower_blue = np.array([70, 70, 70])  # 蓝色低区间（H: 100-120）
        upper_blue = np.array([140, 255, 255])

        # 创建蓝色掩膜
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

        # 创建多边形区域掩膜
        mask_poly = np.zeros_like(mask_blue)
        cv2.fillPoly(mask_poly, [self.polygon_pts], 255)

        # 联合掩膜：只在多边形区域内检测
        mask_combined = cv2.bitwise_and(mask_blue, mask_poly)

        # 查找轮廓
        contours, _ = cv2.findContours(mask_combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 过滤小轮廓并提取顶端中心坐标
        centers = []
        min_area = 50  # 根据实际情况调整面积阈值
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            center=ecy.adaptive_contour_center(contour)
            centers.append(center)

        if not centers:
            print("未找到有效标志物")
            return

        if self.pre_points is None:  # 第一次调用
            sorted_points = self.smart_sort_cross(centers)
        else:  # 后续调用
            sorted_points = self.sort_with_previous(centers)

            # 更新历史点（转换为numpy数组以便后续处理）
        self.pre_points = np.array(sorted_points, dtype=np.float32)

        return self.pre_points

if __name__ == '__main__':
    process=ExPixelCoord(polygon_pts=np.array([(1059,841), (2689,831), (2635,1645), (1093,1611)], dtype=np.int32))
    img_path=r'ocr_text_img/TLS_0202_0001.jpg'
    pixel=process.mark_pixel_coords_ex(img_path)
    img_backup_path=r'ocr_text_img/text.jpg'
    img = cv2.imread(img_path)
    # 绘制编号和坐标点
    img_draw = img.copy()
    for idx, (x, y) in enumerate(pixel, 1):
        cv2.circle(img_draw, (int(x), int(y)), 2, (0, 255, 0), -1)
        cv2.putText(img_draw, str(idx), (int(x + 10), int(y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 2)
    cv2.imwrite(img_backup_path, img_draw)
    del img_draw
    del img