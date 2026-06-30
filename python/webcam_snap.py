import cv2
import os

# ==========================
# 저장 플래그
# ==========================
save_image = False


def mouse_callback(event, x, y, flags, param):
    """마우스 이벤트 처리"""
    global save_image

    # 가운데 버튼 클릭
    if event == cv2.EVENT_MBUTTONDOWN:
        save_image = True


# ==========================
# 웹캠 열기
# ==========================
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    exit()

# ==========================
# 저장 폴더 생성
# ==========================
base_dir = os.path.dirname(os.path.abspath(__file__))
save_dir = os.path.join(base_dir, "capture")
os.makedirs(save_dir, exist_ok=True)

# ==========================
# 다음 파일 번호 찾기
# ==========================
count = 1

while os.path.exists(os.path.join(save_dir, f"{count:03d}.jpg")):
    count += 1

# ==========================
# 윈도우 생성 및 마우스 이벤트 등록
# ==========================
window_name = "Camera"

cv2.namedWindow(window_name)
cv2.setMouseCallback(window_name, mouse_callback)

# ==========================
# 메인 루프
# ==========================
while True:

    ret, frame = cap.read()

    if not ret:
        print("프레임을 읽을 수 없습니다.")
        break

    # 현재 저장된 장수 표시
    cv2.putText(
        frame,
        f"Count : {count - 1}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        2
    )

    cv2.imshow(window_name, frame)

    key = cv2.waitKey(1) & 0xFF

    # 종료
    if key == ord('q') or key == 27:
        break

    # 스페이스바 촬영
    if key == 32:
        save_image = True

    # 저장
    if save_image:
        filename = os.path.join(save_dir, f"{count:03d}.jpg")

        cv2.imwrite(filename, frame)

        print(f"저장 완료 : {filename}")

        count += 1
        save_image = False

# ==========================
# 종료
# ==========================
cap.release()
cv2.destroyAllWindows()