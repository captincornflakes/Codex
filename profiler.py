import tkinter as tk
from utils.settings import load_settings
from utils.gui import DocumenterApp

if __name__ == "__main__":
    root = tk.Tk()
    settings = load_settings()
    app = DocumenterApp(root, settings)
    
    
    root.mainloop()