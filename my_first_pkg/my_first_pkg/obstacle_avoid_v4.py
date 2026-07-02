import rclpy
from rclpy.node import Node

from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from enum import Enum


class RobotState(Enum):
    FORWARD = 1
    ROTATE_LEFT = 2
    ROTATE_RIGHT = 3


class ObstacleAvoidV4(Node):
    def __init__(self):
        super().__init__('obstacle_avoid_v2')
        self.front_distance = 999.0
        self.left_distance = 999.0
        self.right_distance = 999.0

        self.publisher_ = self.create_publisher(
            Twist, '/cmd_vel', 10
        )
        self.subscription = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10
        )
        self.timer = self.create_timer(0.1, self.control_loop)
        self.state = RobotState.FORWARD

    def scan_callback(self, msg):
        ranges = list(msg.ranges)

        self.front_distance = min(
            ranges[0:20] +
            ranges[340:360]
        )

        self.left_distance = min(
            ranges[60:120]
        )

        self.right_distance = min(
            ranges[240:300]
        )
        
        self.get_logger().info(
            f'F:{self.front_distance:.2f} '
            f'L:{self.left_distance:.2f} '
            f'R:{self.right_distance:.2f}'
        )

    def control_loop(self):
        cmd = Twist()

        if self.state == RobotState.FORWARD:
            if self.front_distance < 0.8:
                if self.left_distance > self.right_distance:
                    self.state = RobotState.ROTATE_LEFT
                    self.get_logger().warn("-> LEFT")
                else:
                    self.state = RobotState.ROTATE_RIGHT
                    self.get_logger().warn("-> RIGHT")
            else:
                cmd.linear.x = 0.15

        elif self.state == RobotState.ROTATE_LEFT:
            if self.front_distance > 1.2:
                self.state = RobotState.FORWARD
                self.get_logger().info("-> FORWARD")
            else:
                cmd.angular.z = 0.5    

        elif self.state == RobotState.ROTATE_RIGHT:
            if self.front_distance > 1.2:
                self.state = RobotState.FORWARD
                self.get_logger().info("-> FORWARD")
            else:
                cmd.angular.z = 0.5    
                
        self.publisher_.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidV4()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()