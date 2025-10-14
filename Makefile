# allow Bashisms
SHELL := /bin/bash
MOUNTPOINT := $(HOME)/mnt/docker-images
PYTHON ?= $(word 1, $(shell which python3 python false))
PYLINT ?= $(word 1, $(shell which pylint3 pylint true))
OPT ?= -OO
ifeq ($(SHOWENV),)
else
export
endif
$(MOUNTPOINT)/README: dockerfs.py $(MOUNTPOINT)
	$(MAKE) $(<:.py=.pylint)
	$(PYTHON) $(OPT) $+
$(MOUNTPOINT): | $(HOME)
	mkdir -p $@
%.pylint: %.py
	$(PYLINT) $<
env:
ifeq ($(SHOWENV),)
	$(MAKE) SHOWENV=1 $@
else
	$@
endif
umount:
	fusermount -u $(MOUNTPOINT)
test:
	$(MAKE) OPT=
