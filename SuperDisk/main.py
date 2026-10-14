# main.py
import os
import sys
import argparse
from core.disk_engine import DiskCloneEngine
from core.sector_map import SectorMap


def progress(done, total, bad, retried):
    pct = (done / total * 100) if total else 0
    bar_len = 40
    filled = int(bar_len * done / total) if total else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\r[{bar}] {pct:5.1f}% | bad={bad} | reintentos={retried}", end="", flush=True)


def cmd_clone(args):
    print(f"\n🔍 Origen : {args.source}")
    print(f"💾 Destino: {args.dest}\n")

    if not args.yes:
        confirm = input("⚠️  ¿Continuar? Esta acción sobrescribe el destino (s/N): ")
        if confirm.lower() != "s":
            print("❌ Cancelado.")
            return

    engine = DiskCloneEngine(on_progress=progress)
    try:
        smap, stats = engine.clone(args.source, args.dest, max_retries=3)
    except KeyboardInterrupt:
        print("\n⏹  Interrumpido por el usuario.")
        return
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return

    print("\n\n")
    m = SectorMap(smap)
    print(m.to_ascii(columns=100))

    resumen = m.summary()
    print("\n📊 Resumen final:")
    for k, v in resumen.items():
        print(f"   {k}: {v}")

    # Guardar mapa como JSON
    json_path = args.dest + ".map.json"
    m.to_json(json_path)
    print(f"\n🗺️  Mapa guardado en: {json_path}")


def main():
    parser = argparse.ArgumentParser(
        description="SuperDisk 💽 - Clonador y rescatador de discos a nivel de sector."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_clone = sub.add_parser("clone", help="Clonar un disco o imagen")
    p_clone.add_argument("source", help="Origen: archivo imagen o disco físico (ej: \\\\.\\PhysicalDrive1)")
    p_clone.add_argument("dest", help="Destino: archivo imagen o disco físico")
    p_clone.add_argument("-y", "--yes", action="store_true", help="No pedir confirmación")
    p_clone.set_defaults(func=cmd_clone)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
