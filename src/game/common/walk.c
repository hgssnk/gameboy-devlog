#include <gb/gb.h>
#include "assets.h"
#include "common/input.h"
#include "common/walk.h"

#define STEP 8                          // 1マス進むのにかかるフレーム（1フレーム 2px）
#define SPR_LEFT 0                      // スプライト番号：主人公の左半分、右半分、♪
#define SPR_RIGHT 1
#define SPR_NOTE 2

static const Map *map;
static uint8_t px, py, face;            // 主人公のマス、向き
static int8_t fx, fy;                   // 歩いている方向
static uint8_t t;                       // 歩き終わるまでの残りフレーム

static const int8_t dx[4] = { 0, 0, -1, 1 };
static const int8_t dy[4] = { -1, 1, 0, 0 };

static const Obj *find(const Obj *list, uint8_t n, uint8_t x, uint8_t y) {
    uint8_t i;
    for (i = 0; i < n; i++) {
        if (list[i].x == x && list[i].y == y) return &list[i];
    }
    return 0;
}

static uint8_t walkable(uint8_t x, uint8_t y) {
    if (x >= MAP_W || y >= MAP_H) return 0;
    if (map->rows[y][x] != '.') return 0;
    return !find(map->objs, map->n_objs, x, y);
}

// 16x16 の絵を、8x8 タイル4枚で描く
static void put_meta(uint8_t x, uint8_t y, uint8_t tile) {
    set_bkg_tile_xy(x * 2, y * 2, tile);
    set_bkg_tile_xy(x * 2 + 1, y * 2, tile + 1);
    set_bkg_tile_xy(x * 2, y * 2 + 1, tile + 2);
    set_bkg_tile_xy(x * 2 + 1, y * 2 + 1, tile + 3);
}

static void draw_map(void) {
    uint8_t x, y, i;
    for (y = 0; y < MAP_H; y++) {
        for (x = 0; x < MAP_W; x++) {
            if (map->rows[y][x] == '.') put_meta(x, y, T_FLOOR);
            else put_meta(x, y, ((x * 3 + y * 5) % 4 == 0) ? T_WALL2 : T_WALL);
        }
    }
    for (i = 0; i < map->n_steps; i++) {
        if (map->steps[i].tile) put_meta(map->steps[i].x, map->steps[i].y, map->steps[i].tile);
    }
    for (i = 0; i < map->n_objs; i++) {
        if (map->objs[i].tile) put_meta(map->objs[i].x, map->objs[i].y, map->objs[i].tile);
    }
}

static void draw_player(void) {
    uint8_t base = (face == FACE_UP) ? S_PLAYER_UP : (face == FACE_DOWN) ? S_PLAYER_DOWN : S_PLAYER_SIDE;
    uint8_t flip = (face == FACE_RIGHT);            // 右向きは、左向きを反転して使う
    uint8_t k = t ? (STEP - t) * 2 : 0;             // 歩いている途中の、進んだ px
    uint8_t sx = px * 16 + 8 + fx * k, sy = py * 16 + 16 + fy * k;   // スプライトの座標は、画面より(8,16)ずれる

    set_sprite_tile(SPR_LEFT, flip ? base + 2 : base);
    set_sprite_tile(SPR_RIGHT, flip ? base : base + 2);
    set_sprite_prop(SPR_LEFT, flip ? S_FLIPX : 0);
    set_sprite_prop(SPR_RIGHT, flip ? S_FLIPX : 0);
    move_sprite(SPR_LEFT, sx, sy);
    move_sprite(SPR_RIGHT, sx + 8, sy);
}

// 声が聞こえる場所の近くでは、♪を点滅させる
static void draw_note(void) {
    int8_t d, ex, ey;
    if (map->note_x < 0) return;
    ex = px - map->note_x;
    ey = py - map->note_y;
    d = (ex < 0 ? -ex : ex) + (ey < 0 ? -ey : ey);
    if (d <= 3 && (tick & 63) < 44) move_sprite(SPR_NOTE, map->note_x * 16 + 12, map->note_y * 16 + 8);
    else move_sprite(SPR_NOTE, 0, 0);
}

void walk_enter(const Map *m, uint8_t x, uint8_t y, uint8_t f) {
    map = m;
    px = x; py = y; face = f;
    fx = fy = 0; t = 0;
    draw_map();
    set_sprite_tile(SPR_NOTE, S_NOTE);
    set_sprite_prop(SPR_NOTE, S_PALETTE);           // 白抜き用のパレット
    draw_player();
    draw_note();
}

void walk_place(uint8_t x, uint8_t y) {
    px = x; py = y;
    fx = fy = 0; t = 0;
    draw_player();
}

void walk_hide(void) {
    move_sprite(SPR_LEFT, 0, 0);
    move_sprite(SPR_RIGHT, 0, 0);
    move_sprite(SPR_NOTE, 0, 0);
}

uint8_t walk_run(void) {
    const Obj *o;
    uint8_t d;

    for (;;) {
        frame();
        if (t) {
            t--;
            if (!t) {                                       // 1マス渡り終えた
                px += fx; py += fy; fx = fy = 0;
                o = find(map->steps, map->n_steps, px, py);
                if (o) { draw_player(); draw_note(); return o->id; }
            }
        } else {
            if (pressed(J_A)) {                             // 向いている先を調べる
                o = find(map->objs, map->n_objs, px + dx[face], py + dy[face]);
                if (o) return o->id;
            }
            d = held(J_UP) ? FACE_UP : held(J_DOWN) ? FACE_DOWN : held(J_LEFT) ? FACE_LEFT : held(J_RIGHT) ? FACE_RIGHT : 4;
            if (d < 4) {
                face = d;
                if (walkable(px + dx[d], py + dy[d])) { fx = dx[d]; fy = dy[d]; t = STEP; }
            }
        }
        draw_player();
        draw_note();
    }
}
