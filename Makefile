GBDK_HOME ?= $(CURDIR)/gbdk/
LCC = $(GBDK_HOME)bin/lcc

PROJECT = hello
OUT = build/$(PROJECT).gb
EMULATOR = SameBoy

GEN = build/gen
GEN_SRCS = $(wildcard src/scenario/*.md) $(wildcard src/assets/bg/*.png) src/tools/gen_assets.py src/tools/font/misaki_gothic.bdf
SRCS = $(shell find src/game -name '*.c') $(GEN)/assets.c
HDRS = $(shell find src/game -name '*.h')

# make: ビルドして、エミュレータで起動する
all: build run

# make build: ビルドだけ
build: $(OUT)

# make run: 起動だけ
run: $(OUT)
	open -a $(EMULATOR) $(OUT)

# テキストと絵から、C のソースを作る
$(GEN)/assets.c $(GEN)/assets.h: $(GEN_SRCS)
	python3 src/tools/gen_assets.py

$(OUT): $(SRCS) $(HDRS) $(GEN)/assets.h
	mkdir -p build
	$(LCC) -Isrc/game -I$(GEN) -o $@ $(SRCS)

# make web: ブラウザで遊べる形(ページ + ROM)を build/web/ に作る。GitHub Pages に置くのはこれ
web: $(OUT)
	rm -rf build/web
	mkdir -p build/web
	cp src/web/* build/web/
	cp $(OUT) build/web/game.gb

# make serve: build/web/ を http://localhost:8000/ で開く(手元での確認用)
serve: web
	@echo "http://localhost:8000/ を開く。止めるときは Ctrl+C"
	cd build/web && python3 -m http.server 8000

clean:
	rm -rf build

.PHONY: all build run web serve clean
