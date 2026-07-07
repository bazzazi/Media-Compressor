#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Compression Script (Images + PDFs)
----------------------------------------
- Reads files from the "input" folder (any number, any format).
- Reduces file size as much as possible without noticeable quality loss
  and brings it below the size limit you specify.
- Saves output with the same name in the "output" folder.

Strategy:
  1) First, lossless compression is applied.
  2) If the file is still larger than the limit, quality is gradually
     and controllably reduced to meet the limit (minimum possible loss).

Prerequisites (automatically checked):
    pip install pillow
    Ghostscript for PDF (optional but recommended):
        - Linux/macOS: ghostscript package
        - Windows: gswin64c

Developed by Mohammad Ali Bazzazi
https://mohammadalibazzazi.ir
"""

import os
import sys
import shutil
import subprocess
import tempfile
import re

# ----------------------------- Settings -----------------------------
INPUT_DIR = "input"
OUTPUT_DIR = "output"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".gif"}
PDF_EXTS = {".pdf"}


# ----------------------------- Helper Utilities -----------------------------
def human(size_bytes: float) -> str:
    """Human-readable representation of bytes."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024 or unit == "GB":
            return f"{size_bytes:.1f}{unit}" if unit != "B" else f"{int(size_bytes)}B"
        size_bytes /= 1024
    return f"{size_bytes:.1f}GB"


def parse_size(text: str) -> int:
    """
    Convert a size string like '500KB' or '1MB' or '1.5 mb' to bytes.
    Numbers without a unit are interpreted as bytes.
    """
    text = text.strip().upper().replace(" ", "")
    m = re.match(r"^([\d.]+)(KB|MB|GB|B)?$", text)
    if not m:
        raise ValueError("Invalid size format. Example: 500KB or 1MB")
    value = float(m.group(1))
    unit = m.group(2) or "B"
    factor = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}[unit]
    return int(value * factor)


def which_ghostscript():
    for cand in ("gs", "gswin64c", "gswin32c"):
        if shutil.which(cand):
            return cand
    return None


# ----------------------------- Image Compression -----------------------------
def compress_image(src: str, dst: str, max_bytes: int) -> tuple[bool, str]:
    """
    Compress an image to stay below the limit.
    First try lossless, then if needed gradually reduce quality/dimensions.
    """
    from PIL import Image, ImageFile
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    ext = os.path.splitext(src)[1].lower()
    img = Image.open(src)

    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    is_animated = getattr(img, "is_animated", False)

    # Animated GIF: copy as-is (no safe compression method)
    if ext == ".gif" and is_animated:
        shutil.copy2(src, dst)
        return os.path.getsize(dst) <= max_bytes, "Animated GIF (direct copy)"

    # --- Step 1: lossless attempt ---
    def save_lossless(path):
        if ext == ".png" or has_alpha:
            im = img.convert("RGBA") if has_alpha else img.convert("RGB")
            im.save(path, format="PNG", optimize=True)
        elif ext == ".webp":
            img.save(path, format="WEBP", lossless=True, quality=100, method=6)
        else:  # jpeg and others -> jpeg high quality
            im = img.convert("RGB")
            im.save(path, format="JPEG", quality=95, optimize=True, progressive=True)

    save_lossless(dst)
    if os.path.getsize(dst) <= max_bytes:
        return True, "Lossless"

    # --- Step 2: gradual quality reduction (output format JPEG/WEBP) ---
    # Convert PNG without alpha to JPEG for better compression.
    target_fmt = "WEBP" if ext == ".webp" else "JPEG"
    base = img.convert("RGBA") if (has_alpha and target_fmt == "WEBP") else img.convert("RGB")

    best = None
    for quality in range(92, 29, -3):
        tmp = dst + ".tmp"
        if target_fmt == "WEBP":
            base.save(tmp, format="WEBP", quality=quality, method=6)
        else:
            base.save(tmp, format="JPEG", quality=quality, optimize=True, progressive=True)
        size = os.path.getsize(tmp)
        if size <= max_bytes:
            os.replace(tmp, dst)
            return True, f"Quality {quality}"
        best = (tmp, size, quality)

    # --- Step 3: reduce dimensions along with quality ---
    w, h = base.size
    scale = 0.9
    while min(w, h) * scale > 200:
        nw, nh = int(w * scale), int(h * scale)
        resized = base.resize((nw, nh), Image.LANCZOS)
        for quality in range(85, 39, -5):
            tmp = dst + ".tmp"
            if target_fmt == "WEBP":
                resized.save(tmp, format="WEBP", quality=quality, method=6)
            else:
                resized.save(tmp, format="JPEG", quality=quality, optimize=True, progressive=True)
            if os.path.getsize(tmp) <= max_bytes:
                os.replace(tmp, dst)
                return True, f"Dimensions {nw}x{nh}, Quality {quality}"
        scale -= 0.1

    # If nothing worked, keep the best attempt
    if best and os.path.exists(best[0]):
        os.replace(best[0], dst)
    return os.path.getsize(dst) <= max_bytes, "Smallest possible (still above limit)"


