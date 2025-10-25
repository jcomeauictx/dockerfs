# allow Bashisms
SHELL := /bin/bash
MOUNTPOINT := $(HOME)/mnt/docker
PYTHON ?= $(word 1, $(shell which python3 python false))
PYLINT ?= $(word 1, $(shell which pylint3 pylint true))
OPT ?= -OO
ifeq ($(SHOWENV),)
else
export
endif
all: $(MOUNTPOINT)-images/README umount
$(MOUNTPOINT)-images/README: dockerfs.py $(MOUNTPOINT)
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
	-fusermount -u $(MOUNTPOINT)-images
	-fusermount -u $(MOUNTPOINT)-containers
test:
	$(MAKE) OPT= MOUNTPOINT=$(HOME)/tmp/mnt/docker
install: dockerfs.py dockerfs.service
	if ! diff -q $< $(BINDIR); then \
	 cp --archive --interactive $< $(BINDIR)/; \
	fi
	if ! diff -q $(word 2, $+) $(SERVICEDIR)/; then \
	 cp --archive --interactive $(word 2, $+) $(SERVICEDIR)/; \
	 systemctl --user daemon-reload; \
	fi
start stop enable disable status:
	systemctl --user $@ dockerfs
log:
	journalctl --user -u dockerfs -f
debug info warning:
	sed -i 's/logging\.\(debug\|info\|warning\)/logging.$@/' dockerfs.py
diff: dockerfs.py dockerfs.service
	-diff $< $(BINDIR)/
	-diff $(word 2, $+) $(SERVICEDIR)/
.PHONY: install test umount env %.pylint start stop enable disable
