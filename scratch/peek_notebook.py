"""Print the code cells of a notebook (avoids quoting pain in the shell)."""
import json
import sys

nb = json.load(open(sys.argv[1], encoding="utf-8"))
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 700
for i, cell in enumerate(nb.get("cells", [])):
    if cell.get("cell_type") != "code":
        continue
    src = "".join(cell.get("source", [])).strip()
    if not src:
        continue
    print(f"--- cell {i} ---")
    print(src[:limit])
    print()
