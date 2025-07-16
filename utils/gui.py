import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
import os
import shutil
import json
from utils.settings import load_settings
from utils.profile_transfer import export_profile, import_profile  # <-- Add this import
import threading

settings = load_settings()

class DocumenterApp:
    def __init__(self, master, settings, storage_utils=None, files_utils=None):
        self.master = master
        self.master.title("Documenter Program")
        self.master.geometry("1280x900")
        self.settings = settings

        # Optionally inject storage and files utils for easier testing
        if storage_utils is None:
            from utils import storage as storage_utils
        if files_utils is None:
            from utils import files as files_utils
        self.storage_utils = storage_utils
        self.files_utils = files_utils

        self.selected_folder = tk.StringVar(value="")  # Start blank
        self.selected_album = tk.StringVar(value="")   # Start blank
        self.profile_data = {}

        self.create_widgets()
        self.refresh_storage_folders()
        self.refresh_albums()

    def create_widgets(self):
        # --- Button Bar ---
        button_bar = tk.Frame(self.master)
        button_bar.pack(fill="x", padx=5, pady=5)

        # Storage folders dropdown
        tk.Label(button_bar, text="Storage Folder:").pack(side="left")
        self.folder_dropdown = ttk.Combobox(
            button_bar,
            textvariable=self.selected_folder,
            state="readonly",
            width=20
        )
        self.folder_dropdown.pack(side="left", padx=2)
        self.folder_dropdown.bind("<<ComboboxSelected>>", lambda e: [self.load_profile(), self.refresh_albums()])

        tk.Button(button_bar, text="New", command=self.new_storage_folder).pack(side="left", padx=2)
        tk.Button(button_bar, text="Load", command=self.load_profile).pack(side="left", padx=2)
        tk.Button(button_bar, text="Save", command=self.save_profile).pack(side="left", padx=2)

        # --- Export and Import buttons ---
        tk.Button(button_bar, text="Export", command=self.export_profile_gui).pack(side="left", padx=2)
        tk.Button(button_bar, text="Import", command=self.import_profile_gui).pack(side="left", padx=2)

        # Albums dropdown
        tk.Label(button_bar, text="Albums:").pack(side="left", padx=(20,2))
        self.album_dropdown = ttk.Combobox(
            button_bar,
            textvariable=self.selected_album,
            state="readonly",
            width=40
        )
        self.album_dropdown.pack(side="left", padx=2)
        self.album_dropdown.bind("<<ComboboxSelected>>", lambda e: self.load_album())  # <-- Load album on change

        tk.Button(button_bar, text="New Album", command=self.new_album).pack(side="left", padx=2)
        tk.Button(button_bar, text="Get Albums", command=self.refresh_albums).pack(side="left", padx=2)
        tk.Button(button_bar, text="Load Album", command=self.load_album).pack(side="left", padx=2)

        # About button
        tk.Button(button_bar, text="About", command=self.show_about).pack(side="right", padx=2)

        # --- Separator Line ---
        separator = tk.Frame(self.master, height=2, bg="black")
        separator.pack(fill="x", padx=0, pady=0)

        # --- Main Working Area with Vertical Divider ---
        main_area = tk.Frame(self.master)
        main_area.pack(fill="both", expand=True, padx=10, pady=10)

        # Left: Profile Area (40%)
        self.profile_area = tk.Frame(main_area)
        self.profile_area.pack(side="left", fill="both", expand=False, padx=(0, 5), pady=0)
        self.profile_area.pack_propagate(False)
        self.profile_area.config(width=int(self.master.winfo_screenwidth() * 0.50))

        # Vertical Divider
        divider = tk.Frame(main_area, width=2, bg="black")
        divider.pack(side="left", fill="y", padx=0, pady=0)

        # Right: Album Area (60%)
        self.album_area = tk.Frame(main_area)
        self.album_area.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=0)
        self.album_area.pack_propagate(False)
        self.album_area.config(width=int(self.master.winfo_screenwidth() * 0.50))

        # --- Profile fields (editable) in left area ---
        self.fields = {}
        field_names = [
            ("displayname", "Display Name"),
            ("realname", "Real Name"),
            ("phone_number", "Phone Number"),
            ("address", "Address"),
            ("email", "Email"),
            ("social_medias", "Social Medias"),
            ("notes", "Notes"),
        ]
        for idx, (key, label) in enumerate(field_names):
            tk.Label(self.profile_area, text=label + ":").grid(row=idx, column=0, sticky="ne", pady=2)
            if key == "notes":
                entry = tk.Text(self.profile_area, height=20, width=60)  # Wider notes section
                entry.grid(row=idx, column=1, sticky="w", pady=2)
                self.fields[key] = entry
            elif key in ("email", "social_medias"):
                frame = tk.Frame(self.profile_area)
                frame.grid(row=idx, column=1, sticky="w", pady=2)
                entry_list = []
                self.add_more_entry(key, frame, initial_value="", entry_list=entry_list)
                more_btn = tk.Button(frame, text="+", width=2, command=lambda k=key, f=frame: self.add_more_entry(k, f))
                more_btn.pack(anchor="w", pady=2)
                self.fields[key] = entry_list
            else:
                entry = tk.Entry(self.profile_area, width=40)
                entry.grid(row=idx, column=1, sticky="w", pady=2)
                self.fields[key] = entry

        # --- Album controls and info in right area ---
        self.album_controls = tk.Frame(self.album_area)
        self.album_controls.pack(fill="x", pady=(0, 10))
        self.upload_btn = tk.Button(self.album_controls, text="Upload File", command=self.upload_file_to_album)
        self.upload_btn.pack(anchor="w", pady=2)

        self.album_files_label = tk.Label(self.album_area, text="Album Files:")
        self.album_files_label.pack(anchor="nw", pady=(10, 0))
        self.album_files_list = tk.Listbox(self.album_area, width=50)
        self.album_files_list.pack(fill="both", expand=True, padx=5, pady=5)

    def refresh_storage_folders(self):
        storage_dir = self.settings.get("storage_directory", "storage/")
        folders = self.storage_utils.list_subfolders(storage_dir)
        self.folder_dropdown["values"] = folders
        # Do not auto-select a folder
        self.selected_folder.set("")

    def refresh_albums(self):
        storage_dir = self.settings.get("storage_directory", "storage/")
        folder = self.selected_folder.get()
        if not folder:
            self.album_dropdown["values"] = []
            self.selected_album.set("")
            return
        albums = self.files_utils.list_album_upload_folders(storage_dir, folder)
        self.album_dropdown["values"] = albums
        # Do not auto-select an album
        self.selected_album.set("")

        # Add upload button next to album dropdown if not already present
        if not hasattr(self, "upload_btn"):
            self.upload_btn = tk.Button(self.master, text="Upload File", command=self.upload_file_to_album)
            # Place the button just below the album dropdown (or adjust as needed)
            self.upload_btn.pack(pady=(0, 10), anchor="w")
        self.upload_btn.lift()

    def add_more_entry(self, key, frame, initial_value="", entry_list=None):
        """
        Adds a new entry row for email or social media, with a delete button.
        """
        row_frame = tk.Frame(frame)
        row_frame.pack(anchor="w", pady=2, fill="x")
        entry = tk.Entry(row_frame, width=32)
        entry.insert(0, initial_value)
        entry.pack(side="left")
        del_btn = tk.Button(row_frame, text="–", width=2, command=lambda: self.delete_entry_row(key, row_frame, entry))
        del_btn.pack(side="left", padx=2)
        if entry_list is None:
            self.fields[key].append(entry)
        else:
            entry_list.append(entry)

    def delete_entry_row(self, key, row_frame, entry):
        """
        Deletes an entry row for email or social media.
        """
        entry.destroy()
        row_frame.destroy()
        if entry in self.fields[key]:
            self.fields[key].remove(entry)

    def load_profile(self):
        storage_dir = self.settings.get("storage_directory", "storage/")
        folder = self.selected_folder.get()
        if not folder:
            messagebox.showwarning("Warning", "No storage folder selected.")
            return
        data = self.storage_utils.read_data_json(storage_dir, folder)
        if not data:
            messagebox.showinfo("Info", "No profile data found.")
            return
        self.profile_data = data
        for key, widget in self.fields.items():
            value = data.get(key, "")
            if key == "notes":
                widget.delete("1.0", tk.END)
                widget.insert(tk.END, value)
            elif key in ("email", "social_medias"):
                frame = widget[0].master.master if widget else None
                # Remove all old entry rows
                for entry in widget:
                    try:
                        entry.master.destroy()
                    except Exception:
                        pass
                widget.clear()
                values = value if isinstance(value, list) else ([value] if value else [])
                if not values:
                    values = [""]
                for v in values:
                    self.add_more_entry(key, frame, initial_value=v)
                # Ensure "+" button exists at the end
                for child in frame.winfo_children():
                    if isinstance(child, tk.Button) and child["text"] == "+":
                        child.lift()
                        break
                else:
                    more_btn = tk.Button(frame, text="+", width=2, command=lambda k=key, f=frame: self.add_more_entry(k, f))
                    more_btn.pack(anchor="w", pady=2)
            else:
                widget.delete(0, tk.END)
                widget.insert(0, value)

        # Also refresh albums for the loaded profile
        self.refresh_albums()

    def save_profile(self):
        storage_dir = self.settings.get("storage_directory", "storage/")
        folder = self.selected_folder.get()
        if not folder:
            messagebox.showwarning("Warning", "No storage folder selected.")
            return
        updates = {}
        for key, widget in self.fields.items():
            if key == "notes":
                updates[key] = widget.get("1.0", tk.END).strip()
            elif key in ("email", "social_medias"):
                updates[key] = [e.get().strip() for e in widget if e.get().strip()]
            else:
                updates[key] = widget.get().strip()
        self.storage_utils.update_data_json(storage_dir, folder, updates)
        messagebox.showinfo("Saved", "Profile saved successfully.")

    def load_album(self):
        from PIL import Image, ImageTk  # Requires Pillow installed
        from utils.album_preview import AlbumPreview
        import mimetypes

        storage_dir = self.settings.get("storage_directory", "storage/")
        folder = self.selected_folder.get()
        album = self.selected_album.get()
        if not folder or not album:
            messagebox.showwarning("Warning", "No storage folder or album selected.")
            return

        # Clear previous album area content
        for widget in self.album_area.winfo_children():
            widget.destroy()

        # Album controls
        self.album_controls = tk.Frame(self.album_area)
        self.album_controls.pack(fill="x", pady=(0, 10))
        self.upload_btn = tk.Button(self.album_controls, text="Upload File", command=self.upload_file_to_album)
        self.upload_btn.pack(anchor="w", pady=2)

        self.album_files_label = tk.Label(self.album_area, text=f"Album Files: {album}")
        self.album_files_label.pack(anchor="nw", pady=(10, 0))

        album_files_frame = tk.Frame(self.album_area)
        album_files_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Get files info (album can be a path like "album1/subfolder1")
        files_json = self.files_utils.get_album_files_info(storage_dir, folder, album)
        try:
            files_info = json.loads(files_json)
        except Exception:
            files_info = []

        # Separate images, videos, folders, and other files
        image_exts = {"jpg", "jpeg", "png", "gif", "bmp", "webp"}
        video_exts = {"mp4", "avi", "mov", "wmv", "webm"}
        folder_files = [f for f in files_info if f.get("is_folder")]
        image_files = [f for f in files_info if not f.get("is_folder") and f["type"].lower() in image_exts]
        video_files = [f for f in files_info if not f.get("is_folder") and f["type"].lower() in video_exts]
        other_files = [f for f in files_info if not f.get("is_folder") and f["type"].lower() not in image_exts and f["type"].lower() not in video_exts]

        # Show folder icons
        files_per_row = 4
        for idx, file_info in enumerate(folder_files):
            row = (idx // files_per_row) * 2
            col = idx % files_per_row
            canvas = tk.Canvas(album_files_frame, width=100, height=100, bg="#f0dc8c", highlightthickness=0, cursor="hand2")
            canvas.create_rectangle(10, 40, 90, 90, fill="#e2c76c", outline="#b89d4a")
            canvas.create_rectangle(20, 25, 70, 50, fill="#f6e7a1", outline="#b89d4a")
            canvas.grid(row=row, column=col, padx=5, pady=5)
            display_name = file_info["name"][:25] + ("..." if len(file_info["name"]) > 25 else "")
            name_label = tk.Label(album_files_frame, text=display_name)
            name_label.grid(row=row + 1, column=col, padx=5, pady=(0, 10))

            # Bind click to load this folder as album (append to current album path)
            def load_subfolder_album(event, folder_name=file_info["name"], parent_album=album):
                # Use os.path.join to handle nested folders
                new_album = os.path.join(parent_album, folder_name)
                self.selected_album.set(new_album)
                self.load_album()
            canvas.bind("<Button-1>", lambda e, fn=file_info["name"], pa=album: load_subfolder_album(e, fn, pa))
            name_label.bind("<Button-1>", lambda e, fn=file_info["name"], pa=album: load_subfolder_album(e, fn, pa))
            name_label.config(cursor="hand2")

        # Show image previews
        self.album_images = []  # Keep references to PhotoImage objects
        offset = len(folder_files)
        for idx, file_info in enumerate(image_files):
            file_path = os.path.join(storage_dir, folder, album, file_info["name"])
            try:
                img = Image.open(file_path)
                img.thumbnail((100, 100))
                photo = ImageTk.PhotoImage(img)
                self.album_images.append(photo)
                row = ((offset + idx) // files_per_row) * 2
                col = (offset + idx) % files_per_row
                img_label = tk.Label(album_files_frame, image=photo, cursor="hand2")
                img_label.grid(row=row, column=col, padx=5, pady=5)
                img_label.bind("<Button-1>", lambda e, fp=file_path: AlbumPreview(self.master, fp))
                img_label.file_info = file_info
                display_name = file_info["name"][:25] + ("..." if len(file_info["name"]) > 25 else "")
                name_label = tk.Label(album_files_frame, text=display_name)
                name_label.grid(row=row + 1, column=col, padx=5, pady=(0, 10))
            except Exception as e:
                err_label = tk.Label(album_files_frame, text=f"Error loading {file_info['name']}")
                err_label.grid(row=0, column=idx, padx=5, pady=5)

        # Show video previews (as placeholder image with play icon)
        video_start_idx = offset + len(image_files)
        for idx, file_info in enumerate(video_files):
            file_path = os.path.join(storage_dir, folder, album, file_info["name"])
            try:
                vid_idx = video_start_idx + idx
                row = (vid_idx // files_per_row) * 2
                col = vid_idx % files_per_row
                play_icon = tk.Canvas(album_files_frame, width=100, height=100, bg="black")
                play_icon.create_polygon(
                    [35, 25, 35, 75, 75, 50], fill="white"
                )
                play_icon.grid(row=row, column=col, padx=5, pady=5)
                play_icon.bind("<Button-1>", lambda e, fp=file_path: AlbumPreview(self.master, fp))
                display_name = file_info["name"][:25] + ("..." if len(file_info["name"]) > 25 else "")
                name_label = tk.Label(album_files_frame, text=display_name)
                name_label.grid(row=row + 1, column=col, padx=5, pady=(0, 10))
            except Exception:
                vid_label = tk.Label(album_files_frame, text=f"[Video] {file_info['name']}", width=15, height=5, bg="black", fg="white")
                vid_label.grid(row=0, column=video_start_idx + idx, padx=5, pady=5)
                vid_label.bind("<Button-1>", lambda e, fp=file_path: AlbumPreview(self.master, fp))
                display_name = file_info["name"][:25] + ("..." if len(file_info["name"]) > 25 else "")
                name_label = tk.Label(album_files_frame, text=display_name)
                name_label.grid(row=1, column=video_start_idx + idx, padx=5, pady=(0, 10))

        # List other files below images/videos
        total_media = offset + len(image_files) + len(video_files)
        row_offset = ((total_media - 1) // files_per_row + 1) * 2 if total_media else 0
        col_span = min(files_per_row, total_media) if total_media else 1
        if other_files:
            files_list_label = tk.Label(album_files_frame, text="Other Files:")
            files_list_label.grid(row=row_offset, column=0, sticky="w", pady=(10, 0), columnspan=col_span)
            for i, file_info in enumerate(other_files):
                file_path = os.path.join(storage_dir, folder, album, file_info["name"])
                file_label = tk.Label(album_files_frame, text=f"{file_info['name']} ({file_info['type']}, {file_info['size']} bytes)", fg="blue", cursor="hand2")
                file_label.grid(row=row_offset + 1 + i, column=0, sticky="w", columnspan=col_span)
                file_label.bind("<Button-1>", lambda e, fp=file_path: AlbumPreview(self.master, fp))

    def show_about(self):
        messagebox.showinfo(
            "About",
            f"Documenter Program\nVersion: {self.settings.get('version', 'N/A')}\nAuthor: {self.settings.get('author', 'N/A')}"
        )

    def new_storage_folder(self):
        storage_dir = self.settings.get("storage_directory", "storage/")
        folder_name = simpledialog.askstring("New Storage Folder", "Enter new folder name:")
        if not folder_name:
            return
        if folder_name in self.storage_utils.list_subfolders(storage_dir):
            messagebox.showerror("Error", "Folder already exists.")
            return
        self.storage_utils.create_storage_folder(storage_dir, folder_name)
        self.refresh_storage_folders()
        self.selected_folder.set(folder_name)
        messagebox.showinfo("Created", f"Storage folder '{folder_name}' created.")

    def new_album(self):
        storage_dir = self.settings.get("storage_directory", "storage/")
        folder = self.selected_folder.get()
        if not folder:
            messagebox.showwarning("Warning", "No storage folder selected.")
            return
        album_name = simpledialog.askstring("New Album", "Enter new album name:")
        if not album_name:
            return
        if album_name in self.files_utils.list_album_upload_folders(storage_dir, folder):
            messagebox.showerror("Error", "Album already exists.")
            return
        self.files_utils.create_album_upload_folder(storage_dir, folder, album_name)
        self.refresh_albums()
        self.selected_album.set(album_name)
        messagebox.showinfo("Created", f"Album '{album_name}' created.")

    def upload_file_to_album(self):
        from tkinter import filedialog
        storage_dir = self.settings.get("storage_directory", "storage/")
        folder = self.selected_folder.get()
        album = self.selected_album.get()
        if not folder or not album:
            messagebox.showwarning("Warning", "No storage folder or album selected.")
            return
        file_path = filedialog.askopenfilename(title="Select file to upload")
        if not file_path:
            return
        album_dir = os.path.join(storage_dir, folder, album)
        if not os.path.isdir(album_dir):
            os.makedirs(album_dir, exist_ok=True)
        dest_path = os.path.join(album_dir, os.path.basename(file_path))
        try:
            shutil.copy2(file_path, dest_path)
            # No confirmation, just refresh album display
            self.load_album()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload file: {e}")

    def export_profile_gui(self):
        storage_dir = self.settings.get("storage_directory", "storage/")
        folder = self.selected_folder.get()
        if not folder:
            messagebox.showwarning("Warning", "No storage folder selected.")
            return
        export_path = filedialog.asksaveasfilename(
            title="Export Profile as ZIP",
            defaultextension=".zip",
            initialfile=f"{folder}.zip",
            filetypes=[("Zip Files", "*.zip")]
        )
        if export_path:
            def do_export():
                try:
                    export_profile(storage_dir, folder, export_path)
                    self.master.after(0, lambda: messagebox.showinfo("Export", f"Profile exported to {export_path}"))
                except Exception as e:
                    self.master.after(0, lambda: messagebox.showerror("Export Error", f"Failed to export profile: {e}"))
            threading.Thread(target=do_export, daemon=True).start()

    def import_profile_gui(self):
        storage_dir = self.settings.get("storage_directory", "storage/")
        import_zip_path = filedialog.askopenfilename(
            title="Import Profile from ZIP",
            filetypes=[("Zip Files", "*.zip")]
        )
        if not import_zip_path:
            return
        folder_name = simpledialog.askstring("Import Profile", "Enter folder name for imported profile (leave blank to use zip name):")
        def do_import():
            try:
                imported_folder = import_profile(storage_dir, import_zip_path, folder_name if folder_name else None)
                self.master.after(0, lambda: messagebox.showinfo("Import", f"Profile imported to {imported_folder}"))
                self.master.after(0, self.refresh_storage_folders)
            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Import Error", f"Failed to import profile: {e}"))
        threading.Thread(target=do_import, daemon=True).start()
