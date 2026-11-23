"""Make homepage crest assets transparent, square, and evenly padded."""
from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "assets" / "images"
OUT = ROOT / "crests"
SIZE = 256
PAD = 22

FILES = [
    "Yangon University Logo.webp",
    "Mandalay University logo.webp",
    "Dagon University logo.webp",
    "East Yangon University Logo.webp",
    "Yadabon University logo.webp",
    "Mawlamyine university logo.webp",
    "NSPU logo.webp",
    "ytu-removebg-preview.webp",
    "wytu-removebg-preview.webp",
    "uit-removebg-preview.webp",
    "UM2-removebg-preview.webp",
    "PU(Dawei)logo.webp",
    "PU(Kyaing Tong)logo.webp",
    "PU(Maubin)logo.webp",
    "PU(Panglong)logo.webp",
    "PU(Bamaw).webp",
    "PU(Lashio).webp",
    "PU(Myeik).webp",
    "TU_Kalay__logo-removebg-preview.webp",
    "TU_Magway__logo-removebg-preview.webp",
    "TU_Mohywa__logo-removebg-preview.webp",
    "TU_Myitkyina__logo-removebg-preview.webp",
    "TU_Pakokku__logo-removebg-preview.webp",
    "TU_Sagaing__logo-removebg-preview.webp",
    "hmawbi-removebg-preview.webp",
    "thanlin-removebg-preview.webp",
    "loikaw_tu_-removebg-preview.webp",
    "pathein_tu_-removebg-preview.webp",
    "pyay_tu_-removebg-preview.webp",
    "sittwe_tu_-removebg-preview.webp",
    "taunggyi_tu_-removebg-preview.webp",
    "taungoo_tu_-removebg-preview.webp",
    "HInthadaCU_logo-removebg-preview.webp",
    "Hpa-anCU_logo-removebg-preview.webp",
    "PatheinCU_logo-removebg-preview.webp",
    "PyayCU_logo-removebg-preview.webp",
    "SittweCU_logo-removebg-preview.webp",
    "ThatonCU_logo-removebg-preview.webp",
    "p1__1_-removebg-preview.webp",
    "p1__2_-removebg-preview.webp",
    "p1__3_-removebg-preview.webp",
    "p1__4_-removebg-preview.webp",
    "p1__5_-removebg-preview.webp",
    "p1__6_-removebg-preview.webp",
    "p1__8_-removebg-preview.webp",
    "p1__9_-removebg-preview.webp",
    "dentistry-removebg-preview.webp",
]


def near_white(r: int, g: int, b: int, a: int, thr: int = 248) -> bool:
    return a > 8 and r >= thr and g >= thr and b >= thr


def near_black(r: int, g: int, b: int, a: int, thr: int = 18) -> bool:
    return a > 8 and r <= thr and g <= thr and b <= thr


def flood_clear(im: Image.Image, predicate) -> Image.Image:
    w, h = im.size
    px = im.load()
    seen = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def push(x: int, y: int) -> None:
        if x < 0 or y < 0 or x >= w or y >= h or seen[y][x]:
            return
        r, g, b, a = px[x, y]
        if a < 8 or predicate(r, g, b, a):
            seen[y][x] = True
            q.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    while q:
        x, y = q.popleft()
        r, g, b, a = px[x, y]
        if a >= 8 and predicate(r, g, b, a):
            px[x, y] = (r, g, b, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nx < 0 or ny < 0 or nx >= w or ny >= h or seen[ny][nx]:
                continue
            rr, gg, bb, aa = px[nx, ny]
            if aa < 8 or predicate(rr, gg, bb, aa):
                seen[ny][nx] = True
                q.append((nx, ny))
    return im


def to_square(im: Image.Image, size: int = SIZE, pad: int = PAD) -> Image.Image:
    bbox = im.split()[-1].getbbox()
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if not bbox:
        return canvas
    cropped = im.crop(bbox)
    cw, ch = cropped.size
    max_inner = size - pad * 2
    scale = min(max_inner / cw, max_inner / ch)
    nw = max(1, int(round(cw * scale)))
    nh = max(1, int(round(ch * scale)))
    resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas.paste(resized, ((size - nw) // 2, (size - nh) // 2), resized)
    return canvas


def slug(name: str) -> str:
    keep = []
    for ch in Path(name).stem:
        keep.append(ch.lower() if ch.isalnum() else "-")
    s = "".join(keep)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-") + ".webp"


def process(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 0 and r > 252 and g > 252 and b > 252:
                px[x, y] = (255, 255, 255, a)

    corners = [
        im.getpixel((1, 1)),
        im.getpixel((w - 2, 1)),
        im.getpixel((1, h - 2)),
        im.getpixel((w - 2, h - 2)),
    ]
    blackish = sum(1 for r, g, b, a in corners if near_black(r, g, b, a, 25))

    flood_clear(im, lambda r, g, b, a: near_white(r, g, b, a, 242))
    if blackish >= 2:
        flood_clear(im, lambda r, g, b, a: near_black(r, g, b, a, 22))
    flood_clear(im, lambda r, g, b, a: near_white(r, g, b, a, 235))
    return to_square(im)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    ok = 0
    for name in FILES:
        src = ROOT / name
        if not src.exists():
            print("MISSING", name)
            continue
        out = OUT / slug(name)
        try:
            process(src).save(out, "WEBP", quality=92, method=6)
            ok += 1
            print("OK", name, "->", out.name)
        except Exception as exc:  # noqa: BLE001
            print("FAIL", name, exc)
    print(f"DONE {ok}/{len(FILES)} -> {OUT}")


if __name__ == "__main__":
    main()
