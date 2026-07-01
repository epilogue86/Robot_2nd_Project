import os
import cv2
import rclpy

from rclpy.node import Node
from std_msgs.msg import String
from ultralytics import YOLO


class ObjectDetector(Node):
    def __init__(self):
        super().__init__('object_detector')
        
        self.pub = self.create_publisher(String, '/object_detected', 10)
        self.cap = cv2.VideoCapture(0)
        
        model_path = "/home/user/ros2_ws/src/second_project_pkg/second_project_pkg/best.pt"
        self.model = YOLO(model_path)

        
    def loop(self):
        while rclpy.ok():
            ret, frame = self.cap.read()
            
            if not ret:
                continue

            results = self.model.predict(frame, conf=0.25)
            detected_name = "Nothing"

            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls.item())
                    if cls_id == 0:         # 0 = mannequin
                        detected_name = "Mannequin"
                    elif cls_id == 1:       # 1 = QR Code
                        detected_name = "Qr_code"

            # 토픽 발행
            self.pub.publish(String(data = detected_name))

            # 디버깅용 화면 표시
            annotated_frame = results[0].plot()
            cv2.imshow("Object Detector", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

def main():
    rclpy.init()
    node = ObjectDetector()
    
    try:
        node.loop()
    except KeyboardInterrupt:
        pass
    
    node.cap.release()
    
    cv2.destroyAllWindows()
    rclpy.shutdown()

if __name__ == '__main__':
    main()