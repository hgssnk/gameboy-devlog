# 第1章 掘る

// これは、歩く版の文を、選択肢で進む形に組み替えた下書き。文は歩く版のまま。
// 書式は README の「シナリオの書式」を見る。`//` で始まる行はコメント。

## room 部屋
bg: room_night
> 夜。
> 誰ともつながらない部屋で/ビートだけを作っている。
> この街に、仲間はいない。/まだ。
> 窓の外に、/中古屋の灯りが見えた。
> ……行ってみるか。
?
- 外に出る -> street

## street 夜の街
bg: street_night
> 夜の街。/どこへ行こう。
?
- 中古屋へ行く -> shop_front
- 自販機を調べる -> street_vending
- 掲示板を調べる -> street_board
- 高架下へ行く -> street_bridge

## street_vending
> つめたい、しか/残っていない。
-> street

## street_board
> 色あせたチラシ。/「公園で、音を鳴らそう」
> 日付は、/三年前だ。
-> street

## street_bridge
> 誰かの声が、/リズムに乗っている。
> 近づくと、/音はもう消えていた。
-> street

## shop_front 中古屋の前
bg: shop_front
> 古い看板。
> 「買取・販売/ハリオト商店」
> 閉店まで、/あと三十分。
?
- 中に入る -> shop_inside
- 街に戻る -> street

## shop_inside 店内
bg: shop_inside
?
- 店主に話す -> shop_owner
- ラジカセを調べる -> shop_radio
- 奥の箱を掘る -> shop_box
- 外に出る -> shop_notyet

## shop_owner
> 店主：……いらっしゃい。
> 店主：レコードなら、/奥の箱だ。
> 店主：全部百円。/当たりは、自分で探せ。
-> shop_inside

## shop_radio
> 値札に「ジャンク」。/……今日はやめておく。
-> shop_inside

## shop_box
// 場面5（ディグ）はまだ作っていない
> この先は、/まだ作っていない。
-> shop_inside

## shop_notyet
> ……まだ、何も/見つけていない。
-> shop_inside
