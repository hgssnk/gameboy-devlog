#!/usr/bin/env python3
"""仮背景を作る。John の絵に差し替えるまでのつなぎ。作り込みすぎない。

使い方:
  python3 src/tools/placeholder.py room_night            # src/assets/bg/room_night.png を作る
  python3 src/tools/placeholder.py room_night --preview out.png   # 確認用に、5倍に拡大した絵も作る

絵は 160x112、4色（0=白 1=明るい灰 2=暗い灰 3=黒）。
一点透視で、床の線は消失点 VP に向かって集まる。手前は暗く、奥は明るく。
"""
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
W, H = 160, 112
PALETTE = [(255, 255, 255), (170, 170, 170), (85, 85, 85), (0, 0, 0)]


class Canvas:
    def __init__(self, bg):
        self.px = [[bg] * W for _ in range(H)]

    def dot(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = c

    def rect(self, c, x, y, w, h):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.dot(xx, yy, c)

    def line(self, c, x0, y0, x1, y1, dash=0):
        """ブレゼンハムの直線。dash>0 なら、その長さごとに描く・描かないを繰り返す"""
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err, n = dx + dy, 0
        while True:
            if not dash or (n // dash) % 2 == 0:
                self.dot(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
            n += 1

    def polygon(self, c, pts):
        """多角形を塗る（走査線）"""
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(len(pts)):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
                if y0 == y1:
                    continue
                if min(y0, y1) <= y < max(y0, y1):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(round(xs[i]), round(xs[i + 1]) + 1):
                    self.dot(x, y, c)

    def ellipse(self, c, cx, cy, rx, ry):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    self.dot(x, y, c)


def write_png(path, canvas, scale=1, bits=2):
    """インデックスカラー PNG。bits=2 なら4色（ゲーム用）、bits=8 なら拡大した確認用"""
    rows = []
    for row in canvas.px:
        row = [c for c in row for _ in range(scale)]
        if bits == 2:
            row += [0] * (-len(row) % 4)
            data = bytes(sum(row[i + k] << (6 - 2 * k) for k in range(4)) for i in range(0, len(row), 4))
        else:
            data = bytes(row)
        rows += [b"\x00" + data] * scale

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W * scale, H * scale, bits, 3, 0, 0, 0))
    png += chunk(b"PLTE", bytes(v for rgb in PALETTE for v in rgb))
    png += chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
    png += chunk(b"IEND", b"")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(png)


# ===== 部屋（夜） =====
def room_night():
    WALL, FLOOR = 2, 3
    VPX, VPY = 78, 46                   # 消失点
    BASE = 74                           # 壁と床の境目

    c = Canvas(WALL)
    c.rect(FLOOR, 0, BASE, W, H - BASE)

    # 壁に、モニターの光がにじむ（ディザ：近いほど密）
    mx, my = 103, 48
    for y in range(BASE):
        for x in range(W):
            d = ((x - mx) ** 2 + ((y - my) * 1.3) ** 2) ** 0.5
            if c.px[y][x] == WALL and ((d < 24 and (x + y) % 2 == 0) or (d < 34 and x % 2 == 0 and y % 2 == 0)):
                c.dot(x, y, 1)
    c.rect(1, 0, BASE - 1, W, 1)                                    # 壁の下の線

    # 床の線：消失点に向かう線と、手前ほど間が空く横線
    for y in (78, 84, 92, 103):
        c.line(2, 0, y, W - 1, y)
    for x_end in (-30, 45, 120, 195):
        y0 = BASE
        x0 = VPX + (x_end - VPX) * (y0 - VPY) / (H - 1 - VPY)
        c.line(2, round(x0), y0, x_end, H - 1)

    # 窓：黒い夜空、星、街のシルエット
    c.rect(1, 17, 12, 58, 49)
    c.rect(3, 20, 15, 52, 43)
    for x, y in ((24, 18), (33, 24), (28, 34), (52, 17), (62, 22), (66, 30), (56, 36), (38, 15)):
        c.dot(x, y, 0)
    c.dot(61, 19, 0); c.dot(60, 19, 0); c.dot(62, 19, 0); c.dot(61, 18, 0); c.dot(61, 20, 0)   # 大きな星
    for x, top, w in ((20, 46, 8), (28, 42, 6), (34, 48, 8), (46, 44, 7), (53, 40, 9), (62, 47, 10)):
        c.rect(2, x, top, w, 58 - top)
    c.rect(1, 44, 15, 3, 43)                                        # 窓の桟
    c.rect(1, 15, 60, 62, 3)                                        # 窓の下の出っ張り
    c.rect(3, 15, 63, 62, 1)

    # ベッド：上の面は明るく、手前の面は暗く
    c.polygon(1, [(14, 78), (66, 78), (69, 90), (8, 90)])
    c.rect(2, 8, 90, 61, 11)
    c.polygon(0, [(10, 79), (27, 79), (25, 86), (8, 86)])         # まくら
    for x in range(32, 65, 5):
        c.line(2, x, 84, x + 2, 84)
    for x in range(30, 63, 5):
        c.line(2, x, 88, x + 2, 88)
    c.rect(3, 8, 101, 61, 1)

    # 机：脚、天板
    c.rect(1, 85, 68, 2, 26)
    c.rect(1, 147, 68, 2, 26)
    c.rect(3, 86, 94, 1, 1)
    c.polygon(1, [(84, 64), (150, 64), (153, 68), (81, 68)])
    c.rect(0, 84, 64, 66, 1)
    c.rect(2, 81, 68, 72, 2)

    # 椅子
    c.rect(1, 111, 70, 4, 9)                                        # 背もたれ
    c.rect(1, 100, 79, 16, 3)                                       # 座面
    c.rect(1, 106, 82, 3, 12)                                       # 脚
    c.rect(1, 98, 94, 16, 2)                                        # 底

    # モニター：白い画面と、黒い縁
    c.rect(1, 89, 35, 28, 26)
    c.rect(3, 90, 36, 26, 24)
    c.rect(0, 92, 38, 22, 20)
    for i, y in enumerate((41, 45, 49, 53)):
        c.rect(3, 94, y, 18 - (i % 2) * 5, 2)
    c.dot(103, 40, 3)
    c.rect(3, 100, 61, 6, 4)

    # ターンテーブル
    c.rect(1, 118, 57, 28, 8)
    c.rect(3, 119, 58, 26, 6)
    c.ellipse(1, 129, 61, 9, 2)
    c.ellipse(3, 129, 61, 8, 1)
    c.dot(129, 61, 0)
    c.line(0, 140, 58, 137, 62)                                     # トーンアーム

    # 右はしの小物入れ
    c.rect(1, 150, 74, 10, 28)
    for x in (152, 155, 158):
        c.rect(0, x, 70, 1, 6)
    c.rect(3, 150, 102, 10, 1)

    return c


SCENES = {"room_night": room_night}


def main():
    args = sys.argv[1:]
    if not args or args[0] not in SCENES:
        sys.exit(f"使い方: placeholder.py {{{'|'.join(SCENES)}}} [--preview 出力.png]")
    name = args[0]
    canvas = SCENES[name]()
    out = ROOT / "src" / "assets" / "bg" / f"{name}.png"
    write_png(out, canvas)
    print(f"作りました: {out.relative_to(ROOT)}")
    if "--preview" in args:
        prev = Path(args[args.index("--preview") + 1])
        write_png(prev, canvas, scale=5, bits=8)
        print(f"確認用: {prev}")


if __name__ == "__main__":
    main()
