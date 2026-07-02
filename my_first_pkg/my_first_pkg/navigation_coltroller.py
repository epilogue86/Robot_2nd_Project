#!/usr/bin/env python3
import rclpy
import math
import threading

from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import Twist
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import Bool


class NavigationController(Node):

    def __init__(self):
        super().__init__('navigation_controller')

        # Navigation2 액션 클라이언트
        self.client = ActionClient(self, NavigateToPose,'/navigate_to_pose')
        
        # 사람 감지 토픽 구독
        self.sub = self.create_subscription(Bool, '/person_detected', self.person_callback, 10)

        # 정지를 위한 cmd 퍼블리셔
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # 목적지 정의
        self.goals = {
            "1": (-1.8,  1.8,  0.0),  # A
            "2": ( 1.8,  1.8,  0.0),  # B
            "3": ( 1.8, -1.8,  0.0),  # C
            "4": (-1.8, -1.8,  0.0),  # D
            "5": ( 0.0, -0.75, 0.0),  # HOME
        }
        
        self.goal_handle = None
        self.goal_pose = None
        self.is_person_detected = False
        self.resume_timer = None

        self.get_logger().info("Navigation Controller Ready")

        # 키보드 입력을 별도 쓰레드에서 실행
        thread = threading.Thread(target=self.keyboard_loop)
        thread.daemon = True
        thread.start()

    # yaw → quaternion
    def yaw_to_quaternion(self, yaw):
        half = yaw / 2.0
        qz = math.sin(half)
        qw = math.cos(half)
        return (0.0, 0.0, qz, qw)
    
    # Goal 전송
    def send_goal(self, x, y, yaw):
        self.client.wait_for_server()
        self.goal_pose = (x, y, yaw)

        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = "map"
        goal.pose.header.stamp = self.get_clock().now().to_msg()

        goal.pose.pose.position.x = float(x)
        goal.pose.pose.position.y = float(y)
        goal.pose.pose.position.z = 0.0

        q = self.yaw_to_quaternion(yaw)
        goal.pose.pose.orientation.x = q[0]
        goal.pose.pose.orientation.y = q[1]
        goal.pose.pose.orientation.z = q[2]
        goal.pose.pose.orientation.w = q[3]

        future = self.client.send_goal_async(goal)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.get_logger().info("Goal Rejected")
            return
        self.get_logger().info("Goal Accepted")
        result_future = self.goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def result_callback(self, future):
        self.get_logger().info("Goal Finished")
        self.goal_handle = None

    def cancel_goal(self):
        self.get_logger().info(f"Cancel Goal!! handle={self.goal_handle}")
        if self.goal_handle is None:
            self.get_logger().info("No Active Goal to Cancel")
            return
        self.get_logger().info("Cancel Specific Goal")
        future = self.goal_handle.cancel_goal_async()
        future.add_done_callback(self.cancel_done)


    def cancel_done(self, future):
        self.get_logger().info("Goal Cancel Complete")
        self.goal_handle = None

    def stop_robot(self):
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        self.cmd_pub.publish(twist)
        self.get_logger().info("로봇 정지")

    # 사람 감지 콜백
    def person_callback(self, msg):
        self.get_logger().info(f"사람 감지 여부: {msg.data}")
        if msg.data:
            # 사람이 감지됨 → 즉시 취소 + 정지
            self.cancel_goal()
            self.stop_robot()
            self.is_person_detected = True

            # 기존 타이머가 있으면 취소
            if self.resume_timer:
                self.resume_timer.cancel()
                self.resume_timer = None

        else:
            # 사람이 사라짐 → 일정 시간 후 재개
            if self.is_person_detected:
                self.is_person_detected = False
                if self.goal_pose:
                    # 3초 후 resume_goal 실행
                    self.resume_timer = self.create_timer(3.0, self.resume_goal)

    def resume_goal(self):
        if not self.is_person_detected and self.goal_pose:
            x, y, yaw = self.goal_pose
            self.get_logger().info(f"Resume Goal → ({x}, {y}, yaw={yaw})")
            self.send_goal(x, y, yaw)
        if self.resume_timer:
            self.resume_timer.cancel()
            self.resume_timer = None

    # 키보드 입력 루프 (쓰레드에서 실행)
    def keyboard_loop(self):
        while rclpy.ok():
            key = input("\n[1-5] Goal  [c] Cancel  [q] Quit : ")
            if key in self.goals:
                x, y, yaw = self.goals[key]
                self.send_goal(x, y, yaw)
            elif key == "c":
                self.cancel_goal()
            elif key == "q":
                rclpy.shutdown()
                break


def main():
    rclpy.init()
    node = NavigationController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
