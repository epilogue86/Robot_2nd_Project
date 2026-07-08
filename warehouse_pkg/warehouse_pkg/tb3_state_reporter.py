#!/usr/bin/env python3
import rclpy
import os
import socket
import math

from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import BatteryState
from std_msgs.msg import String


# SERVER_IP = "192.168.0.37"
SERVER_IP = "192.168.0.33"
# SERVER_IP = "192.168.45.146"

ROBOT_UDP_PORT = 9000

FILE_PATH = "/home/jonghun/ros2_ws/src/warehouse_pkg/warehouse_pkg/target_zone.txt"



class Tb3StateReporter(Node):
    def __init__(self):
        super().__init__('tb3_state_reporter')
        self.x, self.y, self.z = 0.0, 0.0, 0.0
        self.linear_vel, self.angular_vel = 0.0, 0.0
        self.battery_percent = 0.0
        self.target_zone = "-"
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_addr = (SERVER_IP, ROBOT_UDP_PORT)

        self.amcl_pose_sub = self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.amcl_pose_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.battery_sub = self.create_subscription(BatteryState, '/battery_state', self.battery_callback, 10)
        self.target_sub = self.create_subscription(String, '/target_sector', self.target_zone_callback, 10)
        
        self.log_timer = self.create_timer(0.1, self.update_and_send)
        

    def amcl_pose_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.z = msg.pose.pose.position.z
        

    def odom_callback(self, msg):
        self.linear_vel = msg.twist.twist.linear.x
        self.angular_vel = msg.twist.twist.angular.z


    def battery_callback(self, msg):
        self.battery_percent = msg.percentage


    def target_zone_callback(self, msg):
        self.target_zone = msg.data
        self.get_logger().info(f"목표 구역 업데이트 됨: {self.target_zone}")
        
        
    def update_and_send(self):
        # 💡 파일에서 현재 구역명을 안전하게 읽어옵니다.
        target_zone = "-"

        try:
            with open(FILE_PATH, "r") as f:
                target_zone = f.read().strip()
        except FileNotFoundError:
            # 파일이 없으면 기본값("-" 등)을 유지하고 경고만 출력
            self.get_logger().warn(f"파일을 찾을 수 없습니다: {FILE_PATH}. 기본값을 사용합니다.")
        
        is_moving = "1" if abs(self.linear_vel) > 0.01 or abs(self.angular_vel) > 0.01 else "0"
        packet_string = f"{self.x:.2f} {self.y:.2f} {self.z:.2f} {is_moving} {target_zone} {int(self.battery_percent)} {self.linear_vel:.2f} {self.angular_vel:.2f}"
        
        try:
            self.sock.sendto(packet_string.encode('utf-8'), self.server_addr)
        except:
            pass

        os.system('clear')
        print("==================================================")
        print("        🤖 TURTLEBOT 3 실시간 관제 모니터 로그        ")
        print("==================================================")
        print(f" 🔋 배터리 잔량      : {self.battery_percent:.1f} %")
        print("--------------------------------------------------")
        print(f" 🚀 주행 상태        : {'MOVING' if is_moving == '1' else 'STOPPED'}")
        print(f" 👉 스마트폰 목표구역  : {target_zone} 구역")
        print("==================================================")
        print(f" 📡 [UDP PORT 9000 SEND] -> {packet_string}")


def main(args=None):
    rclpy.init(args=args)
    logger = Tb3StateReporter()
    
    try:
        rclpy.spin(logger)
    except KeyboardInterrupt:
        pass
    finally:
        logger.sock.close()
        logger.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
