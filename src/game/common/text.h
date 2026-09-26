#ifndef TEXT_H
#define TEXT_H

#include "assets.h"

// 会話ウィンドウで、画面を順に表示する。Aで次へ。最後の画面でAを押すと閉じる。
// 使うときは SAY(txt_名前) と書く（text/*.txt の [名前]）
void say(const Screen *screens, uint8_t count);

#endif
