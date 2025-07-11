import tkinter as tk
from tkinter import filedialog, messagebox
import os

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

class AlbumPreview(tk.Toplevel):
    def __init__(self, master, file_path):
        super().__init__(master)
        self.title(f"Preview: {os.path.basename(file_path)}")
        self.geometry("800x800")  # Set preview window to 800x800
        self.file_path = file_path

        self.preview_frame = tk.Frame(self)
        self.preview_frame.pack(fill="both", expand=True)

        ext = os.path.splitext(file_path)[1].lower()
        self.is_image = ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp") and Image and ImageTk
        self.is_video = ext in (".mp4", ".avi", ".mov", ".wmv", ".webm")

        self.display_widget = None
        self.photo = None  # Keep reference to avoid garbage collection

        # Ensure video stops when window is closed
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if self.is_image:
            self.display_image()
            self.bind("<Configure>", self.on_resize)
        elif self.is_video:
            self.display_video_vlc()
        else:
            self.display_file_info()

        # --- Horizontal bar above export button ---
        bar = tk.Frame(self, height=2, bg="gray")
        bar.pack(fill="x", side="bottom", pady=(0, 0))

        export_btn = tk.Button(self, text="Export", command=self.export_file)
        export_btn.pack(side="bottom", pady=10)

        delete_btn = tk.Button(self, text="Delete", command=self.delete_file)
        delete_btn.pack(side="bottom", pady=(0, 5))

    def display_image(self):
        # Remove previous widget if any
        if self.display_widget:
            self.display_widget.destroy()
        try:
            img = Image.open(self.file_path)
            # Calculate size based on current preview_frame size minus space for the bottom bar/buttons
            self.update_idletasks()
            w = self.preview_frame.winfo_width()
            h = self.preview_frame.winfo_height()
            # Reserve space for the bottom controls (about 80px)
            if w < 10 or h < 10:
                w, h = 800, 720  # Default size for first render
            else:
                h = max(100, h - 80)
            img_ratio = img.width / img.height
            frame_ratio = w / h
            if img_ratio > frame_ratio:
                new_w = w
                new_h = int(w / img_ratio)
            else:
                new_h = h
                new_w = int(h * img_ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            label = tk.Label(self.preview_frame, image=self.photo, bg="black")
            label.pack(expand=True, fill="both")
            self.display_widget = label
        except Exception as e:
            tk.Label(self.preview_frame, text=f"Error loading image: {e}").pack()

    def on_resize(self, event):
        if self.is_image and event.widget == self:
            self.display_image()

    def display_video_vlc(self):
        try:
            import vlc  # pip install python-vlc
        except ImportError:
            self.display_video_placeholder()
            tk.Label(self, text="python-vlc not installed.\nRun: pip install python-vlc").pack()
            return

        if self.display_widget:
            self.display_widget.destroy()

        self.vlc_panel = tk.Frame(self.preview_frame, bg="black")
        self.vlc_panel.pack(fill="both", expand=True)
        self.display_widget = self.vlc_panel

        self.instance = vlc.Instance('--no-video-title-show', '--avcodec-hw=none')
        self.player = self.instance.media_player_new()
        self.media = self.instance.media_new(self.file_path)
        self.player.set_media(self.media)

        self.update_idletasks()
        # Set the video output window
        if os.name == "nt":
            self.player.set_hwnd(self.vlc_panel.winfo_id())
        elif os.name == "posix":
            self.player.set_xwindow(self.vlc_panel.winfo_id())
        elif os.name == "darwin":
            self.player.set_nsobject(self.vlc_panel.winfo_id())

        # --- Video Controls ---
        controls = tk.Frame(self)
        controls.pack(side="bottom", fill="x", pady=(0, 5))

        play_btn = tk.Button(controls, text="Play", command=self.play_video)
        play_btn.pack(side="left", padx=5)
        pause_btn = tk.Button(controls, text="Pause", command=self.pause_video)
        pause_btn.pack(side="left", padx=5)
        stop_btn = tk.Button(controls, text="Stop", command=self.stop_video)
        stop_btn.pack(side="left", padx=5)

        tk.Label(controls, text="Volume:").pack(side="left", padx=(20, 2))
        self.volume_var = tk.DoubleVar(value=100)
        volume_slider = tk.Scale(controls, from_=0, to=100, orient="horizontal", variable=self.volume_var, command=self.set_volume, length=120)
        volume_slider.pack(side="left")

        self.player.audio_set_volume(int(self.volume_var.get()))
        # self.player.play()  # <-- Do NOT auto-play video on open

    def play_video(self):
        if hasattr(self, "player"):
            self.player.play()

    def pause_video(self):
        if hasattr(self, "player"):
            self.player.pause()

    def stop_video(self):
        if hasattr(self, "player"):
            self.player.stop()

    def set_volume(self, value):
        if hasattr(self, "player"):
            self.player.audio_set_volume(int(float(value)))

    def display_video_placeholder(self):
        if self.display_widget:
            self.display_widget.destroy()
        # Show a placeholder for video
        canvas = tk.Canvas(self.preview_frame, width=350, height=350, bg="black")
        canvas.pack(expand=True, fill="both")
        w, h = 350, 350
        canvas.create_polygon(
            [w//2-30, h//2-50, w//2-30, h//2+50, w//2+50, h//2],
            fill="white"
        )
        canvas.create_text(w//2, h//2+70, text="Video preview not supported", fill="white")
        self.display_widget = canvas

    def display_file_info(self):
        if self.display_widget:
            self.display_widget.destroy()
        tk.Label(self.preview_frame, text=f"Cannot preview this file type.\nFile: {os.path.basename(self.file_path)}").pack(expand=True, pady=40)

    def open_video(self):
        try:
            if os.name == "nt":
                os.startfile(self.file_path)
            elif os.name == "posix":
                import subprocess
                subprocess.Popen(["xdg-open", self.file_path])
            else:
                messagebox.showinfo("Open Video", "Opening video is not supported on this OS.")
        except Exception as e:
            messagebox.showerror("Open Video Error", f"Failed to open video: {e}")

    def export_file(self):
        export_path = filedialog.asksaveasfilename(
            title="Export File",
            initialfile=os.path.basename(self.file_path)
        )
        if export_path:
            try:
                import shutil
                shutil.copy2(self.file_path, export_path)
                messagebox.showinfo("Export", f"File exported to {export_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export file: {e}")

    def delete_file(self):
        confirm = messagebox.askyesno("Delete File", f"Are you sure you want to delete '{os.path.basename(self.file_path)}'?")
        if confirm:
            try:
                os.remove(self.file_path)
                messagebox.showinfo("Deleted", f"File '{os.path.basename(self.file_path)}' deleted.")
                self.destroy()
            except Exception as e:
                messagebox.showerror("Delete Error", f"Failed to delete file: {e}")

    def on_close(self):
        # Stop video if playing before closing
        if hasattr(self, "player"):
            try:
                self.player.stop()
            except Exception:
                pass
        self.destroy()