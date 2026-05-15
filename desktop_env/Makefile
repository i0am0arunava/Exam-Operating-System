# Makefile - Minimal Desktop Environment

CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -std=c99 \
          $(shell pkg-config --cflags x11 xft xinerama 2>/dev/null)
LDFLAGS = $(shell pkg-config --libs   x11 xft xinerama 2>/dev/null) \
          -lX11 -lXft -lXinerama -lfontconfig

TARGET  = desktop
SRC     = desktop.c

all: $(TARGET)

$(TARGET): $(SRC) desktop.h
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

clean:
	rm -f $(TARGET) *.o

install: $(TARGET)
	install -m 755 $(TARGET) /usr/local/bin/$(TARGET)
	@echo "Add 'exec desktop' to your ~/.xinitrc"

.PHONY: all clean install
