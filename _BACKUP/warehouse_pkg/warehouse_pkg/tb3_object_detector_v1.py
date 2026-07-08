import cv2
import rclpy
import socket

from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import CompressedImage

from ultralytics import YOLO
from cv_bridge import CvBridge
from pyzbar import pyzbar


SERVER_IP = "192.168.0.37"
SERVER_PORT = 9091
QR_UDP_PORT = 9092
PACKET_LIMIT = 65000


# 📦 QR 코드 데이터에 매핑할 고정 상품 정보 (ID, 상품명, 총 재고량)
PRODUCT_MASTER = {
    "1": {"id": "1", "name": "A", "total": "10"},
    "2": {"id": "2", "name": "B", "total": "10"},
    "3": {"id": "3", "name": "C", "total": "10"},
    "4": {"id": "4", "name": "D", "total": "10"}
}


class Tb3ObjectDetector(Node):
    def __init__(self):
        super().__init__('tb3_object_detector')
        
        self.pub = self.create_publisher(String, '/object_detected', 10)
        
        self.bridge = CvBridge()

        self.subscription = self.create_subscription(
            CompressedImage,
            "/image_raw/compressed",
            self.image_callback,
            10
        )
        
        # Yolo 처리 관련 변수    
        self.model = YOLO("/home/jonghun/ros2_ws/src/best.pt")
        self.detected_name = "Nothing"
        self.frame = None
        self.annotated_frame = None  
        
        cv2.namedWindow("Object Detector", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Object Detector", 480, 320)
        
        # QR Code 처리 관련 변수
        self.last_detected_qr = ""  
        self.last_sent_qr = ""      
        self.frames_without_qr = 0
    
        # 관제페이지에 데이터 전송을 위한 통신 변수
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.qr_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # 타이머 생성
        self.yolo_timer = self.create_timer(0.1, self.yolo_detect_timer)
        self.qr_timer = self.create_timer(0.2, self.qr_detect_timer)
        self.streaming_timer = self.create_timer(0.05, self.camera_streaming_timer)
        
        self.get_logger().info("tb3 Object Detector Ready")

    
    def image_callback(self, msg):
        self.frame = self.bridge.compressed_imgmsg_to_cv2(msg, desired_encoding="bgr8")

                    
    def yolo_detect_timer(self):
        if self.frame is None:
            return
        
        frame = self.frame.copy()
        small_frame = cv2.resize(frame, (320, 240))
        results = self.model.predict(small_frame, conf=0.25, verbose=False)

        self.annotated_frame = results[0].plot()  
        cv2.imshow("Object Detector", self.annotated_frame)
        
        key = cv2.waitKey(1)
        
        if key & 0xFF == 27:
            self.get_logger().info("ESC pressed. Shutting down.")
            cv2.destroyAllWindows()
            rclpy.shutdown()
            return
        
        self.detected_name = "Nothing"
        
        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                label = self.model.names[cls]

                if label == "mannequin":
                    self.detected_name = "Mannequin"
                    break
            
            if self.detected_name == "Mannequin":
                break

        msg = String()
        msg.data = self.detected_name
        self.pub.publish(msg)


    def qr_detect_timer(self):
        if self.frame is None:
            return
        
        frame = self.frame.copy()
        decoded_objects = pyzbar.decode(frame)
        
        if not decoded_objects:
            self.frames_without_qr += 1
            if self.frames_without_qr > 15:
                self.last_detected_qr = ""  
        else:
            self.frames_without_qr = 0
        
        for obj in decoded_objects:
            qr_raw_data = obj.data.decode('utf-8').strip()
            
            if qr_raw_data != self.last_detected_qr:
                self.last_detected_qr = qr_raw_data
                
                if qr_raw_data in PRODUCT_MASTER:
                    if qr_raw_data == self.last_sent_qr:
                        print(f"⚠️ [BLOCK] 상품 {qr_raw_data}번 연속 감지 차단")
                        continue  
                    
                    prod = PRODUCT_MASTER[qr_raw_data]
                    packet_string = f"{prod['id']} {prod['name']} {prod['total']}"
                    
                    self.qr_sock.sendto(packet_string.encode('utf-8'), (SERVER_IP, QR_UDP_PORT))
                    print(f"🎯 [QR SENT to 9092] -> \"{packet_string}\"")
                    
                    self.last_sent_qr = qr_raw_data
                else:
                    print(f"❌ [UNKNOWN QR] 미등록 QR 인식됨: {qr_raw_data}")
                                

    def camera_streaming_timer(self):
        """
        🚀 [수정] 서버(server.js) 규격에 맞춰 플래그('Y', 'R')를 접두어로 붙여 송신하는 로직
        """
        if self.frame is None:
            return
        
        # JPEG 압축 화질 설정 (패킷 용량 제한 65000 바이트 방어 안전장치)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 75]

        # 1️⃣ [RIGHT CAM] 원본 웹캠 스트리밍 데이터 조립 및 전송 (플래그: R)
        raw_small = cv2.resize(self.frame.copy(), (320, 240))
        ret_raw, img_encode_raw = cv2.imencode(".jpg", raw_small, encode_param)
        
        if ret_raw:
            # 바이너리 맨 앞에 문자 'R'을 바이트 형태로 결합
            raw_bytes = b'R' + img_encode_raw.tobytes()
            if len(raw_bytes) <= PACKET_LIMIT:
                self.sock.sendto(raw_bytes, (SERVER_IP, SERVER_PORT))

        # 2️⃣ [LEFT CAM] YOLO 가공 웹캠 스트리밍 데이터 조립 및 전송 (플래그: Y)
        if self.annotated_frame is not None:
            ret_yolo, img_encode_yolo = cv2.imencode(".jpg", self.annotated_frame, encode_param)
            
            if ret_yolo:
                # 바이너리 맨 앞에 문자 'Y'를 바이트 형태로 결합
                yolo_bytes = b'Y' + img_encode_yolo.tobytes()
                if len(yolo_bytes) <= PACKET_LIMIT:
                    self.sock.sendto(yolo_bytes, (SERVER_IP, SERVER_PORT))


def main():
    rclpy.init()
    node = Tb3ObjectDetector()
    
    try:
        rclpy.spin(node)
    finally:
        node.sock.close()
        node.qr_sock.close()
        cv2.destroyAllWindows()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()
    

if __name__ == '__main__':
    main()