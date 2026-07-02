import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class ScanReader(Node):
    def __init__(self):
        super().__init__('scan_reader')
        self.subscription = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10
        )

    def scan_callback(self, msg):
        front = min(
            min(msg.ranges[0:20]), 
            min(msg.ranges[340:360])
        )

        if front < 0.5:
            self.get_logger().warn(f"장애물 발견! {front:.2f} m")
        else:
            self.get_logger().info(f"안전 {front:.2f} m")


def main(args=None):
    rclpy.init(args=args)
    node = ScanReader()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()