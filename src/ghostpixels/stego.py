from PIL import Image

from ghostpixels.errors import CapacityError

CHANNELS = 3
BITS_PER_BYTE = 8


def _channels(image: Image.Image) -> bytearray:
    return bytearray(image.convert("RGB").tobytes())


def capacity(image: Image.Image) -> int:
    return (image.width * image.height * CHANNELS) // BITS_PER_BYTE


def embed(image: Image.Image, data: bytes) -> Image.Image:
    data_size = len(data)
    image_size = capacity(image)
    # Size guard
    if data_size > image_size:
        raise CapacityError(f"Data is {data_size} bytes, but the image can only hold {image_size} bytes")
    
    channels = _channels(image)
    index = 0
    for byte in data:
        for i in range(BITS_PER_BYTE - 1, -1, -1):
            bit = (byte >> i) & 1

            # Clear the last bit (& 0xFE), then set it to our bit (| bit).
            channels[index] = (channels[index] & 0xFE) | bit
            index += 1
    return Image.frombytes("RGB", image.size, bytes(channels))


def extract(image: Image.Image, length: int) -> bytes:
    image_size = capacity(image)
    # Size guard
    if length > image_size:
        raise CapacityError(f"Requested {length:,} bytes, but the image can only hold {image_size:,} bytes")

    channels = _channels(image)
    result = bytearray()
    index = 0
    for _ in range(length):
        byte = 0
        for _ in range(BITS_PER_BYTE):
            bit = channels[index] & 1
            byte = (byte << 1) | bit
            index += 1
        result.append(byte)
    return bytes(result)
