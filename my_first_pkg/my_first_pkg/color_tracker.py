import cv2
import numpy as np
import rclpy

from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class ColorTracker(Node):
    def __init__(self):
        super().__init__('color_tracker')
        self.bridge = CvBridge()
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        self.get_logger().info('Color Tracker Started')

    def image_callback(self, msg):
        # ROS Image -> OpenCV Image
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # BGR -> HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # ------------------------
        # Red Color Range
        # ------------------------
        lower_red1 = np.array([0, 120, 70])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 70])
        upper_red2 = np.array([180, 255, 255])

        # ------------------------
        # Create Mask
        # ------------------------
        mask1 = cv2.inRange(hsv,lower_red1,upper_red1)
        mask2 = cv2.inRange(hsv,lower_red2,upper_red2)
        mask = mask1 + mask2

        # 노이즈 제거
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask,kernel,iterations=1)
        mask = cv2.dilate(mask,kernel,iterations=2)

        # ------------------------
        # Find Contours
        # ------------------------
        contours, _ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE
        )

        if len(contours) > 0:
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)

            if area > 300:
                M = cv2.moments(largest)

                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    # 중심 표시
                    cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

                    # Bounding Box
                    x, y, w, h = cv2.boundingRect(largest)

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                    # 텍스트 출력
                    cv2.putText(
                        frame,
                        f'Center: ({cx},{cy})',
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2
                    )

                    cv2.putText(
                        frame,
                        f'Area: {int(area)}',
                        (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2
                    )

                    # 로그 출력
                    self.get_logger().info(
                        f'Center X={cx}, Y={cy}, Area={area:.0f}'
                    )

        # 화면 중앙선 표시
        h, w = frame.shape[:2]

        cv2.line(frame, (w // 2, 0), (w // 2, h), (255, 255, 0), 2)

        # 화면 출력

        cv2.imshow('Camera', frame)
        cv2.imshow('Mask', mask)

        key = cv2.waitKey(1)

        if key == ord('q'):
            self.get_logger().info('Shutdown')
            rclpy.shutdown()

    def destroy_node(self):
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ColorTracker()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()