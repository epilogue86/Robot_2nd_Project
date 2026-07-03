#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import BatteryState
import os
import socket
import math

SERVER_IP = "192.168.0.33"  
ROBOT_UDP_PORT = 9000

class RobotLogger(Node):
    def __init__(self):
        super().__init__('robot_logger')
        self.x, self.y, self.z = 0.0, 0.0, 0.0
        self.linear_vel, self.angular_vel = 0.0, 0.0
        self.battery_percent = 0.0

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_addr = (SERVER_IP, ROBOT_UDP_PORT)

        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.battery_sub = self.create_subscription(BatteryState, '/battery_state', self.battery_callback, 10)
        self.log_timer = self.create_timer(0.2, self.update_and_send)

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        self.z = msg.pose.pose.position.z
        self.linear_vel = msg.twist.twist.linear.x
        self.angular_vel = msg.twist.twist.angular.z

    def battery_callback(self, msg):
        if math.isnan(msg.percentage):
            raw_percent = 0.0
        else:
            raw_percent = msg.percentage

        if 0.0 < raw_percent <= 1.0:
            self.battery_percent = raw_percent * 100.0
        elif raw_percent > 1.0:
            self.battery_percent = raw_percent
        else:
            if msg.voltage > 0:
                calc_percent = ((msg.voltage - 11.1) / (12.6 - 11.1)) * 100.0
                self.battery_percent = max(0.0, min(100.0, calc_percent))
            else:
                self.battery_percent = 0.0

    def update_and_send(self):
        # 💡 파일에서 현재 구역명을 안전하게 읽어옵니다.
        target_zone = "-"
        if os.path.exists("/tmp/target_zone.txt"):
            try:
                with open("/tmp/target_zone.txt", "r") as f:
                    target_zone = f.read().strip()
            except:
                target_zone = "-"

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
        print(f" 🔋 배터리 잔량 : {self.battery_percent:.1f} %")
        print("--------------------------------------------------")
        print(f" 🚀 주행 상태        : {'MOVING' if is_moving == '1' else 'STOPPED'}")
        print(f"    👉 스마트폰 목표구역 : {target_zone} 구역")
        print("==================================================")
        print(f" 📡 [UDP PORT 9000 SEND] -> {packet_string}")

def main(args=None):
    rclpy.init(args=args)
    logger = RobotLogger()
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
