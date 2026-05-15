# Top-level Makefile - build both components

all:
	$(MAKE) -C process_manager
	$(MAKE) -C desktop_env

clean:
	$(MAKE) -C process_manager clean
	$(MAKE) -C desktop_env clean

.PHONY: all clean
