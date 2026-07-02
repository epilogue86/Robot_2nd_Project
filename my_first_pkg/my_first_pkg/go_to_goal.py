import math
import rclpy

from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from tf_transformations import euler_from_quaternion
from enum import Enum


class RobotState(Enum):
    GO_TO_GOAL = 1
    GOAL_REACHED = 2


class GoToGoal(Node):
    def __init__(self):
        super().__init__('go_to_goal')
        self.state = RobotState.GO_TO_GOAL

        self.goal_x = 5.0
        self.goal_y = 5.0

        self.current_x = 0.0
        self.current_y = 0.0

        self.yaw = 0.0

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

        if self.state == RobotState.GO_TO_GOAL:
            if distance < 0.15:
                self.state = (
                    RobotState.GOAL_REACHED
                )
                self.get_logger().info(
                    'Goal Reached'
                )
            else:
                kp = 1.0
                cmd.linear.x = 0.15
                cmd.angular.z = (
                    kp *
                    angle_error
                )

        elif self.state == RobotState.GOAL_REACHED:
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0

        self.get_logger().info(
            f'Dist:{distance:.2f} '
            f'AngleErr:{angle_error:.2f}'
        )

        self.cmd_pub.publish(cmd)
        
        
def main(args=None):
    rclpy.init(args=args)
    node = GoToGoal()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()        