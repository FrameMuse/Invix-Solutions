#!/usr/bin/env python3

import os
import struct
import sys
import zlib
from uuid import uuid4

import httpx

API_URL = os.getenv("API_URL", "http://localhost:18000").rstrip("/")
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN", "change-me")

PRODUCTS = [
    ("Кружка", (188, 86, 68)),
    ("Футболка", (62, 104, 154)),
    ("Блокнот", (86, 132, 92)),
]


def png_chunk(name: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(name + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + name + data + struct.pack(">I", checksum)


def solid_png(color: tuple[int, int, int], size: int = 128) -> bytes:
    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    row = b"\x00" + bytes(color) * size
    pixels = zlib.compress(row * size, 9)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", pixels)
        + png_chunk(b"IEND", b"")
    )


def existing_titles(client: httpx.Client) -> set[str]:
    titles: set[str] = set()
    offset = 0

    while True:
        response = client.get("/api/products", params={"limit": 100, "offset": offset})
        response.raise_for_status()
        items = response.json()
        titles.update(item["title"] for item in items)

        if len(items) < 100:
            return titles

        offset += 100


def upload_products(client: httpx.Client) -> None:
    titles = existing_titles(client)

    for title, color in PRODUCTS:
        if title in titles:
            print(f"Уже есть: {title}")
            continue

        response = client.post(
            "/internal/products",
            headers={"X-Service-Token": SERVICE_TOKEN},
            data={"title": title},
            files={"photo": (f"{uuid4().hex}.png", solid_png(color), "image/png")},
        )
        response.raise_for_status()
        print(f"Добавлен: {title}")


def main() -> int:
    try:
        with httpx.Client(base_url=API_URL, timeout=30.0) as client:
            upload_products(client)
    except httpx.HTTPError as error:
        print(f"Не удалось обратиться к API: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
