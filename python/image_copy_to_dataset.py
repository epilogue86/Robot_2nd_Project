import os
import random
import shutil

# 원본 폴더 (이미지와 라벨이 함께 들어있는 곳)
capture_dir = "capture"

# 출력 폴더
train_img_dir = "dataset/images/train"
valid_img_dir = "dataset/images/valid"
train_lbl_dir = "dataset/labels/train"
valid_lbl_dir = "dataset/labels/valid"

# 폴더 생성
for d in [train_img_dir, valid_img_dir, train_lbl_dir, valid_lbl_dir]:
    os.makedirs(d, exist_ok=True)

# 파일 목록 불러오기
files = [f for f in os.listdir(capture_dir) if f.endswith(".jpg")]
files.sort()

# 랜덤 섞기
random.shuffle(files)

# train/valid 비율 설정 (예: 80% train, 20% valid)
split_ratio = 0.8
split_index = int(len(files) * split_ratio)

train_files = files[:split_index]
valid_files = files[split_index:]

# 복사 함수
def copy_files(file_list, img_dest, lbl_dest):
    for f in file_list:
        # 이미지 복사
        shutil.copy(os.path.join(capture_dir, f), os.path.join(img_dest, f))
        # 라벨 파일 이름 맞추기
        label_file = f.replace(".jpg", ".txt")
        shutil.copy(os.path.join(capture_dir, label_file), os.path.join(lbl_dest, label_file))

# 실행
copy_files(train_files, train_img_dir, train_lbl_dir)
copy_files(valid_files, valid_img_dir, valid_lbl_dir)

print(f"Train: {len(train_files)} files, Valid: {len(valid_files)} files")
