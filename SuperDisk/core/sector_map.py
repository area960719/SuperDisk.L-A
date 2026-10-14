# core/sector_map.py
import json

class SectorMap:
    def __init__(self, sector_map):
        self.sector_map = sector_map  # {offset: 'ok' | 'bad'}

    def to_json(self, path):
        with open(path, "w") as f:
            json.dump(
                {str(k): v for k, v in self.sector_map.items()},
                f, indent=2,
            )

    def to_ascii(self, columns=80):
        """Devuelve un mapa visual tipo: ████▓▓░░ (ok), ░░▒▒ (bad)."""
        offsets = sorted(self.sector_map.keys())
        if not offsets:
            return ""
        total = len(offsets)
        lines = []
        for i in range(0, total, columns):
            chunk = offsets[i:i + columns]
            row = "".join("█" if self.sector_map[o] == "ok" else "X" for o in chunk)
            lines.append(row)
        return "\n".join(lines)

    def summary(self):
        total = len(self.sector_map)
        bad = sum(1 for v in self.sector_map.values() if v == "bad")
        ok = total - bad
        pct = (ok / total * 100) if total else 0
        return {
            "total_sectores": total,
            "ok": ok,
            "bad": bad,
            "salud_%": round(pct, 2),
        }
