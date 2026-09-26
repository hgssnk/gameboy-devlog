#ifndef TEXT_H
#define TEXT_H

#include "assets.h"

// 文を1ページ出す。1文字ずつ出て、Aで早送り。ページの終わりでAを押すと戻る
void say_page(const Page *page);

#endif
