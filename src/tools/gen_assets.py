#!/usr/bin/env python3
"""ドット絵とテキストから、ゲームボーイ用の C ソースを作る。

入力:
  src/scenario/*.txt              シナリオのテキスト
  src/tools/font/misaki_gothic.bdf  美咲フォント（8x8ドット。src/tools/font/misaki.txt を参照）
出力:
  build/gen/assets.h, build/gen/assets.c

絵は、下の「絵」の部分に、元のブラウザ版（layers/objects.js）と同じ
rect(色, x, y, w, h) で書いてある。色は 0(白) 1(薄い灰) 2(濃い灰) 3(黒)。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "build" / "gen"
FONT = ROOT / "src" / "tools" / "font" / "misaki_gothic.bdf"
TEXTS = sorted((ROOT / "src" / "scenario").glob("*.txt"))

MAX_SLOTS = 36          # 1画面で同時に VRAM へ載せる文字の数（本文32 + 名前3 に余裕）
LINES, COLS = 2, 16     # 1画面 = 2行、1行16文字（画面の幅20マスから、左右の余白を引いた数）


# ===== 絵 =====
class Img:
    def __init__(self, w, h, bg=0):
        self.w, self.h = w, h
        self.px = [[bg] * w for _ in range(h)]

    def rect(self, c, x, y, w, h):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px[yy][xx] = c
        return self

    def tile(self, tx, ty):
        """8x8 タイル1枚を、2bpp の16バイトにする"""
        out = []
        for row in self.px[ty * 8:ty * 8 + 8]:
            lo = hi = 0
            for c in row[tx * 8:tx * 8 + 8]:
                lo = (lo << 1) | (c & 1)
                hi = (hi << 1) | ((c >> 1) & 1)
            out += [lo, hi]
        return out

    def tiles_rowmajor(self):       # 背景用：左上, 右上, 左下, 右下
        return [self.tile(x, y) for y in range(self.h // 8) for x in range(self.w // 8)]

    def tiles_colmajor(self):       # 8x16スプライト用：左の上下, 右の上下
        return [self.tile(x, y) for x in range(self.w // 8) for y in range(self.h // 8)]


def floor():
    return Img(16, 16, 1)


def solid(c):
    return Img(8, 8, c)


def make_bg_images():
    """背景タイル。名前 → 画像。順番がそのままタイル番号になる"""
    imgs = []

    def add(name, img):
        imgs.append((name, img))

    add("BLANK", solid(0))                                         # 0番は白（空白）
    add("BLACK", solid(3))                                         # 黒（会話ウィンドウの上の帯、暗い画面）
    add("BOTLINE", Img(8, 8, 0).rect(3, 0, 0, 8, 2))               # 会話ウィンドウの下の線
    add("CURSOR", Img(8, 8, 0).rect(3, 0, 2, 7, 2).rect(3, 1, 4, 5, 2).rect(3, 2, 6, 3, 1))  # 続きの矢印

    add("FLOOR", floor())
    add("WALL", Img(16, 16, 3))
    add("WALL2", Img(16, 16, 3).rect(2, 5, 4, 5, 6))
    add("SHOPDOOR", floor().rect(0, 2, 2, 12, 14).rect(3, 4, 5, 8, 2).rect(3, 4, 9, 6, 2))
    add("VENDING", floor().rect(2, 3, 1, 10, 15).rect(0, 5, 3, 6, 5).rect(3, 5, 11, 6, 2))
    add("BOARD", floor().rect(3, 7, 9, 2, 7).rect(3, 2, 2, 12, 8).rect(0, 4, 4, 3, 4).rect(0, 9, 4, 3, 4))
    add("VIADUCT", Img(16, 16, 2).rect(3, 2, 5, 12, 11))
    add("BOX", floor().rect(2, 1, 3, 14, 12).rect(3, 1, 7, 14, 1).rect(3, 1, 11, 14, 1)
        .rect(0, 3, 1, 2, 3).rect(0, 7, 1, 2, 3).rect(0, 11, 1, 2, 3))
    add("RADIO", floor().rect(2, 2, 4, 12, 10).rect(3, 4, 6, 4, 4).rect(0, 10, 7, 2, 2).rect(0, 11, 1, 1, 3))
    add("OWNER", floor().rect(3, 4, 6, 8, 9).rect(2, 4, 2, 8, 5).rect(0, 5, 4, 6, 1))
    add("EXIT", floor().rect(2, 2, 0, 12, 16).rect(0, 2, 13, 12, 3))
    # 暗い画面に浮かぶ、中古屋の看板（3x2タイル）
    add("SIGN", Img(24, 16, 3).rect(0, 0, 0, 24, 14).rect(3, 4, 4, 16, 2).rect(3, 4, 8, 10, 2))
    return imgs


def make_sprite_images(note_glyph):
    """スプライト（8x16モード）。1つ4タイル。番号は4の倍数になる"""
    def pose(eye):
        img = Img(16, 16, 0).rect(3, 4, 5, 8, 10).rect(2, 4, 2, 8, 5)     # からだ、あたま
        if eye:
            img.rect(1, eye[0], eye[1], 2, 2)                              # かお（向き）
        return img

    imgs = [
        ("PLAYER_DOWN", pose((6, 4))),
        ("PLAYER_UP", pose(None)),
        ("PLAYER_SIDE", pose((5, 4))),      # 左向き。右向きは左右反転して使う
    ]
    note = Img(8, 16, 0)
    for y, row in enumerate(note_glyph):                                   # ♪：美咲フォントの字を上半分に
        for x in range(8):
            if row & (0x80 >> x):
                note.px[y][x] = 3
    imgs.append(("NOTE", note))
    return imgs


# ===== フォント（BDF） =====
def load_bdf(path):
    """{ 文字コード: 8バイト(8行分。左端が最上位ビット) }"""
    glyphs, cur = {}, None
    fb_h = fb_yo = 0
    for line in path.read_text(encoding="ascii", errors="ignore").splitlines():
        if line.startswith("FONTBOUNDINGBOX"):
            _, _, fb_h, _, fb_yo = line.split()
            fb_h, fb_yo = int(fb_h), int(fb_yo)
        elif line.startswith("ENCODING"):
            cur = {"code": int(line.split()[1]), "rows": [], "bitmap": False}
        elif line.startswith("BBX") and cur is not None:
            _, w, h, xo, yo = line.split()
            cur.update(w=int(w), h=int(h), xo=int(xo), yo=int(yo))
        elif line.startswith("BITMAP"):
            cur["bitmap"] = True
        elif line.startswith("ENDCHAR"):
            if cur and cur["code"] >= 0:
                top = fb_h + fb_yo - (cur["yo"] + cur["h"])
                rows = [0] * 8
                for i, hexrow in enumerate(cur["rows"]):
                    if 0 <= top + i < 8:
                        rows[top + i] = (int(hexrow[:2], 16) >> cur["xo"]) & 0xFF
                glyphs[cur["code"]] = rows
            cur = None
        elif cur and cur.get("bitmap"):
            cur["rows"].append(line.strip())
    return glyphs


def glyph_tile(rows):
    """文字は黒(色3)で描く。2bpp では、下位・上位ビットが同じ"""
    out = []
    for r in rows:
        out += [r, r]
    return out


# ===== テキスト =====
def parse_texts(paths):
    """[ (名前, [ (who, [行,行]) , ...]) , ... ]"""
    sections, cur = [], None
    for path in paths:
        for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            m = re.fullmatch(r"\[(\w+)\]", line)
            if m:
                cur = (m.group(1), [])
                sections.append(cur)
                continue
            if cur is None:
                sys.exit(f"{path}:{n}: 最初に [名前] が必要です")
            who = ""
            i = line.find("：")
            if 0 < i <= 3:
                who, line = line[:i], line[i + 1:]
            rows = line.split("/")
            if len(rows) > LINES or any(len(r) > COLS for r in rows):
                sys.exit(f"{path}:{n}: 1画面は{LINES}行まで、1行{COLS}文字までです: {raw}")
            cur[1].append((who, rows))
    return sections


def c_bytes(data, per_line=16):
    lines = []
    for i in range(0, len(data), per_line):
        lines.append("    " + ", ".join(f"0x{b:02X}" for b in data[i:i + per_line]) + ",")
    return "\n".join(lines)


def main():
    font = load_bdf(FONT)
    sections = parse_texts(TEXTS)

    # 使う文字を、出てきた順に並べる
    gids = {}                  # 文字 → フォント内の番号
    def gid(ch):
        if ord(ch) not in font:
            sys.exit(f"美咲フォントに '{ch}' (U+{ord(ch):04X}) がありません")
        return gids.setdefault(ch, len(gids))

    screens = []               # (セクション名, 画面のC初期化子)
    sec_out = []
    for name, items in sections:
        body = []
        for who, rows in items:
            slots_body, slots_who = [], []
            cells = [[0xFF] * COLS for _ in range(LINES)]
            for r, row in enumerate(rows):
                for c, ch in enumerate(row):
                    if ch in " 　":
                        continue
                    g = gid(ch)
                    if g not in slots_body:
                        slots_body.append(g)
                    cells[r][c] = slots_body.index(g)
            who_cells = [0xFF] * 3
            for k, ch in enumerate(who):
                g = gid(ch)
                if g not in slots_who:
                    slots_who.append(g)
                who_cells[k] = len(slots_body) + slots_who.index(g)
            glyph = slots_body + slots_who
            if len(glyph) > MAX_SLOTS:
                sys.exit(f"[{name}] 1画面の文字の種類が多すぎます: {rows}")
            glyph += [0] * (MAX_SLOTS - len(glyph))
            body.append(
                "    { %d, %d,\n      { %s },\n      { %s },\n      { { %s }, { %s } } },"
                % (len(slots_body), len(slots_who),
                   ", ".join(map(str, glyph)),
                   ", ".join(map(str, who_cells)),
                   ", ".join(map(str, cells[0])),
                   ", ".join(map(str, cells[1])))
            )
        sec_out.append((name, len(items), body))
    if len(gids) > 256:
        sys.exit("文字の種類が256を超えました（uint8_t では足りません）")

    bg = make_bg_images()
    spr = make_sprite_images(font[ord("♪")])

    OUT.mkdir(parents=True, exist_ok=True)

    # ---- assets.h ----
    h = ["/* 自動生成：tools/gen_assets.py。手で書き換えない */",
         "#ifndef ASSETS_H", "#define ASSETS_H", "#include <stdint.h>", ""]
    n = 0
    h.append("/* 背景タイル番号（メタタイルは、左上・右上・左下・右下の4枚が並ぶ。この番号は左上） */")
    for name, img in bg:
        h.append(f"#define T_{name} {n}")
        n += (img.w // 8) * (img.h // 8)
    h.append(f"#define BG_TILE_COUNT {n}")
    h.append("")
    n = 0
    h.append("/* スプライトのタイル番号（8x16モード） */")
    for name, img in spr:
        h.append(f"#define S_{name} {n}")
        n += (img.w // 8) * (img.h // 8)
    h.append(f"#define SPR_TILE_COUNT {n}")
    h.append("")
    h.append("extern const uint8_t bg_tiles[];")
    h.append("extern const uint8_t spr_tiles[];")
    h.append("extern const uint8_t font_tiles[];   /* 1文字 = 16バイト */")
    h.append("")
    h.append(f"#define MAX_SLOTS {MAX_SLOTS}")
    h.append("typedef struct {")
    h.append("    uint8_t n_body;               /* 本文の文字の種類 */")
    h.append("    uint8_t n_who;                /* 話す人の文字の種類 */")
    h.append("    uint8_t glyph[MAX_SLOTS];     /* 本文、話す人の順に、フォント内の番号 */")
    h.append("    uint8_t who[3];               /* 話す人の各文字の、glyph の番号（なしは 0xFF） */")
    h.append(f"    uint8_t cell[{LINES}][{COLS}];        /* 本文の各マスの、glyph の番号（空白は 0xFF） */")
    h.append("} Screen;")
    h.append("")
    h.append("#define SAY(name) say(name, name##_N)")
    for name, count, _ in sec_out:
        h.append(f"extern const Screen txt_{name}[];")
        h.append(f"#define txt_{name}_N {count}")
    h += ["", "#endif", ""]
    (OUT / "assets.h").write_text("\n".join(h), encoding="utf-8")

    # ---- assets.c ----
    c = ["/* 自動生成：tools/gen_assets.py。手で書き換えない */", '#include "assets.h"', ""]
    bg_data = [b for _, img in bg for t in img.tiles_rowmajor() for b in t]
    spr_data = [b for _, img in spr for t in img.tiles_colmajor() for b in t]
    font_data = [b for ch in gids for b in glyph_tile(font[ord(ch)])]
    c.append("const uint8_t bg_tiles[] = {\n" + c_bytes(bg_data) + "\n};\n")
    c.append("const uint8_t spr_tiles[] = {\n" + c_bytes(spr_data) + "\n};\n")
    c.append(f"/* {len(gids)} 文字：{''.join(gids)} */")
    c.append("const uint8_t font_tiles[] = {\n" + c_bytes(font_data) + "\n};\n")
    for name, _, body in sec_out:
        c.append(f"const Screen txt_{name}[] = {{\n" + "\n".join(body) + "\n};\n")
    (OUT / "assets.c").write_text("\n".join(c), encoding="utf-8")

    print(f"assets: 背景{len(bg_data)//16}タイル / スプライト{len(spr_data)//16}タイル / 文字{len(gids)}種")


if __name__ == "__main__":
    main()
