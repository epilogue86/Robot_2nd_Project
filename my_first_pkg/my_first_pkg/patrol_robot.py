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

        self.waypoints = [
            (1.0, 0.0),
            (1.0, 1.0),
            (0.0, 1.0),
            (0.0, 0.0)
        ]
        
        self.state = RobotState.GO_TO_GOAL
        self.current_x = 0.0
        self.current_y = 0.0
        self.yaw = 0.0
        self.current_waypoint = 0
        
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
        
        if self.state == RobotState.GOAL_REACHED:
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            self.cmd_pub.publish(cmd)
            
            self.get_logger().info('Mission Complete')
            return
        
        goal_x, goal_y = self.get_current_goal()
        
        dx = goal_x - self.current_x
        dy = goal_y - self.current_y

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
                self.get_logger().info(f'Waypoint {self.current_waypoint}')
                
                self.current_waypoint += 1
                
                if self.current_waypoint >= len(self.waypoints):
                    self.state = RobotState.GOAL_REACHED                    
            else:
                if abs(angle_error) > 0.3:
                    cmd.linear.x = 0.0
                else:
                    cmd.linear.x = 0.15
        
                kp = 1.0
                cmd.angular.z = kp * angle_error

            self.get_logger().info(
                f'Dist:{distance:.2f} '
                f'AngleErr:{angle_error:.2f}'
            )

            self.cmd_pub.publish(cmd)
        
    def get_current_goal(self):
        if self.current_waypoint >= len(self.waypoints):
            return None

        return self.waypoints[self.current_waypoint]
       
        
def main(args=None):
    rclpy.init(args=args)
    node = GoToGoal()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()        