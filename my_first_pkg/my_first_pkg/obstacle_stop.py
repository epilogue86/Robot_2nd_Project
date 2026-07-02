import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class ObstacleStop(Node):
    def __init__(self):
        super().__init__('obstacle_stop')
        self.publisher_ = self.create_publisher(
            Twist, '/cmd_vel', 10
        )

        self.subscription = self.create_subscription(
            LaserScan, '/scan', self.scan_callback,
            10
        )

    def scan_callback(self, msg):
        front = min(
            min(msg.ranges[0:20]),
            min(msg.ranges[340:360])
        )

        cmd = Twist()

        if front > 0.8:
            cmd.linear.x = 0.15
            self.get_logger().info('전진')
        else:
            cmd.angular.z = 0.5
            self.get_logger().warn("회전")

        self.publisher_.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleStop()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()