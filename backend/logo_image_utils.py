"""Logo-Bilder: EXIF-Orientierung normalisieren (Upload + Export).

Rein additiv — betrifft nur Firmenlogo-Upload und Logo-Einbettung in Exporte.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

_RASTER_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def normalize_logo_bytes(content: bytes, ext: str) -> bytes:
    """Wendet EXIF-Orientierung an und speichert rasterisiert neu; bei Fehler Original."""
    suffix = str(ext or "").lower()
    if suffix not in _RASTER_EXT:
        return content
    try:
        from PIL import Image, ImageOps

        img = Image.open(BytesIO(content))
        img = ImageOps.exif_transpose(img)
        out = BytesIO()
        if suffix in {".jpg", ".jpeg"}:
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            img.save(out, format="JPEG", quality=92, optimize=True)
        elif suffix == ".png":
            img.save(out, format="PNG", optimize=True)
        elif suffix == ".webp":
            img.save(out, format="WEBP", quality=92)
        else:
            return content
        return out.getvalue()
    except Exception:
        return content


def _pil_open_transposed(path: Path):
    from PIL import Image, ImageOps

    img = Image.open(path)
    return ImageOps.exif_transpose(img)


def logo_bytes_for_export(path: Path) -> BytesIO | None:
    """Raster-Logo mit EXIF-Korrektur als Stream für PDF/DOCX; SVG unverändert."""
    suffix = path.suffix.lower()
    if suffix == ".svg":
        try:
            data = path.read_bytes()
        except OSError:
            return None
        return BytesIO(data)
    if suffix not in _RASTER_EXT:
        return None
    try:
        img = _pil_open_transposed(path)
        buf = BytesIO()
        if suffix in {".jpg", ".jpeg"}:
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            img.save(buf, format="JPEG", quality=92, optimize=True)
        elif suffix == ".png":
            img.save(buf, format="PNG", optimize=True)
        elif suffix == ".webp":
            img.save(buf, format="WEBP", quality=92)
        else:
            return None
        buf.seek(0)
        return buf
    except Exception:
        try:
            return BytesIO(path.read_bytes())
        except OSError:
            return None
