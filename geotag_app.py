import os
import random
import re
import threading
import time
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
from typing import List

import requests
from PIL import Image, PngImagePlugin
import piexif


def dms_coordinates(value: float):
    """Convert decimal degrees to degrees, minutes, seconds tuple."""
    abs_value = abs(value)
    deg = int(abs_value)
    minutes_float = (abs_value - deg) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60 * 1000000)
    return ((deg, 1), (minutes, 1), (seconds, 1000000))


class GeoTaggerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Image Geotagger")

        self.folder_var = tk.StringVar()
        self.rps_var = tk.StringVar(value="1")
        self.cancel_event = threading.Event()

        self._build_ui()

    def _build_ui(self) -> None:
        # Folder selection
        folder_frame = ttk.Frame(self.root)
        folder_frame.pack(fill="x", padx=5, pady=5)
        ttk.Entry(folder_frame, textvariable=self.folder_var, width=50).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(folder_frame, text="Select Folder", command=self.select_folder).pack(
            side="left", padx=5
        )

        # Locations and Keywords
        lists_frame = ttk.Frame(self.root)
        lists_frame.pack(fill="both", padx=5, pady=5)
        loc_frame = ttk.Frame(lists_frame)
        key_frame = ttk.Frame(lists_frame)
        loc_frame.pack(side="left", fill="both", expand=True)
        key_frame.pack(side="left", fill="both", expand=True)

        ttk.Label(loc_frame, text="Locations").pack(anchor="w")
        self.locations_text = tk.Text(loc_frame, width=40, height=10)
        self.locations_text.pack(fill="both", expand=True)

        ttk.Label(key_frame, text="Keywords").pack(anchor="w")
        self.keywords_text = tk.Text(key_frame, width=40, height=10)
        self.keywords_text.pack(fill="both", expand=True)

        # Requests per second
        rate_frame = ttk.Frame(self.root)
        rate_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(rate_frame, text="Requests per second:").pack(side="left")
        self.rps_entry = ttk.Entry(rate_frame, textvariable=self.rps_var, width=10)
        self.rps_entry.pack(side="left", padx=5)

        # Start/Cancel buttons
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=5, pady=5)
        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.start)
        self.start_btn.pack(side="left", padx=5)
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.cancel, state="disabled")
        self.cancel_btn.pack(side="left")

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=5, pady=5)

        # Log output
        ttk.Label(self.root, text="Log").pack(anchor="w", padx=5)
        self.log_text = scrolledtext.ScrolledText(self.root, width=80, height=10, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    def select_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def log(self, message: str) -> None:
        def append():
            self.log_text.configure(state="normal")
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.configure(state="disabled")
            self.log_text.see(tk.END)
        self.root.after(0, append)

    def start(self) -> None:
        folder = self.folder_var.get()
        locations = [l.strip() for l in self.locations_text.get("1.0", tk.END).splitlines() if l.strip()]
        keywords = [k.strip() for k in self.keywords_text.get("1.0", tk.END).splitlines() if k.strip()]
        if not folder or not locations or not keywords:
            self.log("Please select folder, locations, and keywords.")
            return
        try:
            rps = float(self.rps_var.get())
            if rps <= 0:
                raise ValueError
        except ValueError:
            self.log("Invalid requests per second value.")
            return

        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.cancel_event.clear()

        threading.Thread(
            target=self.process_images, args=(folder, locations, keywords, rps), daemon=True
        ).start()

    def cancel(self) -> None:
        self.cancel_event.set()
        self.log("Cancelling...")

    def process_images(self, folder: str, locations: List[str], keywords: List[str], rps: float) -> None:
        images = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        total = len(images)
        if total == 0:
            self.log("No images found in selected folder.")
            self._reset_buttons()
            return

        out_folder = os.path.join(folder, f"geotagged_{os.path.basename(folder)}")
        os.makedirs(out_folder, exist_ok=True)

        self.root.after(0, lambda: self.progress.config(maximum=total, value=0))

        delay = 1.0 / rps
        last_request = 0.0
        name_counts = {}

        for idx, img_name in enumerate(images, 1):
            if self.cancel_event.is_set():
                break
            img_path = os.path.join(folder, img_name)
            location = random.choice(locations)
            keyword = random.choice(keywords)
            base, ext = os.path.splitext(img_name)
            safe_keyword = re.sub(r"[^A-Za-z0-9_-]", "_", keyword) or "image"
            count = name_counts.get(safe_keyword, 0) + 1
            name_counts[safe_keyword] = count
            new_name = f"{safe_keyword}{'_' + str(count) if count > 1 else ''}{ext}"
            try:
                # Rate limiting
                wait = delay - (time.time() - last_request)
                if wait > 0:
                    time.sleep(wait)
                lat, lon = self.geocode(location)
                last_request = time.time()

                out_path = os.path.join(out_folder, new_name)
                self.write_metadata(img_path, lat, lon, keyword, out_path)
                self.log(f"Processed {img_name} -> {location} ({lat}, {lon}) as {new_name}")
            except Exception as e:
                self.log(f"Error processing {img_name}: {e}")
            finally:
                self.root.after(0, lambda v=idx: self.progress.config(value=v))

        self.log("Done" if not self.cancel_event.is_set() else "Cancelled")
        self._reset_buttons()

    def _reset_buttons(self) -> None:
        self.root.after(0, lambda: [
            self.start_btn.config(state="normal"),
            self.cancel_btn.config(state="disabled"),
        ])

    def geocode(self, location: str):
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": location, "format": "json", "limit": 1}
        headers = {"User-Agent": "geotagger-app"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError(f"Location not found: {location}")
        return float(data[0]["lat"]), float(data[0]["lon"])

    def write_metadata(self, img_path: str, lat: float, lon: float, keyword: str, out_path: str) -> None:
        img = Image.open(img_path)
        if img.format == "PNG":
            info = PngImagePlugin.PngInfo()
            info.add_text("Title", keyword)
            info.add_text("Latitude", str(lat))
            info.add_text("Longitude", str(lon))
            img.save(out_path, pnginfo=info)
            return

        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        try:
            exif_dict = piexif.load(img.info.get("exif", b""))
        except Exception:
            pass
        exif_dict.setdefault("GPS", {})
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = b"N" if lat >= 0 else b"S"
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = dms_coordinates(lat)
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = b"E" if lon >= 0 else b"W"
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = dms_coordinates(lon)
        exif_dict.setdefault("0th", {})
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = keyword
        exif_bytes = piexif.dump(exif_dict)
        img.save(out_path, exif=exif_bytes)


def main() -> None:
    root = tk.Tk()
    app = GeoTaggerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
