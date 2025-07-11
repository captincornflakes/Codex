import os
import json
import shutil

def create_album_upload_folder(storage_directory, folder_name, album_name):
    album_path = os.path.join(storage_directory, folder_name, album_name)
    os.makedirs(album_path, exist_ok=True)
    return album_path

def list_album_upload_folders(storage_directory, folder_name):
    uploads_path = os.path.join(storage_directory, folder_name)
    if not os.path.isdir(uploads_path):
        return []
    return [
        name for name in os.listdir(uploads_path)
        if os.path.isdir(os.path.join(uploads_path, name))
    ]

def get_album_files_info(storage_directory, folder_name, album_name):
    album_path = os.path.join(storage_directory, folder_name, album_name)
    if not os.path.isdir(album_path):
        return json.dumps([])

    files_info = []
    for filename in os.listdir(album_path):
        file_path = os.path.join(album_path, filename)
        if os.path.isfile(file_path):
            file_info = {
                "name": filename,
                "type": os.path.splitext(filename)[1][1:],  # extension without dot
                "size": os.path.getsize(file_path),
                "is_folder": False
            }
            files_info.append(file_info)
        elif os.path.isdir(file_path):
            folder_info = {
                "name": filename,
                "type": "folder",
                "size": None,
                "is_folder": True
            }
            files_info.append(folder_info)
    return json.dumps(files_info, indent=4)

def delete_album_upload_folder(storage_directory, folder_name, album_name):
    album_path = os.path.join(storage_directory, folder_name, album_name)
    if os.path.isdir(album_path):
        shutil.rmtree(album_path)
        return True
    return False

def delete_file_in_album(storage_directory, folder_name, album_name, filename):
    file_path = os.path.join(storage_directory, folder_name, album_name, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)
        return True
    return False