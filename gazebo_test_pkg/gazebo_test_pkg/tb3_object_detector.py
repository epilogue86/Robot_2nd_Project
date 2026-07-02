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
PACKET_LIMIT = 65000


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
        
        # 관제페이지에 데이터 전송을 위한 통신 변수
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
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
        pass


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
        cv2.destroyAllWindows()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()
    

if __name__ == '__main__':
    main()