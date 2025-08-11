from pathlib import Path
from typing import List, Dict
from fastapi import HTTPException
from fastapi.responses import PlainTextResponse

BASE = Path(__file__).resolve().parents[1]  # ~/AI

def _safe(p: str) -> Path:
    q = (BASE / p).resolve()
    if BASE not in q.parents and q != BASE:
        raise HTTPException(status_code=400, detail="path escapes base")
    return q

def list_tree(subdir: str = ".") -> Dict:
    root = _safe(subdir)
    items: List[str] = []
    for p in root.rglob("*"):
        if p.is_file():
            rel = p.relative_to(BASE).as_posix()
            items.append(rel)
    return {"base": BASE.as_posix(), "count": len(items), "files": sorted(items)}

def get_file(relpath: str) -> PlainTextResponse:
    p = _safe(relpath)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="not found")
    # limit file size to 1.5MB to avoid huge dumps
    if p.stat().st_size > 1_500_000:
        raise HTTPException(status_code=413, detail="file too large")
    text = p.read_text(errors="ignore")
    return PlainTextResponse(text)
