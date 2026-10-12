import argparse
import sys
from importlib.metadata import version
from pathlib import Path

from platformdirs import user_downloads_dir
from PIL import Image

from ghostpixels.container import HiddenFile, pack, unpack, parse_header, HEADER_SIZE
from ghostpixels.errors import GhostPixelsError, CapacityError, CorruptDataError
from ghostpixels.stego import embed, extract


def _output_dir(args: argparse.Namespace) -> Path:
    folder = args.output
    if folder is not None:
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    downloads = Path(user_downloads_dir())
    if not downloads.is_dir():
        raise GhostPixelsError(
            f"Your computer is weird, it has no Downloads folder ({downloads}). "
            "Use --output to choose where to save the result."
        )
    return downloads


def _unique_path(path: Path) -> Path:
    """Return `path`, or `name (1).ext`, `name (2).ext`, ... if it is taken."""
    if not path.exists():
        return path

    n = 1
    while True:
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def run_hide(args: argparse.Namespace) -> int:
    if args.encrypt:
        raise GhostPixelsError("Encryption is not implemented yet")

    payload = args.file.read_bytes()
    hidden_file = HiddenFile(filename=args.file.name, payload=payload, encrypted=args.encrypt)
    packed = pack(hidden_file)

    with Image.open(args.image) as image:
        result = embed(image, packed)

    output_path = _unique_path(_output_dir(args) / f"{args.image.stem}_hidden.png")
    result.save(output_path, format="PNG")

    print(f"Hid {args.file.name} ({len(payload):,} bytes) in {output_path}")
    return 0


def run_reveal(args: argparse.Namespace) -> int:
    with Image.open(args.image) as image:
        header_result = extract(image=image, length=HEADER_SIZE)
        header = parse_header(header_result)
        if header.encrypted:
            raise GhostPixelsError("This file is encrypted; decryption is not implemented yet")

        # A header claiming more data than the image holds means the data is damaged.
        try:
            result = extract(image=image, length=header.total_size)
        except CapacityError:
            raise CorruptDataError("The hidden data is damaged or incomplete") from None

    hidden_file = unpack(result)
    output_path = _unique_path(_output_dir(args) / hidden_file.filename)
    output_path.write_bytes(hidden_file.payload)

    print(f"Revealed {hidden_file.filename} ({len(hidden_file.payload):,} bytes) to {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ghostpixels", 
        description="Hides, Reveals and optionally encrypts files into images"
        )

    parser.add_argument("--version", action="version", version=f"%(prog)s {version('ghostpixels')}")
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="commands")

    #The hide command and its flags
    hide_parser = subparsers.add_parser("hide", help="hide a file inside an image")
    hide_parser.add_argument("-i", "--image", type=Path, required=True, help="Path of image data should be hidden in")
    hide_parser.add_argument("-f", "--file", type=Path, required=True, help="File that should be hidden")
    hide_parser.add_argument("-e", "--encrypt", action="store_true", help="Encrypt file before hiding it in image")
    hide_parser.add_argument("-o", "--output", type=Path, help="folder to save the result in. Default is Downloads")
    hide_parser.set_defaults(func=run_hide)

    #The reveal command and its flags
    reveal_parser = subparsers.add_parser("reveal", help="Reveals and extracts a file hidden in an image")
    reveal_parser.add_argument("-i", "--image", type=Path, required=True, help="Path of image data is hidden in")
    reveal_parser.add_argument("-o", "--output", type=Path, help="folder to save the result in. Default is Downloads")
    reveal_parser.set_defaults(func=run_reveal)



    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (GhostPixelsError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1