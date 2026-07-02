import rclpy
from rclpy.node import Node

from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from enum import Enum


class RobotState(Enum):
    FORWARD = 1
    ROTATE = 2


class ObstacleAvoidV3(Node):
    def __init__(self):
        super().__init__('obstacle_avoid_v2')
        self.front_distance = 999.0
        self.publisher_ = self.create_publisher(
            Twist, '/cmd_vel', 10
        )
        self.subscription = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10
        )
        self.timer = self.create_timer(0.1, self.control_loop)
        self.state = RobotState.FORWARD

    def scan_callback(self, msg):
        front_sector = (
            list(msg.ranges[0:20]) +
            list(msg.ranges[340:360])
        )

        self.front_distance = min(front_sector)

    def control_loop(self):
        cmd = Twist()

        if self.state == RobotState.FORWARD:
            if self.front_distance < 0.8:
                self.state = RobotState.ROTATE
                self.get_logger().warn("FORWARD -> ROTATE")
            else:
                cmd.linear.x = 0.15

        elif self.state == RobotState.ROTATE:
            if self.front_distance > 1.2:
                self.state = RobotState.FORWARD
                self.get_logger().info("ROTATE -> FORWARD")
            else:
                cmd.angular.z = 0.5    

        self.publisher_.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidV2()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()