# ----------------------------- PDF Compression -----------------------------
def _gs_compress(src, dst, setting, gs):
    cmd = [
        gs, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5",
        f"-dPDFSETTINGS=/{setting}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
        "-dDetectDuplicateImages=true", "-dCompressFonts=true",
        f"-sOutputFile={dst}", src,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _gs_compress_dpi(src, dst, dpi, gs):
    cmd = [
        gs, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5",
        "-dNOPAUSE", "-dQUIET", "-dBATCH",
        "-dDetectDuplicateImages=true",
        "-dDownsampleColorImages=true", "-dColorImageDownsampleType=/Bicubic",
        f"-dColorImageResolution={dpi}",
        "-dDownsampleGrayImages=true", "-dGrayImageDownsampleType=/Bicubic",
        f"-dGrayImageResolution={dpi}",
        "-dDownsampleMonoImages=true", "-dMonoImageDownsampleType=/Subsample",
        f"-dMonoImageResolution={max(dpi, 300)}",
        f"-sOutputFile={dst}", src,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def compress_pdf(src: str, dst: str, max_bytes: int) -> tuple[bool, str]:
    gs = which_ghostscript()
    if not gs:
        shutil.copy2(src, dst)
        return os.path.getsize(dst) <= max_bytes, "Ghostscript not installed (direct copy)"

    orig = os.path.getsize(src)
    candidates = []

    # Step 1: standard profiles (least loss first)
    for setting in ("prepress", "printer", "ebook", "screen"):
        tmp = dst + f".{setting}.tmp"
        try:
            _gs_compress(src, tmp, setting, gs)
        except Exception:
            continue
        size = os.path.getsize(tmp)
        candidates.append((tmp, size))
        if size <= max_bytes:
            # Best (first) acceptable result = least loss
            os.replace(tmp, dst)
            for t, _ in candidates:
                if os.path.exists(t):
                    os.remove(t)
            return True, f"Profile /{setting}"

    # Step 2: reduce DPI of images inside the PDF
    for dpi in (200, 150, 120, 100, 72):
        tmp = dst + f".dpi{dpi}.tmp"
        try:
            _gs_compress_dpi(src, tmp, dpi, gs)
        except Exception:
            continue
        size = os.path.getsize(tmp)
        candidates.append((tmp, size))
        if size <= max_bytes:
            os.replace(tmp, dst)
            for t, _ in candidates:
                if os.path.exists(t):
                    os.remove(t)
            return True, f"DPI={dpi}"

    # None below limit: keep the smallest result
    best = min(candidates, key=lambda c: c[1]) if candidates else None
    if best:
        os.replace(best[0], dst)
        note = "Smallest possible (still above limit)"
    else:
        shutil.copy2(src, dst)
        note = "Compression failed (direct copy)"
    for t, _ in candidates:
        if os.path.exists(t):
            os.remove(t)
    return os.path.getsize(dst) <= max_bytes, note


# ----------------------------- Main Execution -----------------------------
def main():
    # Modern developer branding header
    print("=" * 60)
    print("  🚀 Media Compressor  v2.0")
    print("  Developed by Mohammad Ali Bazzazi")
    print("  https://mohammadalibazzazi.ir")
    print("=" * 60)

    # Check Pillow
    try:
        import PIL  # noqa
    except ImportError:
        print("Error: Pillow library is not installed. Run:")
        print("    pip install pillow")
        sys.exit(1)

    if not os.path.isdir(INPUT_DIR):
        os.makedirs(INPUT_DIR, exist_ok=True)
        print(f"Directory '{INPUT_DIR}' created. Place your files inside and run again.")
        sys.exit(0)

    # Interactive prompt for size limit
    while True:
        raw = input("\nEnter maximum file size (e.g., 500KB or 1MB): ").strip()
        try:
            max_bytes = parse_size(raw)
            if max_bytes <= 0:
                raise ValueError
            break
        except ValueError as e:
            print(f"  Invalid input: {e}")

    print(f"\nSelected size limit: {human(max_bytes)}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = []
    for root, _, names in os.walk(INPUT_DIR):
        for name in names:
            if name.startswith("."):
                continue
            files.append(os.path.join(root, name))

    if not files:
        print(f"No files found in '{INPUT_DIR}'.")
        sys.exit(0)

    print(f"Number of files: {len(files)}\n" + "-" * 60)

    stats = {"ok": 0, "over": 0, "skip": 0}
    for path in sorted(files):
        rel = os.path.relpath(path, INPUT_DIR)
        ext = os.path.splitext(path)[1].lower()
        dst = os.path.join(OUTPUT_DIR, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        orig = os.path.getsize(path)

        try:
            if ext in IMAGE_EXTS:
                ok, note = compress_image(path, dst, max_bytes)
            elif ext in PDF_EXTS:
                ok, note = compress_pdf(path, dst, max_bytes)
            else:
                shutil.copy2(path, dst)
                print(f"[SKIP] {rel}  (unsupported format, copied)")
                stats["skip"] += 1
                continue
        except Exception as e:
            shutil.copy2(path, dst)
            print(f"[ERR ] {rel}  ({e}) → direct copy")
            stats["skip"] += 1
            continue

        new = os.path.getsize(dst)
        pct = (1 - new / orig) * 100 if orig else 0
        flag = "OK " if ok else "OVER"
        if ok:
            stats["ok"] += 1
        else:
            stats["over"] += 1
        print(f"[{flag}] {rel}\n       {human(orig)} → {human(new)} "
              f"({pct:+.0f}%)  | {note}")

    print("-" * 60)
    print(f"Done. Below limit: {stats['ok']} | Above limit: {stats['over']} | Copied/Skipped: {stats['skip']}")
    print(f"Outputs are in the '{OUTPUT_DIR}' folder.")
    print("=" * 60)
    print("  Thanks for using Media Compressor!")
    print("  © 2026 Mohammad Ali Bazzazi")
    print("=" * 60)


if __name__ == "__main__":
    main()
