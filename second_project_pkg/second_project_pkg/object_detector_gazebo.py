import cv2
import rclpy

from rclpy.node import Node
from std_msgs.msg import String
from ultralytics import YOLO

from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge


class ObjectDetector(Node):
    def __init__(self):
        super().__init__('object_detector')
        
        self.pub = self.create_publisher(String, '/object_detected', 10)
        self.timer = self.create_timer(0.1, self.publish_result)
        
        self.bridge = CvBridge()

        self.subscription = self.create_subscription(
            CompressedImage,
            "/camera/image_raw/compressed",
            self.image_callback,
            10
        )
        
        model_path = "/home/jonghun/ros2_ws/src/second_project_pkg/second_project_pkg/best.pt"
        self.model = YOLO(model_path)

        self.detected_name = "Nothing"

    
    def image_callback(self, msg):
        frame = self.bridge.compressed_imgmsg_to_cv2(msg, desired_encoding="bgr8")

        self.detect(frame)

                    
    def detect(self, frame):
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
                    return


    def publish_result(self):
        msg = String()
        msg.data = self.detected_name

        self.pub.publish(msg)


def main():
    rclpy.init()
    node = ObjectDetector()
    
    try:
        rclpy.spin(node)
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()
    

if __name__ == '__main__':
    main()