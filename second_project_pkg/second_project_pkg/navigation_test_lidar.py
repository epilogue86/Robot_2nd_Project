import rclpy
import threading

from rclpy.node import Node
from rclpy.action import ActionClient

from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import Twist, PoseStamped
from std_msgs.msg import String
from sensor_msgs.msg import LaserScan
from action_msgs.msg import GoalStatus

from rclpy.duration import Duration


# 목적지 정의
sectors = {
    "1": ( -1.8,   1.84, 1.0),  # A
    "2": (  1.82,  1.78, 1.0),  # B
    "3": (  1.75, -1.73, 1.0),  # C
    "4": ( -1.8,  -1.8,  1.0),  # D
    "5": (  0.0,  -0.68, 1.0),  # HOME
}
        
class NavigationTest(Node):
    def __init__(self):
        super().__init__('navigation_test')

        # Navigation2 액션 클라이언트
        self.action_client = ActionClient(self, NavigateToPose,'/navigate_to_pose')
        
        # 정지를 위한 cmd 퍼블리셔
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Camera 토픽 구독
        self.camera_sub = self.create_subscription(String, '/object_detected', self.detect_callback, 10)
        
        # Lidar 토픽 구독
        self.lidar_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        
        self.get_logger().info("Navigation Test Ready")
        
        self._goal_handle = None
        self._send_goal_future = None
        self.goal_pose = None
        
        self.goal_reached = True
        self.is_driving = False

        self.front_distance = 999.0
        
        self.last_log_time = self.get_clock().now()
        self.log_interval = Duration(seconds = 1)
    
    
    # Camera 구독 콜백
    def detect_callback(self, msg):
        # 목표 위치에 도달했거나 설정되지 않았을 경우는 처리하지 않음
        if self.goal_reached == True:
            return
            
        self.get_logger().info(f"Person: {msg.data}")
 
        # 목표 위치가 설정된 후 주행 중일 때
        if self.is_driving:
            if msg.data == "Mannequin":
                self.cancel_goal()
        else:    
            if msg.data == "Nothing":
                self.resume_goal()

    # Lidar 구독 콜백
    def scan_callback(self, msg):
        ranges = list(msg.ranges)
        self.front_distance = min(ranges[0:20] + ranges[340:360])
        
        self.get_logger().info(f"F:{self.front_distance:.2f}")
        
        
    # 목표 위치로 이동 요청 함수
    def send_goal(self, x, y, w):
        # 액션 서버가 켜질 때까지 대기
        self.action_client.wait_for_server()
        
        self.goal_pose = (x, y, w)
            
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.w = w

        self.get_logger().info(f'목표 전송 중... X: {x}, Y: {y}')
        
        # 비동기로 목표를 보내고 응답 처리 콜백(goal_response_callback) 연결
        self._send_goal_future = self.action_client.send_goal_async(
            goal_msg,
            feedback_callback = self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)
        
        
    # 실시간 피드백 콜백 함수(이동 중 주기적으로 실행됨) -> 디버깅용
    def feedback_callback(self, feedback_msg):
        return
    
        current_time = self.get_clock().now()
        
        if (current_time - self.last_log_time) < self.log_interval:
            return
        
        self.last_log_time = current_time
        
        feedback = feedback_msg.feedback
        x = feedback.current_pose.pose.position.x
        y = feedback.current_pose.pose.position.y
        distance = feedback.distance_remaining
        time = feedback.estimated_time_remaining.sec    
    
        # 터미널에 실시간 로그 출력
        self.get_logger().info(
            f"현재 위치: ({x:.2f}, {y:.2f}) | 남은 거리: {distance:.2f}m | 예상 남은 시간: {time}초"
        )
        
        
    # 서버가 목표를 수락했는지 확인하는 콜백
    def goal_response_callback(self, future):
        goal_handle = future.result()
        
        if not goal_handle.accepted:
            self.get_logger().info('목표가 서버에 의해 거절되었습니다.')
            self.goal_reached = True
            
            return

        self.get_logger().info('목표가 수락되었습니다. 이동을 시작합니다.')
        
        self.goal_reached = False
        self.is_driving = True
        
        # 취소 요청을 위한 goal_handle 저장
        self._goal_handle = goal_handle
        
        # 최종 결과를 받기 위한 콜백 함수 등록
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)


    def get_result_callback(self, future):
        # 최종 도착 결과 확인
        result = future.result()
        status = result.status
        
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.goal_reached = True
            self.is_driving = False
            
            self.get_logger().info('목적지에 무사히 도착했습니다!')
        elif status == GoalStatus.STATUS_CANCELED:
            self.is_driving = False
            
            self.get_logger().info('사용자에 의해 경로가 취소되었습니다.')            
        else:
            pass

              
     # 경로 이동 취소 함수
    def cancel_goal(self):        
        if self._goal_handle is None:
            self.get_logger().warn("취소할 활성화된 목표(Goal)가 없습니다.")
            return
        
        self.get_logger().info("현재 이동 취소 요청 중...")

        # 서버에 비동기 취소 요청을 보내고, 완료 시 실행할 콜백 함수 지정
        cancel_future = self._goal_handle.cancel_goal_async()
        cancel_future.add_done_callback(self.cancel_done_callback)
    
    # 취소 요청 결과가 돌아왔을 때 처리하는 콜백
    def cancel_done_callback(self, future):
        cancel_response = future.result()
        
        # 취소 중인 목표 리스트가 존재한다면 성공적으로 접수 완료
        if len(cancel_response.goals_canceling) > 0:
            self.get_logger().info("이동이 성공적으로 취소되었습니다.")
            self._goal_handle = None
            self.is_driving = False
        else:
            self.get_logger().warn("이동 취소 요청이 거부되었습니다.")
            
    # 취소된 목표 위치로 이동 재개
    def resume_goal(self):
        self.is_canceled = False
        x, y, yaw = self.goal_pose
        
        self.get_logger().info(f"Resume Goal → ({x}, {y}, yaw={yaw})")
        self.send_goal(x, y, yaw)

def main():
    rclpy.init()
    node = NavigationTest()
    
     # spin을 별도 스레드에서 실행
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()
    
    print("키보드 입력 대기: 1~5 → 해당 위치 이동, c → 취소, q → 종료")

    while rclpy.ok():
        key = input("\n[1-5] Goal  [c] Cancel  [q] Quit : ")
        
        if key in sectors:
            x, y, w = sectors[key]
            node.send_goal(x, y, w)
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
        