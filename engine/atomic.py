from pathlib import Path
import json, os, tempfile, csv
def atomic_write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', delete=False, dir=str(path.parent)) as tmp:
        tmp.write(text)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path=tmp.name
    os.replace(tmp_path, path)
def atomic_write_json(path: Path, obj):
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2))
def atomic_append_csv(path: Path, row: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with open(path, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if not exists: w.writerow(["ts","symbol","side","qty","price","stake","note"])
        w.writerow(row)
