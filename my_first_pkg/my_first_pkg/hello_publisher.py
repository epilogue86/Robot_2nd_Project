import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class HelloPublisher(Node):
    def __init__(self):
        super().__init__('hello_publisher')
        self.publisher_ = self.create_publisher(
            String, 'hello_topic', 10
        )
        self.timer = self.create_timer(
            1.0, self.timer_callback
        )
        self.count = 0

    def timer_callback(self):
        self.count += 1
        msg = String()
        msg.data = f"message {self.count}"
        self.publisher_.publish(msg)
        self.get_logger().info(msg.data)


def main(args=None):
    rclpy.init(args=args)
    node = HelloPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()