# core/disk_engine.py
import os
import time
from .disk_reader import DiskReader, SECTOR_SIZE


class DiskCloneEngine:
    def __init__(self, on_progress=None):
        self.on_progress = on_progress or (lambda **kw: None)
        self._stop = False
        self.sector_map = {}
        self.stats = {"ok": 0, "bad": 0, "retried": 0}

    def stop(self):
        self._stop = True

    def clone(self, source_path, dest_path, max_retries=3, write_zeros=True):
        """
        Clona un disco/archivo sector por sector.
        - source_path: disco físico (\\\\.\\PhysicalDrive1 o /dev/sdb) o archivo imagen.
        - dest_path: archivo imagen destino o disco físico.
        """
        reader = DiskReader(source_path)
        reader.open()
        total_sectors = reader.size // SECTOR_SIZE

        # Abrir destino
        if sys.platform == "win32" and dest_path.startswith("\\\\.\\"):
            dest_fd = self._open_dest_windows(dest_path)
        else:
            dest_fd = os.open(dest_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)

        try:
            for i in range(total_sectors):
                if self._stop:
                    break

                offset = i * SECTOR_SIZE
                ok, data = self._read_with_retries(reader, offset, max_retries)

                if ok:
                    self.sector_map[offset] = "ok"
                    self.stats["ok"] += 1
                else:
                    self.sector_map[offset] = "bad"
                    self.stats["bad"] += 1
                    if write_zeros:
                        data = b"\x00" * SECTOR_SIZE

                if data:
                    self._write_sector(dest_fd, offset, data)

                # Reportar progreso cada 500 sectores (250 KB)
                if i % 500 == 0:
                    self.on_progress(
                        done=i, total=total_sectors,
                        bad=self.stats["bad"], retried=self.stats["retried"],
                    )
        finally:
            reader.close()
            os.close(dest_fd)

        return self.sector_map, self.stats

    def _read_with_retries(self, reader, offset, max_retries):
        """Intenta leer hasta N veces. Si falla todas, marca como bad."""
        for attempt in range(max_retries):
            ok, data = reader.read_sector(offset)
            if ok:
                if attempt > 0:
                    self.stats["retried"] += 1
                return True, data
            time.sleep(0.05 * (attempt + 1))  # Espera creciente
        return False, None

    def _write_sector(self, fd, offset, data):
        if isinstance(fd, int):
            os.lseek(fd, offset, os.SEEK_SET)
            os.write(fd, data)
        else:
            # Handle de Windows
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            written = wintypes.DWORD(0)
            high = (offset >> 32) & 0xFFFFFFFF
            low = offset & 0xFFFFFFFF
            kernel32.SetFilePointer(fd, low, ctypes.byref(wintypes.LONG(high)), 0)
            kernel32.WriteFile(fd, data, len(data), ctypes.byref(written), None)

    def _open_dest_windows(self, path):
        import ctypes
        from ctypes import wintypes
        GENERIC_WRITE = 0x40000000
        FILE_SHARE_READ = 1
        FILE_SHARE_WRITE = 2
        OPEN_EXISTING = 3
        INVALID_HANDLE_VALUE = -1
        kernel32 = ctypes.windll.kernel32
        h = kernel32.CreateFileW(
            path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
            None, OPEN_EXISTING, 0, None,
        )
        if h == INVALID_HANDLE_VALUE:
            raise OSError(f"No se pudo abrir destino {path}")
        return h
