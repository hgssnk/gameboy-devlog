#ifndef MAPS_H
#define MAPS_H

#include "common/walk.h"

// 調べるもの・踏む床の ID
enum {
    ID_NONE,
    ID_SHOPDOOR, ID_VENDING, ID_BOARD, ID_VIADUCT,      // 街
    ID_BOX, ID_RADIO, ID_OWNER, ID_EXIT,                // 中古屋
};

extern const Map map_street;            // 夜の街
extern const Map map_shop;              // 中古屋の中

#endif
