import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class MoveForward(Node):
    def __init__(self):
        super().__init__('move_forward')
        self.publisher_ = self.create_publisher(
            Twist, '/cmd_vel', 10
        )
        self.timer = self.create_timer(
            0.1, self.timer_callback
        )

    def timer_callback(self):
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.1
        self.publisher_.publish(msg)
        self.get_logger().info(
            'forward'
        )


def main(args=None):
    rclpy.init(args=args)
    node = MoveForward()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()