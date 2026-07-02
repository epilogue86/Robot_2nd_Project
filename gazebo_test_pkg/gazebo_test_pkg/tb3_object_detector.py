import cv2
import rclpy
import socket

from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import CompressedImage

from ultralytics import YOLO
from cv_bridge import CvBridge
from pyzbar import pyzbar


SERVER_IP = "192.168.45.146"
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
            "/camera/image_raw/compressed",
            self.image_callback,
            10
        )
        
        # Yolo 처리 관련 변수    
        self.model = YOLO("/home/jonghun/ros2_ws/src/best.pt")
        self.detected_name = "Nothing"
        self.frame = None
        
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

        # self.get_logger().info("image_callback")

    
    def yolo_detect_timer(self):
        # self.get_logger().info("yolo_detect_timer")
        
        if self.frame is None:
            return
        
        frame = self.frame.copy()
        small_frame = cv2.resize(frame, (320, 240))
        results = self.model.predict(frame, conf=0.25, verbose=False)

        annotated_frame = results[0].plot()
        cv2.imshow("Object Detector", annotated_frame)
        
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
        
        last_detected_qr = self.last_detected_qr
        last_sent_qr = self.last_sent_qr
        frames_without_qr = self.frames_without_qr
        
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
                    self.qr_sock.sendto(packet_string.encode('utf-8'), (SERVER_IP, QR_UDP_PORT))
                    print(f"🎯 [QR SENT to 9092] -> \"{packet_string}\"")
                    
                    last_sent_qr = qr_raw_data
                else:
                    print(f"❌ [UNKNOWN QR] 미등록 QR 인식됨: {qr_raw_data}")
                                

    def camera_streaming_timer(self):
        # self.get_logger().info("camera_streaming_timer")
        
        if self.frame is None:
            return
        
        frame = self.frame.copy()    
        frame = cv2.resize(frame, (320, 240))
        ret, img_encode = cv2.imencode(".jpg", frame)
                        
        if not ret:
            return
        
        data_bytes = img_encode.tobytes()
            
        if len(data_bytes) <= PACKET_LIMIT:
            self.sock.sendto(data_bytes, (SERVER_IP, SERVER_PORT))
    
    
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