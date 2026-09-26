#ifndef INPUT_H
#define INPUT_H

#include <gb/gb.h>

extern uint8_t tick;                    // 経過フレーム（1フレームごとに増える）

void frame(void);                       // 1フレーム待って、キーの状態を更新する
uint8_t held(uint8_t key);              // 押している間ずっと true
uint8_t pressed(uint8_t key);           // 押した瞬間だけ true

#endif
