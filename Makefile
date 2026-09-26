GBDK_HOME ?= $(CURDIR)/gbdk/
LCC = $(GBDK_HOME)bin/lcc

PROJECT = hello
OUT = build/$(PROJECT).gb
EMULATOR = SameBoy

GEN = build/gen
GEN_SRCS = $(wildcard src/scenario/*.txt) src/tools/gen_assets.py src/tools/font/misaki_gothic.bdf
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

clean:
	rm -rf build

.PHONY: all build run clean
