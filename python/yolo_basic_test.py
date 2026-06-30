import cv2
from ultralytics import YOLO

# YOLO 모델 불러오기 (COCO dataset 학습된 기본 모델)
model = YOLO("yolov8n.pt")  # 작은 모델, 빠른 속도

# 웹캠 열기
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # YOLO 추론
    results = model.predict(frame)

    for box in results[0].boxes:
        xyxy = box.xyxy.cpu().numpy()   # bounding box 좌표 (x1, y1, x2, y2)
        conf = box.conf.cpu().numpy()   # confidence score
        cls = int(box.cls.cpu().numpy()) # 클래스 ID
        label = results[0].names[cls]   # 클래스 이름
        
        # print(f"Detected {label} with {conf:.2f} confidence at {xyxy}")

    # 탐지 결과 시각화
    annotated_frame = results[0].plot()
    cv2.imshow("YOLO Webcam Detection", annotated_frame)

    # ESC 키 누르면 종료
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
