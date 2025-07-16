import os
import zipfile
import shutil

def export_profile(storage_directory, folder_name, export_path):
    """
    Export a profile folder (including all files and subfolders) as a zip file.
    """
    folder_path = os.path.join(storage_directory, folder_name)
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Profile folder '{folder_path}' not found.")

    with zipfile.ZipFile(export_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, folder_path)
                zipf.write(abs_path, arcname=rel_path)
    return export_path

def import_profile(storage_directory, import_zip_path, folder_name=None):
    """
    Import a profile from a zip file. If folder_name is not provided, use the zip filename.
    """
    if not os.path.isfile(import_zip_path):
        raise FileNotFoundError(f"Zip file '{import_zip_path}' not found.")

    if folder_name is None:
        folder_name = os.path.splitext(os.path.basename(import_zip_path))[0]

    dest_folder = os.path.join(storage_directory, folder_name)
    if os.path.exists(dest_folder):
        raise FileExistsError(f"Destination folder '{dest_folder}' already exists.")

    os.makedirs(dest_folder, exist_ok=True)
    with zipfile.ZipFile(import_zip_path, "r") as zipf:
        zipf.extractall(dest_folder)
    return dest_folder

def list_profiles(storage_directory):
    """
    List all profile folders in the storage directory.
    """
    return [
        name for name in os.listdir(storage_directory)
        if os.path.isdir(os.path.join(storage_directory, name))
    ]