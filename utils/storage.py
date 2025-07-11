import os
import json

DEFAULT_DATA = {
    "displayname": "",
    "realname": "",
    "phone_number": "",
    "address": "",
    "email":  [],
    "social_medias": [],
    "notes": ""
}

def list_subfolders(storage_directory):
    if not os.path.isdir(storage_directory):
        return []
    return [
        name for name in os.listdir(storage_directory)
        if os.path.isdir(os.path.join(storage_directory, name))
    ]

def create_storage_folder(storage_directory, folder_name, initial_data=None):
    path = os.path.join(storage_directory, folder_name)
    os.makedirs(path, exist_ok=True)
    data_path = os.path.join(path, "data.json")
    if initial_data is None:
        initial_data = {}
    # Merge defaults with any provided initial data
    data = {**DEFAULT_DATA, **initial_data}
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    return path

def delete_storage_folder(storage_directory, folder_name):
    import shutil
    path = os.path.join(storage_directory, folder_name)
    if os.path.isdir(path):
        shutil.rmtree(path)
        return True
    return False

def read_data_json(storage_directory, folder_name):
    data_path = os.path.join(storage_directory, folder_name, "data.json")
    if not os.path.isfile(data_path):
        return None
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

def update_data_json(storage_directory, folder_name, updates):
    data_path = os.path.join(storage_directory, folder_name, "data.json")
    data = {}
    if os.path.isfile(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.update(updates)
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    return data