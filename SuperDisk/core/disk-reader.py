# core/disk_reader.py
import os
import sys

SECTOR_SIZE = 512  # Tamaño estándar de sector


class DiskReader:
    """Lee sectores crudos de un disco físico o archivo imagen."""

    def __init__(self, path):
        self.path = path
        self.handle = None
        self.size = 0
        self.is_physical = False

    def open(self):
        # Detecta si es un disco físico o un archivo normal
        if sys.platform == "win32" and (
            self.path.startswith("\\\\.\\") or self.path.startswith("\\\\.\\PhysicalDrive")
        ):
            self._open_windows()
            self.is_physical = True
        elif not sys.platform == "win32" and self.path.startswith("/dev/"):
            self._open_unix()
            self.is_physical = True
        else:
            self._open_file()

    def _open_windows(self):
        import ctypes
        from ctypes import wintypes

        GENERIC_READ = 0x80000000
        FILE_SHARE_READ = 0x00000001
        FILE_SHARE_WRITE = 0x00000002
        OPEN_EXISTING = 3
        INVALID_HANDLE_VALUE = -1

        kernel32 = ctypes.windll.kernel32
        kernel32.CreateFileW.restype = wintypes.HANDLE
        handle = kernel32.CreateFileW(
            self.path, GENERIC_READ,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None, OPEN_EXISTING, 0, None,
        )
        if handle == INVALID_HANDLE_VALUE:
            raise OSError(
                f"No se pudo abrir {self.path}.\n"
                "¿Ejecutaste el programa como Administrador?"
            )
        self.handle = handle
        # Tamaño del disco
        size_high = wintypes.DWORD(0)
        size_low = kernel32.GetFileSize(handle, ctypes.byref(size_high))
        self.size = (size_high.value << 32) | size_low

    def _open_unix(self):
        self.handle = os.open(self.path, os.O_RDONLY)
        self.size = os.lseek(self.handle, 0, os.SEEK_END)
        os.lseek(self.handle, 0, os.SEEK_SET)

    def _open_file(self):
        self.handle = os.open(self.path, os.O_RDONLY)
        self.size = os.path.getsize(self.path)

    def read_sector(self, offset):
        """Lee 1 sector (512 bytes). Devuelve (ok, data)."""
        if sys.platform == "win32" and self.is_physical:
            return self._read_windows(offset)
        return self._read_unix_or_file(offset)

    def _read_windows(self, offset):
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        buf = ctypes.create_string_buffer(SECTOR_SIZE)
        bytes_read = wintypes.DWORD(0)

        # Mover el puntero al offset (parte alta + baja del offset de 64 bits)
        high = (offset >> 32) & 0xFFFFFFFF
        low = offset & 0xFFFFFFFF
        kernel32.SetFilePointer(self.handle, low, ctypes.byref(wintypes.LONG(high)), 0)

        ok = kernel32.ReadFile(
            self.handle, buf, SECTOR_SIZE,
            ctypes.byref(bytes_read), None,
        )
        if not ok or bytes_read.value != SECTOR_SIZE:
            return False, None
        return True, buf.raw

    def _read_unix_or_file(self, offset):
        try:
            if sys.platform == "win32":
                os.lseek(self.handle, offset, os.SEEK_SET)
                data = os.read(self.handle, SECTOR_SIZE)
            else:
                data = os.pread(self.handle, SECTOR_SIZE, offset)
            if len(data) != SECTOR_SIZE:
                return False, None
            return True, data
        except OSError:
            return False, None

    def close(self):
        if self.handle is None:
            return
        if sys.platform == "win32" and self.is_physical:
            import ctypes
            ctypes.windll.kernel32.CloseHandle(self.handle)
        else:
            os.close(self.handle)
        self.handle = None
