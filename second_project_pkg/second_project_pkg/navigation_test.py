import rclpy
import threading

from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import Twist, PoseStamped
from std_msgs.msg import String

# 목적지 정의
sectors = {
    "1": (-1.8,  1.8),  # A
    "2": ( 1.8,  1.8),  # B
    "3": ( 1.8, -1.8),  # C
    "4": (-1.8, -1.8),  # D
    "5": ( 0.0, -0.75),  # HOME
}
        
# sectors = {
#     "1": (-1.8,  1.8,  0.0),  # A
#     "2": ( 1.8,  1.8,  0.0),  # B
#     "3": ( 1.8, -1.8,  0.0),  # C
#     "4": (-1.8, -1.8,  0.0),  # D
#     "5": ( 0.0, -0.75, 0.0),  # HOME
# }
        
class NavigationController(Node):
    def __init__(self):
        super().__init__('navigation_controller')

        # Navigation2 액션 클라이언트
        self.action_client = ActionClient(self, NavigateToPose,'/navigate_to_pose')
        
        # 정지를 위한 cmd 퍼블리셔
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # 사람 감지 토픽 구독
        self.sub = self.create_subscription(String, '/object_detected', self.detect_callback, 10)
        
        self.get_logger().info("Navigation Controller Ready")
        
        # 0.5초마다 콜백 실행(디버깅)
        # self.timer = self.create_timer(0.5, self.timer_callback)

    
    # # 디버깅을 위한 타이머 콜백 함수
    # def timer_callback(self):
        # self.get_logger().info(f"test")
        

    def send_goal(self, x, y):
        goal_msg = NavigateToPose.Goal()
        
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.w = 1.0  # 단순히 정방향

        self.action_client.wait_for_server()
        self._send_future = self.action_client.send_goal_async(goal_msg)
        
        self.get_logger().info(f"목표 좌표 ({x}, {y})로 이동 명령 전송")
        self.get_logger().info(f"_send_future: {self._send_future}")
        
        
    def cancel_goal(self):        
        if hasattr(self, "_send_future"):
            goal_handle = self._send_future.result()
            
            if goal_handle:
                goal_handle.cancel_goal_async()
                self.get_logger().info("현재 이동 취소")
        
    # 사람 감지 콜백
    def detect_callback(self, msg):
        self.get_logger().info(f"사람 감지 여부: {msg.data}")


def main():
    rclpy.init()
    node = NavigationController()
    
     # spin을 별도 스레드에서 실행
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()
    
    print("키보드 입력 대기: 1~5 → 해당 위치 이동, c → 취소, q → 종료")

    while rclpy.ok():
        key = input("\n[1-5] Goal  [c] Cancel  [q] Quit : ")
        
        if key in sectors:
            x, y = sectors[key]
            node.send_goal(x, y)
        elif key == "c":
            node.cancel_goal()
        elif key == "q":
            print("프로그램 종료")
            break
        else:
            print("잘못된 입력입니다.")
             
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
        