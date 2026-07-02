import cv2
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from ultralytics import YOLO


class PersonDetector(Node):
    def __init__(self):
        super().__init__('person_detector')
        self.pub = self.create_publisher(Bool, '/person_detected', 10)
        self.cap = cv2.VideoCapture(0)
        self.model = YOLO("yolov8n.pt")  # 사전학습된 YOLOv8n 모델

    def loop(self):
        while rclpy.ok():
            ret, frame = self.cap.read()
            if not ret:
                continue

            results = self.model.predict(frame, conf=0.25)
            person_detected = False

            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls.item())
                    if cls_id == 0:  # 0 = person
                        person_detected = True

            # 토픽 발행
            self.pub.publish(Bool(data=person_detected))

            # 디버깅용 화면 표시
            annotated_frame = results[0].plot()
            cv2.imshow("Person Detector", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

def main():
    rclpy.init()
    node = PersonDetector()
    try:
        node.loop()
    except KeyboardInterrupt:
        pass
    node.cap.release()
    cv2.destroyAllWindows()
    rclpy.shutdown()

if __name__ == '__main__':
    main()