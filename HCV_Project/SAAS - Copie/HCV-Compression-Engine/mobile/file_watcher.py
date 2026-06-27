import threading
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp',
    '.mp4', '.mov', '.avi', '.mkv', '.3gp',
}

DEFAULT_WATCH_DIR = Path.home() / "Pictures"


class _MediaEventHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str], None]):
        super().__init__()
        self._callback = callback

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() in MEDIA_EXTENSIONS:
            self._callback(str(path))


class HCVFileWatcher:
    def __init__(self, watch_dir: Optional[str] = None):
        self._watch_dir = Path(watch_dir) if watch_dir else DEFAULT_WATCH_DIR
        self._observer: Optional[Observer] = None
        self._lock = threading.Lock()

    def start(self, callback: Callable[[str], None]):
        with self._lock:
            if self._observer and self._observer.is_alive():
                return
            self._watch_dir.mkdir(parents=True, exist_ok=True)
            handler = _MediaEventHandler(callback)
            self._observer = Observer()
            self._observer.schedule(handler, str(self._watch_dir), recursive=True)
            self._observer.start()
            print(f"FileWatcher actif sur : {self._watch_dir}")

    def stop(self):
        with self._lock:
            if self._observer and self._observer.is_alive():
                self._observer.stop()
                self._observer.join(timeout=5)
                self._observer = None
                print("FileWatcher arrete.")