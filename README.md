# Codex

Codex is a documentation software designed for profiling people, with support for organizing albums of files (such as images, videos, and documents) for each profile. It provides a graphical user interface for managing personal information and associated media.

## Features

- Create and manage multiple profiles, each stored in its own folder.
- Store detailed profile information, including display name, real name, phone number, address, emails, social media links, and notes.
- Organize files into albums for each profile, supporting images, videos, and other file types.
- Preview images and videos directly within the application.
- Export or delete files from albums.
- Simple and intuitive Tkinter-based GUI.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- [Pillow](https://pypi.org/project/Pillow/) (for image previews)
- [python-vlc](https://pypi.org/project/python-vlc/) (for video previews, optional)

Install dependencies with:

```sh
pip install Pillow python-vlc
```

### Running the Application

Run the main script:

```sh
python profiler.py
```

This will launch the GUI.

## Usage

1. **Create a Storage Folder:**  
   Click "New" next to the Storage Folder dropdown to create a new profile.

2. **Edit Profile Information:**  
   Fill in the profile fields on the left side of the window.

3. **Save Profile:**  
   Click "Save" to store the profile data.

4. **Create Albums:**  
   Select a profile, then click "New Album" to create an album for organizing files.

5. **Upload Files:**  
   Select an album and use "Upload File" to add images, videos, or documents.

6. **Preview and Manage Files:**  
   Click on files in an album to preview, export, or delete them.

## Project Structure

- `profiler.py` — Main entry point for the application.
- `utils/` — Contains modules for GUI, file management, storage, and settings.
- `storage/` — Default directory where profile folders and albums are stored.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Author

TearsOfAnEcho

