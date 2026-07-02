import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2
import numpy as np


class CameraBasic(Node):

    def __init__(self):
        super().__init__('camera_basic')

        self.bridge = CvBridge()

        self.sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.callback,
            10
        )

        self.get_logger().info("Red pixel detector started")

    def callback(self, msg):

        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')

        # =========================
        # 1. 빨간색 조건 정의 (아주 단순)
        # =========================
        b, g, r = cv2.split(frame)

        red_mask = (r > 100) & (g < 30) & (b < 30)

        # =========================
        # 2. 빨간 픽셀 개수
        # =========================
        red_count = np.sum(red_mask)

        # =========================
        # 3. 전체 픽셀 대비 비율
        # =========================
        total_pixels = frame.shape[0] * frame.shape[1]

        ratio = red_count / total_pixels

        # =========================
        # 4. 판단
        # =========================
        if ratio > 0.01:
            self.get_logger().info(f"RED OBJECT DETECTED! ratio={ratio:.4f}")
        else:
            self.get_logger().info(f"No red object ratio={ratio:.4f}")

        b_, g_, r_ = frame[240, 320]
        self.get_logger().info(f"center pixel value: ({b_}, {g_}, {r_})")
        
        # =========================
        # 5. 시각화
        # =========================
        mask_visual = red_mask.astype(np.uint8) * 255

        cv2.imshow("camera", frame)
        cv2.imshow("red mask", mask_visual)
        cv2.waitKey(1)


def main():
    rclpy.init()
    node = CameraBasic()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()