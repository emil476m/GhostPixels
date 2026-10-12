# GhostPixels

A small command-line tool that hides a file inside an image, and gets it back out again.

GhostPixels uses **LSB steganography**: each byte of your file is spread across the
lowest bit of the image's colour values. Each colour changes by at most 1 out of 255,
so the image looks the same as before.

> **Note:** Password encryption (`--encrypt`) is planned but not implemented yet.

## Requirements

- Python 3.13 or newer

## Installation

Clone the repository and run the following from the project folder:

```powershell
# Create and activate a virtual environment (Windows / PowerShell)
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1

# Install GhostPixels and its dependencies
pip install -e .
```

On macOS / Linux, activate the environment with `source .venv/bin/activate` instead.

## Usage

### Hide a file in an image

```powershell
ghostpixels hide -i cat.jpg -f secret.txt
```

This saves `cat_hidden.png` to your Downloads folder.

### Reveal a hidden file

```powershell
ghostpixels reveal -i cat_hidden.png
```

This saves the original file (`secret.txt`) to your Downloads folder.

### Options

| Command | Option | Description |
|---|---|---|
| `hide` | `-i`, `--image` | Image to hide the file in (required) |
| `hide` | `-f`, `--file` | File to hide (required) |
| `hide` | `-o`, `--output` | Folder to save the result in (default: Downloads) |
| `reveal` | `-i`, `--image` | Image that contains a hidden file (required) |
| `reveal` | `-o`, `--output` | Folder to save the result in (default: Downloads) |

Run `ghostpixels --help` or `ghostpixels <command> --help` for more details.


## Good to know

- **The result is always a PNG.** You can use a JPEG as input, but the output must be
  lossless. JPEG compression would destroy the hidden data.
- **Don't send the image through apps that recompress images** (many chat apps and
  social media). Send it as a file attachment instead.
- **Capacity is limited.** An image can hold roughly `width × height × 3 / 8` bytes.
  For example, a 1920×1080 image holds about 760 KB.
