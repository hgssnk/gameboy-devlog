#!/usr/bin/env python3
"""シナリオと背景の絵から、ゲームボーイ用の C ソースを作る。

入力:
  src/scenario/*.md            シナリオ（書式は README の「シナリオの書式」）
  src/assets/bg/<名前>.png     背景の絵。160x112。4色（白・明るい灰・暗い灰・黒）
  src/tools/font/misaki_gothic.bdf  美咲フォント（8x8ドット。ライセンスは同じフォルダの misaki.txt）
出力:
  build/gen/assets.h, build/gen/assets.c

エラーは、John が直せる言葉で出す（どのファイルの何行目か、何が問題か）。
"""
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "build" / "gen"
FONT = ROOT / "src" / "tools" / "font" / "misaki_gothic.bdf"
SCENARIOS = sorted((ROOT / "src" / "scenario").glob("*.md"))
BG_DIR = ROOT / "src" / "assets" / "bg"

LINES, COLS = 2, 12         # 1ページ = 2行、1行12文字
PIC_W, PIC_H = 20, 14       # 背景の絵は 20x14 タイル（160x112）
MAX_OPTS = 4                # 選択肢は最大4つ
MAX_FLAGS = 32
MAX_SLOTS = 36              # 1画面で VRAM に載せる文字の数の上限
GLYPH_BASE = 256 - MAX_SLOTS    # 文字のタイル番号の始まり。絵のタイルは、この手前まで
UI = ["BLANK", "BLACK", "BOTLINE", "CURSOR", "ARROW"]   # 枠の記号（タイル 0〜4）
PIC_BASE = len(UI)
PIC_MAX = GLYPH_BASE - PIC_BASE     # 1枚の絵で使えるタイルの数

OPS = {"PAGE": 1, "SET": 2, "MENU": 3, "GOTO": 4, "SLEEP": 5}
SHADES = [255, 170, 85, 0]      # 色0〜3 の明るさ


def fail(msg):
    sys.exit(f"エラー: {msg}")


# ===== 枠の記号 =====
def tile_from_rows(rows):
    """8行×8桁の文字（'#'=黒）から、2bpp の16バイトを作る（色は 0 と 3 だけ）"""
    out = []
    for r in rows:
        b = sum(1 << (7 - i) for i, ch in enumerate(r) if ch == "#")
        out += [b, b]
    return out


def ui_tiles():
    return {
        "BLANK": tile_from_rows(["........"] * 8),
        "BLACK": tile_from_rows(["########"] * 8),
        "BOTLINE": tile_from_rows(["########", "########"] + ["........"] * 6),
        "CURSOR": tile_from_rows(["........", "#######.", "#######.", ".#####..", ".#####..", "..###...", "..###...", "...#...."]),
        "ARROW": tile_from_rows(["#.......", "##......", "###.....", "####....", "###.....", "##......", "#.......", "........"]),
    }


