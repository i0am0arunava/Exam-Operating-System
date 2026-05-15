# Makefile - Process Manager

CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -std=c99
TARGET  = procman
SRC     = procman.c

all: $(TARGET)

$(TARGET): $(SRC) procman.h
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

clean:
	rm -f $(TARGET) *.o

install: $(TARGET)
	install -m 755 $(TARGET) /usr/local/bin/$(TARGET)

.PHONY: all clean install
