<div align="center">

# 📦 Media Compressor

**Fast, smart, and configurable image & PDF compression with size targeting**

<p>
  <img src="https://img.shields.io/badge/Python-3.7%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.7+" />
  <img src="https://img.shields.io/badge/Pillow-10.0%2B-3766AB?style=for-the-badge&logo=pillow&logoColor=white" alt="Pillow 10.0+" />
  <img src="https://img.shields.io/badge/Ghostscript-9.0%2B-4CAF50?style=for-the-badge" alt="Ghostscript 9.0+" />
  <img src="https://img.shields.io/badge/License-MIT-F5C542?style=for-the-badge" alt="MIT License" />
  <img src="https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-6C757D?style=for-the-badge" alt="Cross-platform" />
</p>

</div>

---

## Overview

**Media Compressor** is a Python command-line tool designed to reduce the size of images and PDF files to a user-defined target while keeping visual quality as high as possible.

It follows a progressive compression workflow:

1. **Apply lossless optimizations first**
   Uses built-in image optimizations and external tools such as `optipng` and `jpegoptim` when available.

2. **Reduce quality gradually if needed**
   If the target size is not reached, it lowers quality in controlled steps.

3. **Resize only as a last resort**
   When necessary, it reduces image dimensions while preserving the aspect ratio.

4. **Compress PDFs intelligently**
   Uses Ghostscript compression profiles and DPI-based downsampling to reduce PDF size effectively.

The tool processes files inside an `input` directory and writes the compressed results to `output`, while preserving the original folder structure and file names.

---

## Key Features

| Feature                           | Description                                                                       |
| --------------------------------- | --------------------------------------------------------------------------------- |
| **Multi-format support**          | JPEG, PNG, WEBP, BMP, TIFF, GIF (static), and PDF                                 |
| **Target-based compression**      | Compress files to a specified maximum size such as `500KB` or `2MB`               |
| **Lossless-first pipeline**       | Tries safe optimizations before applying quality reduction                        |
| **Adaptive quality control**      | Gradually adjusts JPEG/WEBP quality to achieve the best possible result           |
| **Aspect-ratio-safe resizing**    | Reduces dimensions only when needed, without distorting images                    |
| **PDF compression support**       | Uses Ghostscript presets such as `/screen`, `/ebook`, `/printer`, and `/prepress` |
| **Graceful fallback behavior**    | Works even when optional external tools are unavailable                           |
| **Folder structure preservation** | Keeps input subdirectories intact in the output directory                         |
| **Clear reporting**               | Shows original size, compressed size, compression ratio, and method used          |
| **Cross-platform**                | Supports Linux, macOS, and Windows                                                |

---

## Quick Start

### Prerequisites

* Python 3.7 or higher
* Pillow

```bash
pip install pillow
```

### Optional tools

For better compression results, install the following:

* **Ghostscript** for PDF compression
* **optipng** for PNG optimization
* **jpegoptim** for JPEG optimization

### Usage

Place your files inside the `input` folder and run the script.

```bash
python compressor.py --input input --output output --target-size 500KB
```

Example target sizes:

```bash
python compressor.py --target-size 1MB
python compressor.py --target-size 250KB
```

---

## How It Works

* Scans all supported files in the input directory
* Applies the best available optimization method for each file type
* Tries to reach the target size with minimal quality loss
* Saves the compressed file in the output directory
* Preserves subfolder structure and file names

---

## Notes

* Static GIFs are supported; animated GIF handling may vary depending on implementation.
* PDF compression quality depends on the installed Ghostscript version and selected preset.
* Results may differ depending on the original file type, content, and compression target.

## License

All Rights are reserved for Mohammad Ali Bazzazi