# ===== PNG（4色の背景） =====
def read_png(path):
    """PNG を読んで、8x8 の 0〜3 の色番号の並び（行のリスト）にする。色の番号は、明るさで決める"""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"{path.name} は PNG ではありません")
    pos, idat, plte, hdr = 8, b"", None, None
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if kind == b"IHDR":
            hdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            plte = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif kind == b"IDAT":
            idat += body
    w, h, bd, ct, _, _, il = hdr
    if il:
        fail(f"{path.name}: インターレース PNG には対応していません")
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ct)
    if ch is None or (ct != 3 and bd != 8 and ct != 0):
        fail(f"{path.name}: この形式の PNG には対応していません（インデックスカラーか、8ビットの画像にしてください）")
    stride = (w * ch * bd + 7) // 8
    bpp = max(1, ch * bd // 8)
    raw = zlib.decompress(idat)
    rows, prev = [], bytearray(stride)
    for y in range(h):
        f = raw[y * (stride + 1)]
        cur = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = cur[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                cur[i] = (cur[i] + a) & 255
            elif f == 2:
                cur[i] = (cur[i] + b) & 255
            elif f == 3:
                cur[i] = (cur[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                cur[i] = (cur[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(cur)
        prev = cur

    def shade(lum):
        return min(range(4), key=lambda k: abs(SHADES[k] - lum))

    px = []
    for cur in rows:
        line = []
        for x in range(w):
            if ct == 3:
                if bd == 8:
                    idx = cur[x]
                else:
                    idx = (cur[x * bd // 8] >> (8 - bd - (x * bd) % 8)) & ((1 << bd) - 1)
                r, g, b = plte[idx]
                lum = (r * 299 + g * 587 + b * 114) // 1000
            elif ct == 0:
                v = (cur[x * bd // 8] >> (8 - bd - (x * bd) % 8)) & ((1 << bd) - 1)
                lum = v * 255 // ((1 << bd) - 1)
            else:
                o = x * ch
                lum = (cur[o] * 299 + cur[o + 1] * 587 + cur[o + 2] * 114) // 1000 if ct in (2, 6) else cur[o]
            line.append(shade(lum))
        px.append(line)
    if (w, h) != (PIC_W * 8, PIC_H * 8):
        fail(f"{path.name}: 大きさが {w}x{h} です。{PIC_W * 8}x{PIC_H * 8} にしてください")
    return px


def tile_bytes(px, tx, ty):
    out = []
    for row in px[ty * 8:ty * 8 + 8]:
        lo = hi = 0
        for c in row[tx * 8:tx * 8 + 8]:
            lo = (lo << 1) | (c & 1)
            hi = (hi << 1) | ((c >> 1) & 1)
        out += [lo, hi]
    return tuple(out)


def convert_bg(name):
    """背景1枚を、重ならないタイルの表と、20x14 の並びにする"""
    path = BG_DIR / f"{name}.png"
    if path.exists():
        px = read_png(path)
    else:
        print(f"背景 {name}.png がまだありません。仮の灰色を使います")
        px = [[2 if (x + y) % 2 else 3 for x in range(PIC_W * 8)] for y in range(PIC_H * 8)]
    tiles, index, tmap = [], {}, []
    for ty in range(PIC_H):
        for tx in range(PIC_W):
            t = tile_bytes(px, tx, ty)
            if t not in index:
                index[t] = len(tiles)
                tiles.append(t)
            tmap.append(PIC_BASE + index[t])
    if len(tiles) > PIC_MAX:
        fail(f"背景 {name}.png のタイルが {len(tiles)} 枚あります。{PIC_MAX} 枚までです"
             "（同じ模様の8x8は1枚と数えます。細かい模様を減らしてください）")
    return tiles, tmap


# ===== フォント（BDF） =====
def load_bdf(path):
    """{ 文字コード: 8行分のバイト }"""
    glyphs, cur, fb_h, fb_yo = {}, None, 0, 0
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


# ===== シナリオ =====
class Scene:
    def __init__(self, sid, title, file, line):
        self.id, self.title, self.file, self.line = sid, title, file, line
        self.bg = None
        self.cmds = []          # ("page", who, rows) ("set", flag) ("goto", id, line) ("menu", [opt]) ("sleep",)
        self.n_pages = 0


def parse_scenarios():
    scenes, chapter_title = [], ""
    for path in SCENARIOS:
        cur, menu = None, None
        for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            where = f"{path.name}の{n}行目"
            line = raw.strip()
            if not line or line.startswith("//"):
                continue
            if line.startswith("## "):
                m = re.fullmatch(r"## (\w+)(?:\s+(.*))?", line)
                if not m:
                    fail(f"{where}: 場面の書き方が違います。「## id 見出し」の形にしてください（id は英数字）: {raw}")
                if any(s.id == m.group(1) for s in scenes):
                    fail(f"{where}: 場面 {m.group(1)} が2回出てきます")
                cur = Scene(m.group(1), m.group(2) or "", path.name, n)
                scenes.append(cur)
                menu = None
                continue
            if line.startswith("# "):
                if not chapter_title:
                    chapter_title = line[2:].strip()
                continue
            if cur is None:
                fail(f"{where}: 最初に「## id 見出し」で場面を始めてください")
            if menu is not None and not line.startswith("- "):
                fail(f"{where}: 選択肢（?）のあとには、「- 文 -> 行き先」しか書けません: {raw}")
            if cur.cmds and cur.cmds[-1][0] in ("menu", "goto", "sleep") and menu is None:
                fail(f"{where}: 場面 {cur.id} は、すでに終わっています（選択肢、-> 、sleep: のあとには書けません）")
            if line.startswith("bg:"):
                cur.bg = line[3:].strip()
            elif line.startswith(">"):
                text = line[1:].strip()
                who, i = "", text.find("：")
                if 0 < i <= 3:
                    who, text = text[:i], text[i + 1:]
                rows = text.split("/")
                cur.n_pages += 1
                if len(rows) > LINES:
                    fail(f"{cur.id} の{cur.n_pages}ページ目({where})が{len(rows)}行あります。{LINES}行までです")
                for r, row in enumerate(rows, 1):
                    if len(row) > COLS:
                        fail(f"{cur.id} の{cur.n_pages}ページ目、{r}行目({where})が{len(row)}文字あります。{COLS}文字までです")
                cur.cmds.append(("page", who, rows))
            elif line.startswith("set:"):
                cur.cmds.append(("set", line[4:].strip()))
            elif line == "?":
                menu = []
                cur.cmds.append(("menu", menu, n))
            elif line.startswith("- ") and menu is not None:
                m = re.fullmatch(r"- (.+?)\s*->\s*(\w+)(?:\s*\[(if|unless)\s+(\w+)\])?", line)
                if not m:
                    fail(f"{where}: 選択肢の書き方が違います。「- 文 -> 行き先」の形にしてください: {raw}")
                if len(m.group(1)) > COLS - 1:
                    fail(f"{cur.id} の選択肢「{m.group(1)}」({where})が{len(m.group(1))}文字あります。{COLS - 1}文字までです")
                menu.append((m.group(1), m.group(2), m.group(3), m.group(4), n))
                if len(menu) > MAX_OPTS:
                    fail(f"{cur.id} の選択肢({where})が{MAX_OPTS}つを超えています")
            elif line.startswith("->"):
                cur.cmds.append(("goto", line[2:].strip(), n))
            elif line.startswith("sleep:"):
                cur.cmds.append(("sleep",))
            elif re.match(r"(random|se|call):", line):
                fail(f"{where}: {line.split(':')[0]}: は、まだ使えません")
            else:
                fail(f"{where}: 読めない行です: {raw}")
    ids = {s.id: i for i, s in enumerate(scenes)}
    for s in scenes:
        if not s.cmds or s.cmds[-1][0] not in ("menu", "goto", "sleep"):
            fail(f"{s.file}の{s.line}行目: 場面 {s.id} の最後に、選択肢（?）か、-> 行き先か、sleep: が必要です")
        if s.cmds[-1][0] == "menu" and not s.cmds[-1][1]:
            fail(f"{s.file}の{s.cmds[-1][2]}行目: 場面 {s.id} の「?」のあとに、選択肢がありません")
        for c in s.cmds:
            targets = [(c[1], c[2])] if c[0] == "goto" else [(o[1], o[4]) for o in c[1]] if c[0] == "menu" else []
            for t, ln in targets:
                if t not in ids:
                    fail(f"{s.file}の{ln}行目: 場面 {s.id} の行き先 {t} という場面がありません")
    if not scenes:
        fail("src/scenario/ に、場面がありません")
    return scenes, ids, chapter_title


def main():
    font = load_bdf(FONT)
    scenes, ids, chapter_title = parse_scenarios()

    gids = {}
    def gid(ch):
        if ord(ch) not in font:
            fail(f"美咲フォントに「{ch}」(U+{ord(ch):04X}) がありません。別の字に置き換えてください")
        return gids.setdefault(ch, len(gids))

    flags = {}
    def flag(name):
        if name not in flags:
            if len(flags) >= MAX_FLAGS:
                fail(f"フラグが{MAX_FLAGS}個を超えました")
            flags[name] = len(flags)
        return flags[name]

    def make_page(who, rows):
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
            fail(f"1ページの文字の種類が多すぎます: {rows}")
        glyph += [0] * (MAX_SLOTS - len(glyph))
        return "    { %d, %d, { %s }, { %s }, { { %s }, { %s } } }," % (
            len(slots_body), len(slots_who), ", ".join(map(str, glyph)), ", ".join(map(str, who_cells)),
            ", ".join(map(str, cells[0])), ", ".join(map(str, cells[1])))

    pages, menus, codes, bg_names = [], [], [], []
    for s in scenes:
        code = []
        for c in s.cmds:
            if c[0] == "page":
                if len(pages) >= 255:
                    fail("ページが多すぎます（255ページまで）")
                pages.append(make_page(c[1], c[2]))
                code += [OPS["PAGE"], len(pages) - 1]
            elif c[0] == "set":
                code += [OPS["SET"], flag(c[1])]
            elif c[0] == "goto":
                code += [OPS["GOTO"], ids[c[1]]]
            elif c[0] == "sleep":
                code += [OPS["SLEEP"]]
            else:
                opts, slots = [], []
                for label, target, cond, fname, _ in c[1]:
                    cells = [0xFF] * COLS
                    for i, ch in enumerate(label):
                        g = gid(ch)
                        if g not in slots:
                            slots.append(g)
                        cells[i] = slots.index(g)
                    opts.append((cells, ids[target], flag(fname) if fname else 0, {None: 0, "if": 1, "unless": 2}[cond]))
                if len(slots) > MAX_SLOTS:
                    fail(f"{s.id} の選択肢の文字の種類が多すぎます")
                glyph = slots + [0] * (MAX_SLOTS - len(slots))
                body = ["    { %d, { %s }, %d, {" % (len(slots), ", ".join(map(str, glyph)), len(opts))]
                for cells, target, fl, cond in opts:
                    body.append("        { { %s }, %d, %d, %d }," % (", ".join(map(str, cells)), target, fl, cond))
                body.append("    } },")
                menus.append("\n".join(body))
                code += [OPS["MENU"], len(menus) - 1]
        codes.append(code)
        if s.bg and s.bg not in bg_names:
            bg_names.append(s.bg)

    end_page = len(pages)
    pages.append(make_page("", [chapter_title[:COLS], "おわり"]))
    if len(gids) > 256:
        fail("文字の種類が256を超えました")

    bgs = {name: convert_bg(name) for name in bg_names}

    # ---- assets.h ----
    OUT.mkdir(parents=True, exist_ok=True)
    h = ["/* 自動生成：tools/gen_assets.py。手で書き換えない */", "#ifndef ASSETS_H", "#define ASSETS_H", "#include <stdint.h>", ""]
    for i, name in enumerate(UI):
        h.append(f"#define T_{name} {i}")
    h += [f"#define N_UI_TILES {len(UI)}", f"#define T_PIC_BASE {PIC_BASE}", f"#define GLYPH_BASE {GLYPH_BASE}", f"#define MAX_SLOTS {MAX_SLOTS}",
          f"#define PIC_W {PIC_W}", f"#define PIC_H {PIC_H}", f"#define COLS {COLS}", f"#define MAX_OPTS {MAX_OPTS}",
          f"#define N_FLAGS {max(len(flags), 1)}", f"#define PAGE_END {end_page}", ""]
    for k, v in OPS.items():
        h.append(f"#define OP_{k} {v}")
    h += ["", "typedef struct {",
          "    uint8_t n_body, n_who;             /* 本文、話す人の、文字の種類 */",
          "    uint8_t glyph[MAX_SLOTS];          /* 本文、話す人の順に、フォント内の番号 */",
          "    uint8_t who[3];                    /* 話す人の各文字の、glyph の番号（なしは 0xFF） */",
          f"    uint8_t cell[{LINES}][COLS];               /* 本文の各マスの、glyph の番号（空白は 0xFF） */",
          "} Page;", "",
          "typedef struct {",
          "    uint8_t cell[COLS];                /* ラベルの各マスの、glyph の番号（空白は 0xFF） */",
          "    uint8_t target;                    /* 行き先の場面 */",
          "    uint8_t flag, cond;                /* cond: 0=いつも出す 1=flag が立っているとき 2=立っていないとき */",
          "} Opt;", "",
          "typedef struct {",
          "    uint8_t n_slots;",
          "    uint8_t glyph[MAX_SLOTS];",
          "    uint8_t n;",
          "    Opt opt[MAX_OPTS];",
          "} Menu;", "",
          "typedef struct { uint8_t n_tiles; const uint8_t *tiles; const uint8_t *map; } Bg;",
          "typedef struct { uint8_t bg; const uint8_t *code; } Scene;   /* bg: 0xFF なら、前の背景のまま */", "",
          "extern const uint8_t font_tiles[];   /* 1文字 = 16バイト */",
          "extern const uint8_t ui_tiles[];",
          "extern const Page pages[];", "extern const Menu menus[];", "extern const Bg bgs[];", "extern const Scene scenes[];",
          "", "#endif", ""]
    (OUT / "assets.h").write_text("\n".join(h), encoding="utf-8")

    # ---- assets.c ----
    def cb(data, per=16):
        return "\n".join("    " + ", ".join(f"0x{b:02X}" for b in data[i:i + per]) + "," for i in range(0, len(data), per))

    c = ["/* 自動生成：tools/gen_assets.py。手で書き換えない */", '#include "assets.h"', ""]
    ut = ui_tiles()
    c.append("const uint8_t ui_tiles[] = {\n" + cb([b for n in UI for b in ut[n]]) + "\n};\n")
    c.append(f"/* {len(gids)} 文字：{''.join(gids)} */")
    c.append("const uint8_t font_tiles[] = {\n" + cb([b for ch in gids for i, r in enumerate(font[ord(ch)]) for b in (r, r)]) + "\n};\n")
    c.append("const Page pages[] = {\n" + "\n".join(pages) + "\n};\n")
    c.append("const Menu menus[] = {\n" + "\n".join(menus or ["    { 0, { 0 }, 0, { { { 0 }, 0, 0, 0 } } },"]) + "\n};\n")
    for name, (tiles, tmap) in bgs.items():
        c.append(f"static const uint8_t bg_{name}_tiles[] = {{\n" + cb([b for t in tiles for b in t]) + "\n};")
        c.append(f"static const uint8_t bg_{name}_map[] = {{\n" + cb(tmap, 20) + "\n};\n")
    c.append("const Bg bgs[] = {")
    for name, (tiles, _) in bgs.items():
        c.append(f"    {{ {len(tiles)}, bg_{name}_tiles, bg_{name}_map }},   /* {name} */")
    c.append("};\n")
    for s, code in zip(scenes, codes):
        c.append(f"static const uint8_t code_{s.id}[] = {{ {', '.join(map(str, code))} }};")
    c.append("")
    c.append("const Scene scenes[] = {")
    bg_index = {n: i for i, n in enumerate(bgs)}
    for s in scenes:
        c.append(f"    {{ {bg_index[s.bg] if s.bg else 255}, code_{s.id} }},   /* {s.id} {s.title} */")
    c.append("};\n")
    (OUT / "assets.c").write_text("\n".join(c), encoding="utf-8")

    print(f"assets: 場面{len(scenes)} / ページ{len(pages) - 1} / 選択肢の画面{len(menus)} / 背景{len(bgs)}枚 / 文字{len(gids)}種"
          + "".join(f" / {n}:タイル{len(t)}枚" for n, (t, _) in bgs.items()))


if __name__ == "__main__":
    main()
