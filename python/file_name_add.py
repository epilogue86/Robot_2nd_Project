import os

# 대상 폴더 경로
folder_path = "capture(QR_Code)"   # 원하는 폴더 경로로 변경하세요
prefix = "qr_code_"                         # 붙이고 싶은 단어

def rename_files(path, prefix):
    for filename in os.listdir(path):
        old_path = os.path.join(path, filename)
        if os.path.isfile(old_path):
            new_name = prefix + filename
            new_path = os.path.join(path, new_name)
            os.rename(old_path, new_path)
            print(f"{filename} → {new_name}")

rename_files(folder_path, prefix)
print("파일 이름 변경 완료!")
