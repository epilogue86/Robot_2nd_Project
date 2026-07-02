#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
import math


class StableNavigator(Node):

    def __init__(self):
        super().__init__('stable_navigator')

        self.client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

        # 목적지
        self.goals = {
            "1": (-1.8,   1.8,  0.0),
            "2": ( 1.8,   1.8,  1.57),
            "3": ( 1.8,  -1.8,  3.14),
            "4": (-1.8,  -1.8, -1.57),
            "5": ( 0.03, -0.64, 0.0),
        }

        # 상태 관리
        self.goal_handle = None
        self.goal_active = False
        self.cancelling = False

        self.get_logger().info("Stable Navigator Ready")

    # ----------------------------------------
    # yaw → quaternion (안정 버전)
    # ----------------------------------------
    def yaw_to_quaternion(self, yaw):
        half = yaw / 2.0
        return (0.0, 0.0, math.sin(half), math.cos(half))

    # ----------------------------------------
    # Goal 전송
    # ----------------------------------------
    def send_goal(self, x, y, yaw):

        # cancel 중이면 새 goal 금지
        if self.cancelling:
            self.get_logger().info("[WAIT CANCEL COMPLETE]")
            return

        self.client.wait_for_server()

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

        # 상태 변경 (핵심)
        self.goal_active = True
        self.goal_handle = None

        self.get_logger().info(f"[SEND GOAL] ({x}, {y}, {yaw})")

        future = self.client.send_goal_async(goal)
        future.add_done_callback(self.goal_response_callback)

    # ----------------------------------------
    # Goal 응답
    # ----------------------------------------
    def goal_response_callback(self, future):

        handle = future.result()

        if not handle.accepted:
            self.get_logger().info("[GOAL REJECTED]")
            self.goal_active = False
            return

        self.goal_handle = handle
        self.goal_active = True

        self.get_logger().info("[GOAL ACCEPTED]")

    # ----------------------------------------
    # Goal 취소 (핵심 안정화 부분)
    # ----------------------------------------
    def cancel_goal(self):

        if not self.goal_active or self.goal_handle is None:
            self.get_logger().info("[NO ACTIVE GOAL]")
            return

        if self.cancelling:
            self.get_logger().info("[ALREADY CANCELLING]")
            return

        self.get_logger().info("[CANCEL REQUEST]")

        self.cancelling = True

        future = self.goal_handle.cancel_goal_async()
        future.add_done_callback(self.cancel_done)

    # ----------------------------------------
    # cancel 완료
    # ----------------------------------------
    def cancel_done(self, future):

        self.goal_active = False
        self.goal_handle = None
        self.cancelling = False

        self.get_logger().info("[CANCEL COMPLETE]")

    # ----------------------------------------
    # 입력 처리
    # ----------------------------------------
    def run(self):

        cmd = input("\n[1~5 이동] [c 취소] [q 종료] > ")

        # goal 실행
        if cmd in self.goals:

            # 이미 움직이고 있으면 먼저 cancel
            if self.goal_active:
                self.cancel_goal()
                return   # ⭐ 중요: cancel 완료 전에 send 금지

            x, y, yaw = self.goals[cmd]
            self.send_goal(x, y, yaw)

        # cancel
        elif cmd == "c":
            self.cancel_goal()

        # 종료
        elif cmd == "q":
            self.get_logger().info("Shutdown")
            rclpy.shutdown()


def main():

    rclpy.init()

    node = StableNavigator()

    while rclpy.ok():
        node.run()
        rclpy.spin_once(node, timeout_sec=0.1)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()