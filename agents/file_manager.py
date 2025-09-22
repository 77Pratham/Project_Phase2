# agents/file_manager.py
import os
import shutil

def list_files(directory):
    try:
        files = os.listdir(directory)
        return files if files else ["No files found."]
    except Exception as e:
        return [f"Error: {e}"]

def create_folder(folder_path):
    try:
        os.makedirs(folder_path, exist_ok=True)
        return f"Folder created at {folder_path}"
    except Exception as e:
        return f"Error: {e}"

def move_file(source, destination):
    try:
        shutil.move(source, destination)
        return f"Moved {source} to {destination}"
    except Exception as e:
        return f"Error: {e}"
