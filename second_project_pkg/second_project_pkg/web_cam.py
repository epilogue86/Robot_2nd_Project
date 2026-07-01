#!/usr/bin/env python3
import socket
import sys
import time
import cv2
from pyzbar import pyzbar

# 📡 서버 및 포트 설정
SERVER_IP = "192.168.0.37"
VIDEO_UDP_PORT = 9091
QR_UDP_PORT = 9092  
PACKET_LIMIT = 65000

# 📦 QR 코드 데이터에 매핑할 고정 상품 정보 (ID, 상품명, 총 재고량)
PRODUCT_MASTER = {
    "1": {"id": "1", "name": "A", "total": "10"},
    "2": {"id": "2", "name": "B", "total": "10"},
    "3": {"id": "3", "name": "C", "total": "10"},
    "4": {"id": "4", "name": "D", "total": "10"}
}

def main():
    # 1. UDP 소켓 생성 (비디오 스트리밍용, QR 전송용)
    try:
        video_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        qr_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error as e:
        print(f"[ERROR] 소켓 생성 실패: {e}")
        return -1

    video_addr = (SERVER_IP, VIDEO_UDP_PORT)
    qr_addr = (SERVER_IP, QR_UDP_PORT)

    # 2. 웹캠 초기화 및 설정
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] 웹캠을 열 수 없습니다.")
        return -1

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 400)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 300)
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 40] # JPEG 압축률 40%

    # 중복 감지 방지 변수들
    last_detected_qr = ""  
    last_sent_qr = ""      
    frames_without_qr = 0

    print("==================================================")
    print(" 📸 터틀봇 비전 및 QR 관제 클라이언트 가동 중...")
    print("   👉 [PORT 9091] 실시간 영상 스트리밍")
    print("   👉 [PORT 9092] 실시간 QR 상품 정보 전송")
    print("==================================================")

    try:
        while True:
            # --- 파트 1: 웹캠 프레임 획득 ---
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            # --- 파트 2: pyzbar QR 코드 인식 ---
            decoded_objects = pyzbar.decode(frame)
            if not decoded_objects:
                frames_without_qr += 1
                if frames_without_qr > 15:
                    last_detected_qr = ""  # QR이 화면에서 사라지면 리셋
            else:
                frames_without_qr = 0

            for obj in decoded_objects:
                qr_raw_data = obj.data.decode('utf-8').strip()
                
                if qr_raw_data != last_detected_qr:
                    last_detected_qr = qr_raw_data
                    
                    # 마스터 데이터에 등록된 상품(1~4)인지 검증
                    if qr_raw_data in PRODUCT_MASTER:
                        if qr_raw_data == last_sent_qr:
                            print(f"⚠️ [BLOCK] 상품 {qr_raw_data}번 연속 감지 차단")
                            continue  
                        
                        # 해당 QR의 매핑 데이터 가져오기
                        prod = PRODUCT_MASTER[qr_raw_data]
                        
                        # 🎯 [요구사항 반영] 상품 ID, 상품명, 수량 패킷 조립 ("1 A 10")
                        packet_string = f"{prod['id']} {prod['name']} {prod['total']}"
                        
                        # 9092번 포트로 패킷 전송 (차감 로직 없음)
                        qr_sock.sendto(packet_string.encode('utf-8'), qr_addr)
                        print(f"🎯 [QR SENT to 9092] -> \"{packet_string}\"")
                        
                        last_sent_qr = qr_raw_data
                    else:
                        print(f"❌ [UNKNOWN QR] 미등록 QR 인식됨: {qr_raw_data}")

            # --- 파트 3: UDP 비디오 스트리밍 전송 (9091) ---
            ret_code, img_encode = cv2.imencode('.jpg', frame, encode_params)
            if ret_code:
                data_bytes = img_encode.tobytes()
                if len(data_bytes) <= PACKET_LIMIT:
                    video_sock.sendto(data_bytes, video_addr)

            # 초당 대략 30프레임 주기를 위한 딜레이
            time.sleep(0.033)

    except KeyboardInterrupt:
        print("\n[INFO] 사용자에 의해 프로그램을 종료합니다.")
    finally:
        cap.release()
        video_sock.close()
        qr_sock.close()
        print("[INFO] 모든 소켓 및 웹캠 자원이 안전하게 해제되었습니다.")

if __name__ == "__main__":
    main()