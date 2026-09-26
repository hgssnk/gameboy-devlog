#include "assets.h"
#include "maps.h"

// 夜の街。中古屋の入り口は左上、高架は右端、掲示板は真ん中
static const Obj street_objs[] = {
    { 1, 0, ID_SHOPDOOR, T_SHOPDOOR },
    { 7, 0, ID_VENDING, T_VENDING },
    { 5, 3, ID_BOARD, T_BOARD },
    { 9, 4, ID_VIADUCT, T_VIADUCT },
};

const Map map_street = {
    {
        "##########",
        "#........#",
        "#.##..##.#",
        "#........#",
        "#........#",
        "#.##..##.#",
        "#........#",
        "#........#",
        "##########",
    },
    street_objs, 4,
    0, 0,
    9, 4,                               // 高架下から声が聞こえる
};

// 中古屋の中。手前に店主、奥にレコードの箱
static const Obj shop_objs[] = {
    { 5, 0, ID_BOX, T_BOX },
    { 2, 0, ID_RADIO, T_RADIO },
    { 7, 6, ID_OWNER, T_OWNER },
};

static const Obj shop_steps[] = {
    { 4, 8, ID_EXIT, T_EXIT },
};

const Map map_shop = {
    {
        "##########",
        "#........#",
        "#........#",
        "#.####...#",
        "#........#",
        "#........#",
        "#........#",
        "#........#",
        "####.#####",
    },
    shop_objs, 3,
    shop_steps, 1,
    -1, -1,
};
