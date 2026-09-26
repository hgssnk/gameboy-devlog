#ifndef WALK_H
#define WALK_H

#include <gb/gb.h>

// マップは 10x9 マス（1マス = 16px = 8x8タイル 2x2）
#define MAP_W 10
#define MAP_H 9

enum { FACE_UP, FACE_DOWN, FACE_LEFT, FACE_RIGHT };

typedef struct {
    uint8_t x, y;
    uint8_t id;                         // 何に反応するか（maps.h の ID_*）
    uint8_t tile;                       // 描く絵（T_*）。0 なら描かない
} Obj;

typedef struct {
    const char *rows[MAP_H];            // # = 壁、. = 床
    const Obj *objs;                    // 向いてAで調べる（通れない）
    uint8_t n_objs;
    const Obj *steps;                   // 踏むと反応する床
    uint8_t n_steps;
    int8_t note_x, note_y;              // 声が聞こえる場所（♪が出る）。なしは -1
} Map;

void walk_enter(const Map *map, uint8_t x, uint8_t y, uint8_t face);   // マップを描いて、主人公を置く
void walk_place(uint8_t x, uint8_t y);                                 // 主人公を置き直す
void walk_hide(void);                                                  // 主人公と♪を隠す

// 歩かせる。Aで調べたか、反応する床を踏んだら、その ID を返す
uint8_t walk_run(void);

#endif
