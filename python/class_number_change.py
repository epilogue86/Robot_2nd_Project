import os

# 대상 폴더 경로
folder_path = "dataset/labels/valid"

def fix_labels(path):
    for file in os.listdir(path):
        if file.endswith(".txt") and file.startswith("mannequin_"):
            fpath = os.path.join(path, file)
            with open(fpath, "r") as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                parts = line.strip().split()
                if parts:
                    parts[0] = "0"  # 클래스 번호를 0으로 변경
                    new_lines.append(" ".join(parts) + "\n")
            with open(fpath, "w") as f:
                f.writelines(new_lines)
            print(f"{file} 수정 완료")

fix_labels(folder_path)
print("모든 라벨 파일 수정 완료!")
