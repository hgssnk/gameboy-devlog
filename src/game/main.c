#include <gb/gb.h>
#include "assets.h"
#include "common/fade.h"
#include "vm.h"

void main(void) {
    DISPLAY_OFF;
    fade_black();
    set_bkg_data(0, N_UI_TILES, ui_tiles);
    SHOW_BKG;
    DISPLAY_ON;

    for (;;) vm_run();
}
