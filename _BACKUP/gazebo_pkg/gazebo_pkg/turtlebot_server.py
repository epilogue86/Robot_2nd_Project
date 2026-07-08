import socket
import sys
import subprocess
import psutil
import json
import os
import threading  # 💡 키보드 감시와 스마트폰 수신을 동시 처리하기 위해 추가

# 🎯 C++ 구조체(ZonePose)를 파이썬 딕셔너리로 매핑한 설정 데이터
ZONE_POSES = {
    "A": {"x":  0.66, "y":  1.62, "z": 0.0, "w": 1.0},
    "B": {"x":  0.84, "y": -0.92, "z": 0.0, "w": 1.0},
    "C": {"x": -0.40, "y": -0.86, "z": 0.0, "w": 1.0},
    "D": {"x": -0.82, "y":  1.47, "z": 0.0, "w": 1.0}
}

is_running = True  # 프로그램 작동 플래그

def save_zone_to_file(zone_name):
    """현재 목표 구역을 임시 텍스트 파일에 안전하게 저장"""
    try:
        with open("/tmp/target_zone.txt", "w") as f:
            f.write(zone_name)
    except Exception as e:
        print(f"[FILE ERROR] 구역 파일 저장 실패: {e}")

def send_goal(zone_name):
    if zone_name not in ZONE_POSES:
        print(f"[ERROR] 존재하지 않는 구역입니다: {zone_name}")
        return

    save_zone_to_file(zone_name)
    target = ZONE_POSES[zone_name]
    
    print("\n=========================================")
    print(f"[🚨 NAVIGATION] {zone_name}구역 목표 설정 및 전송 (비동기)")
    print("=========================================")

    goal_data = {
        "pose": {
            "header": {"frame_id": "map"},
            "pose": {
                "position": {"x": target["x"], "y": target["y"], "z": 0.0},
                "orientation": {"z": target["z"], "w": target["w"]}
            }
        }
    }
    goal_msg_string = json.dumps(goal_data)

    env = os.environ.copy()
    env["ROS_DOMAIN_ID"] = "1"
    env["TURTLEBOT3_MODEL"] = "waffle_pi"
    env["ROS_LOCALHOST_ONLY"] = "0"

    ros_command = (
        f"/opt/ros/humble/bin/ros2 action send_goal /navigate_to_pose "
        f"nav2_msgs/action/NavigateToPose '{goal_msg_string}'"
    )

    try:
        # 💡 Popen 비동기 방식으로 딜레이 없이 백그라운드로 즉각 송신
        subprocess.Popen(["bash", "-c", ros_command], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[LAUNCHED] {zone_name}구역 액션 명령이 대시보드 및 Nav2로 도달했습니다.")
    except Exception as e:
        print(f"[SYSTEM ERROR] 예외 발생: {e}")

class Goal:
    def move_A(self): send_goal("A")
    def move_B(self): send_goal("B")
    def move_C(self): send_goal("C")
    def move_D(self): send_goal("D")

def print_local_ips():
    print("[INFO] 현재 터틀봇의 접속 가능한 IP 주소 목록:")
    try:
        interfaces = psutil.net_if_addrs()
        for interface_name, interface_addresses in interfaces.items():
            if interface_name == 'lo': continue
            for address in interface_addresses:
                if address.family == socket.AF_INET:
                    print(f"   👉 [{interface_name}] {address.address}")
    except Exception as e: pass

def process_command(received_data, goal, source):
    """💡 입력받은 문자열(1~4)을 판별하여 로봇 이동 함수 매핑"""
    print(f"[{source}] 입력 신호 감지: {received_data}")
    if received_data == "1": goal.move_A()
    elif received_data == "2": goal.move_B()
    elif received_data == "3": goal.move_C()
    elif received_data == "4": goal.move_D()
    else:
        print(f"[INFO] 알 수 없는 명령 번호입니다: {received_data}")

def phone_socket_thread(server_sock, goal):
    """📱 별도의 백그라운드 스레드에서 스마트폰 패킷 수신을 상시 대기"""
    global is_running
    server_sock.settimeout(1.0)  # 1초 타임아웃 설정으로 종료 신호 주기적 체크
    
    while is_running:
        try:
            client_sock, client_addr = server_sock.accept()
            try:
                data = client_sock.recv(1024)
                if data:
                    received_data = data.decode('utf-8').strip()
                    process_command(received_data, goal, f"PHONE ({client_addr[0]})")
            except Exception as e: pass
            finally:
                client_sock.close()
        except socket.timeout:
            continue
        except Exception as e:
            break

def main():
    global is_running
    save_zone_to_file("-")
    goal = Goal()
    port = 8080
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try: server_sock.bind(('', port))
    except Exception as e:
        print(f"[CRITICAL] 포트 바인딩 오류: {e}")
        server_sock.close()
        return -1

    server_sock.listen(5)
    
    print("==================================================")
    print("   📱 스마트폰 패킷 & ⌨️ 터미널 키보드 입력 통합 서버   ")
    print("==================================================")
    print_local_ips()
    print(f"   📌 수신 대기 포트: {port}")
    print("   👉 조작방법 1: 스마트폰 앱에서 패킷 송신")
    print("   👉 조작방법 2: 이 터미널에서 숫자 1, 2, 3, 4 입력 후 [엔터]")
    print("   ❌ 프로그램 종료: 'q' 입력 후 [엔터] 또는 Ctrl+C")
    print("==================================================")

    # 1. 백그라운드 스레드로 스마트폰 통신망 가동
    client_thread = threading.Thread(target=phone_socket_thread, args=(server_sock, goal))
    client_thread.daemon = True
    client_thread.start()

    # 2. 메인 스레드는 터미널 창의 키보드 입력(sys.stdin) 상시 대기
    try:
        while is_running:
            # 사용자가 키보드를 치고 엔터를 누를 때까지 블로킹
            user_input = sys.stdin.readline().strip()
            
            if user_input.lower() == 'q':
                print("[INFO] 종료 명령('q')이 입력되었습니다.")
                break
                
            if user_input:
                process_command(user_input, goal, "KEYBOARD")
                
    except KeyboardInterrupt:
        print("\n[INFO] 강제 종료 신호(Ctrl+C)가 감지되었습니다.")
    finally:
        is_running = False
        server_sock.close()
        print("[INFO] 서버가 안전하게 폐쇄되었습니다.")

if __name__ == "__main__":
    main()