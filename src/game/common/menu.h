#ifndef MENU_H
#define MENU_H

#include "assets.h"

// 選択肢を出して、選ばれた行き先の場面を返す（十字キーの上下で選び、Aで決める）
uint8_t menu_choose(const Menu *menu);

#endif
