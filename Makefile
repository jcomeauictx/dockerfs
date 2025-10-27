# allow Bashisms
SHELL := /bin/bash
MOUNTPREFIX := $(HOME)/mnt/docker
PYTHON ?= $(word 1, $(shell which python3 python false))
PYLINT ?= $(word 1, $(shell which pylint3 pylint true))
BINDIR ?= $(HOME)/.local/bin
SERVICEDIR ?= $(HOME)/.config/systemd/user
OPT ?= -OO
ifeq ($(SHOWENV),)
else
export
endif
all: $(MOUNTPREFIX)-images/README umount
%/README: dockerfs.py %
	$(MAKE) $(<:.py=.pylint)
	$(PYTHON) $(OPT) $+
$(MOUNTPREFIX)-%:
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
	-fusermount -u $(MOUNTPREFIX)-images
	-fusermount -u $(MOUNTPREFIX)-containers
test:
	$(MAKE) OPT= MOUNTPREFIX=$(HOME)/tmp/mnt/docker
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
