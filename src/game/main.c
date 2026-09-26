#include <gb/gb.h>
#include "assets.h"
#include "common/fade.h"
#include "chapters/ch1.h"

void main(void) {
    DISPLAY_OFF;
    fade_black();
    set_bkg_data(0, BG_TILE_COUNT, bg_tiles);
    set_sprite_data(0, SPR_TILE_COUNT, spr_tiles);
    SPRITES_8x16;
    SHOW_BKG;
    SHOW_SPRITES;
    DISPLAY_ON;

    ch1_run();
}
