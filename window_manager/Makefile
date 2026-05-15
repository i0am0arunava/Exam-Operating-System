# wm - dynamic window manager
# See LICENSE file for copyright and license details.

include config.mk

SRC = drw.c wm.c util.c
OBJ = ${SRC:.c=.o}

all: wm

.c.o:
	${CC} -c ${CFLAGS} $<

${OBJ}: config.h config.mk

config.h:
	cp config.def.h $@

wm: ${OBJ}
	${CC} -o $@ ${OBJ} ${LDFLAGS}

clean:
	rm -f wm ${OBJ} wm-${VERSION}.tar.gz

dist: clean
	mkdir -p wm-${VERSION}
	cp -R LICENSE Makefile README config.def.h config.mk\
		wm.1 drw.h util.h ${SRC} wm.png transient.c wm-${VERSION}
	tar -cf wm-${VERSION}.tar wm-${VERSION}
	gzip wm-${VERSION}.tar
	rm -rf wm-${VERSION}

install: all
	mkdir -p ${DESTDIR}${PREFIX}/bin
	cp -f wm ${DESTDIR}${PREFIX}/bin
	chmod 755 ${DESTDIR}${PREFIX}/bin/wm
	mkdir -p ${DESTDIR}${MANPREFIX}/man1
	sed "s/VERSION/${VERSION}/g" < wm.1 > ${DESTDIR}${MANPREFIX}/man1/wm.1
	chmod 644 ${DESTDIR}${MANPREFIX}/man1/wm.1

uninstall:
	rm -f ${DESTDIR}${PREFIX}/bin/wm\
		${DESTDIR}${MANPREFIX}/man1/wm.1

.PHONY: all clean dist install uninstall
