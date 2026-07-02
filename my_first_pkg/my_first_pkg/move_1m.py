import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from enum import Enum


class RobotState(Enum):
    MOVE = 1
    STOP = 2


class MoveOneMeter(Node):
    def __init__(self):
        super().__init__('move_one_meter')
        self.state = RobotState.MOVE
        self.current_x = 0.0
        self.current_y = 0.0
        self.start_x = None
        self.start_y = None

        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.timer = self.create_timer(
            0.1,
            self.control_loop
        )

    def odom_callback(self, msg):
        self.current_x = (
            msg.pose.pose.position.x
        )
        self.current_y = (
            msg.pose.pose.position.y
        )
        
        if self.start_x is None:
            self.start_x = self.current_x
            self.start_y = self.current_y

            self.get_logger().info(
                '시작 위치 저장'
            )

    def control_loop(self):
        if self.start_x is None:
            return

        distance = math.sqrt(
            (self.current_x - self.start_x)**2 +
            (self.current_y - self.start_y)**2
        )

        cmd = Twist()

        if self.state == RobotState.MOVE:
            if distance < 1.0:
                cmd.linear.x = 0.15
                self.get_logger().info(
                    f'이동중 {distance:.2f}m'
                )
            else:
                self.state = RobotState.STOP
                self.get_logger().info(
                    '목표 도달'
                )
        elif self.state == RobotState.STOP:
            cmd.linear.x = 0.0

        self.cmd_pub.publish(cmd)
        
        
def main(args=None):
    rclpy.init(args=args)
    node = MoveOneMeter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()        