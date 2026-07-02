import math
import rclpy

from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from tf_transformations import euler_from_quaternion
from enum import Enum


class RobotState(Enum):
    GO_TO_GOAL = 1
    AVOID_OBSTACLE = 2
    GOAL_REACHED = 3


class GoalWithAvoid(Node):
    def __init__(self):
        super().__init__('goal_with_avoid')
        self.state = RobotState.GO_TO_GOAL

        # 목표 좌표
        self.goal_x = 2.0
        self.goal_y = 2.0

        # 현재 위치
        self.current_x = 0.0
        self.current_y = 0.0

        # 현재 방향
        self.yaw = 0.0

        # LiDAR 정보
        self.front_distance = 999.0
        self.left_distance = 999.0
        self.right_distance = 999.0

        # Publisher
        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # Subscriber
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        # Control Loop
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

        q = msg.pose.pose.orientation

        _, _, self.yaw = (
            euler_from_quaternion(
                [
                    q.x,
                    q.y,
                    q.z,
                    q.w
                ]
            )
        )

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

    def normalize_angle(self, angle):
        while angle > math.pi:
            angle -= 2 * math.pi

        while angle < -math.pi:
            angle += 2 * math.pi

        return angle

    def control_loop(self):
        cmd = Twist()

        dx = (
            self.goal_x -
            self.current_x
        )

        dy = (
            self.goal_y -
            self.current_y
        )

        distance = math.sqrt(
            dx**2 +
            dy**2
        )

        goal_angle = math.atan2(
            dy,
            dx
        )

        angle_error = (
            goal_angle -
            self.yaw
        )

        angle_error = self.normalize_angle(
            angle_error
        )

        # ====================
        # GO_TO_GOAL
        # ====================

        if self.state == RobotState.GO_TO_GOAL:
            if distance < 0.15:
                self.state = (
                    RobotState.GOAL_REACHED
                )

                self.get_logger().info(
                    'Goal Reached'
                )
            elif self.front_distance < 0.6:
                self.state = (
                    RobotState.AVOID_OBSTACLE
                )

                self.get_logger().warn(
                    'Obstacle Detected'
                )
            else:
                kp = 1.0
                cmd.linear.x = 0.15
                cmd.angular.z = (
                    kp *
                    angle_error
                )

        # ====================
        # AVOID_OBSTACLE
        # ====================

        elif self.state == RobotState.AVOID_OBSTACLE:
            if self.front_distance > 1.0:
                self.state = (
                    RobotState.GO_TO_GOAL
                )

                self.get_logger().info(
                    'Path Clear'
                )

            else:
                if (
                    self.left_distance >
                    self.right_distance
                ):

                    cmd.angular.z = 0.5
                else:

                    cmd.angular.z = -0.5

        # ====================
        # GOAL_REACHED
        # ====================

        elif self.state == RobotState.GOAL_REACHED:
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0

        self.get_logger().info(
            f'STATE={self.state.name} '
            f'DIST={distance:.2f} '
            f'FRONT={self.front_distance:.2f}'
        )

        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = GoalWithAvoid()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()