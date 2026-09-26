#ifndef VM_H
#define VM_H

#include "assets.h"

extern uint8_t flags[N_FLAGS];          // シナリオの set: で立てるフラグ

// 最初の場面から、章の終わり（sleep:）まで進める
void vm_run(void);

#endif
