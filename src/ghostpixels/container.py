"""Binary layout of the data hidden inside an image.

Layout:
    magic           4 bytes   b"GHPX", marks the image as containing our data
    version         1 byte    format version, currently 1
    flags           1 byte    bit 0 set = payload is encrypted
    name_length     2 bytes   length of the UTF-8 encoded filename
    payload_length  4 bytes   length of the payload
    filename        name_length bytes
    payload         payload_length bytes
"""

import struct
from dataclasses import dataclass

from ghostpixels.errors import CorruptDataError, NoHiddenDataError

MAGIC = b"GHPX"
VERSION = 1
FLAG_ENCRYPTED = 0b0000_0001

# > = big-endian, 4s = 4 raw bytes, B = 1-byte int, H = 2-byte int, I = 4-byte int
HEADER_FORMAT = ">4sBBHI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

MAX_NAME_LENGTH = 0xFFFF
_FORBIDDEN_NAME_CHARS = set("/\\:\0")


@dataclass(frozen=True)
class Header:
    """The fixed-size part at the start of the hidden data.

    Attributes:
        encrypted: Whether the payload is encrypted.
        name_length: Length of the UTF-8 encoded filename, in bytes.
        payload_length: Length of the payload, in bytes.
    """

    encrypted: bool
    name_length: int
    payload_length: int

    @property
    def total_size(self) -> int:
        """Size of the whole hidden block: header + filename + payload."""
        return HEADER_SIZE + self.name_length + self.payload_length


@dataclass(frozen=True)
class HiddenFile:
    """A file as it is stored inside an image.

    Attributes:
        filename: Plain filename without any folders, e.g. "secret.pdf".
        payload: The file contents, encrypted if `encrypted` is True.
        encrypted: Whether the payload is encrypted.
    """

    filename: str
    payload: bytes
    encrypted: bool


def pack(hidden: HiddenFile) -> bytes:
    """Build the bytes to embed: header, then filename, then payload.

    Args:
        hidden: The file to pack.

    Returns:
        The complete block of bytes, ready to be passed to `stego.embed`.

    Raises:
        ValueError: If the filename is not a plain filename or is too long.
    """
    if not _is_safe_filename(hidden.filename):
        raise ValueError(f"Not a plain filename: {hidden.filename!r}")

    name = hidden.filename.encode("utf-8")
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError("Filename is too long to store")

    flags = FLAG_ENCRYPTED if hidden.encrypted else 0
    header = struct.pack(HEADER_FORMAT, MAGIC, VERSION, flags, len(name), len(hidden.payload))
    return header + name + hidden.payload


def parse_header(data: bytes) -> Header:
    """Read and validate the header at the start of the data.

    Args:
        data: Bytes extracted from an image. Only the first `HEADER_SIZE`
            bytes are read; anything after them is ignored.

    Returns:
        The parsed header. Use `Header.total_size` to find out how many
        bytes to extract for `unpack`.

    Raises:
        NoHiddenDataError: If the data is too short or lacks the signature.
        CorruptDataError: If the format version is not supported.
    """
    if len(data) < HEADER_SIZE:
        raise NoHiddenDataError("Not enough data to contain a header")

    magic, version, flags, name_length, payload_length = struct.unpack_from(HEADER_FORMAT, data)
    if magic != MAGIC:
        raise NoHiddenDataError("No hidden data found in this image")
    if version != VERSION:
        raise CorruptDataError(f"Unsupported format version {version} (expected {VERSION})")

    return Header(
        encrypted=bool(flags & FLAG_ENCRYPTED),
        name_length=name_length,
        payload_length=payload_length,
    )


def unpack(data: bytes) -> HiddenFile:
    """Split a complete hidden block back into filename and payload.

    Args:
        data: The whole hidden block, at least `Header.total_size` bytes.

    Returns:
        The stored file. The payload is still encrypted if
        `HiddenFile.encrypted` is True.

    Raises:
        NoHiddenDataError: If the data lacks the signature.
        CorruptDataError: If the data is truncated, the version is not
            supported, or the stored filename is invalid or unsafe.
    """
    header = parse_header(data)
    if len(data) < header.total_size:
        raise CorruptDataError("Hidden data is shorter than its header says")

    name_end = HEADER_SIZE + header.name_length
    try:
        filename = data[HEADER_SIZE:name_end].decode("utf-8")
    except UnicodeDecodeError:
        raise CorruptDataError("Stored filename is not valid UTF-8") from None

    # The image may come from anyone, so never trust the stored name blindly.
    if not _is_safe_filename(filename):
        raise CorruptDataError(f"Stored filename is not safe to use: {filename!r}")

    payload = data[name_end:header.total_size]
    return HiddenFile(filename=filename, payload=payload, encrypted=header.encrypted)


def _is_safe_filename(name: str) -> bool:
    """True if `name` is a plain filename that cannot point outside a folder."""
    return name not in ("", ".", "..") and not (set(name) & _FORBIDDEN_NAME_CHARS)
