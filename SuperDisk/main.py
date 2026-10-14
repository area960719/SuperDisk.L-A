# main.py
import os
import sys

# Asegurar imports al ejecutarse como .exe
if getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.dirname(sys.executable))

from ui.window import MainWindow


def main():
    print("💽 Iniciando SuperDisk...")
    app = MainWindow()
    app.run()
    print("👋 SuperDisk cerrado.")


if __name__ == "__main__":
    main()
