from __future__ import annotations

import imagehash
from PIL import Image


def generate_phash(image: Image.Image) -> str:
    return str(imagehash.phash(image))

