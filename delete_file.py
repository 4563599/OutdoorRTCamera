import os
import shutil


def clean_camera_folders():
    base_path = r"RT_text"

    folders = [
        r"atli_uploads\camera1",
        r"atli_uploads\camera2",
        r"atli_processed\camera1",
        r"atli_processed\camera2"
    ]

    for folder in folders:
        folder_path = os.path.join(base_path, folder)

        if not os.path.exists(folder_path):
            print(f"文件夹不存在: {folder_path}")
            continue

        try:
            # 删除文件夹内的所有内容
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)

                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

            print(f"已清空: {folder_path}")

        except Exception as e:
            print(f"处理 {folder_path} 时出错: {e}")


if __name__ == "__main__":
    clean_camera_folders()