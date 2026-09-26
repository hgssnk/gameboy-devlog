#ifndef WINDOW_H
#define WINDOW_H

#include <gb/gb.h>

// 画面の下の枠（ウィンドウ）。上の帯、中身、下の線でできている。
void win_open(uint8_t rows);                                // 下から rows 行ぶんの枠を出す（中身は空）
void win_hide(void);
void win_glyph(uint8_t slot, uint8_t g, uint8_t invert);    // 文字 g を、slot 番目のタイルに入れる（invert：白抜き）

#endif
