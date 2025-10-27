# dockerfs

In Unix, "everything is a file"[^1], except when it isn't, such as with
Docker images&mdash;and this makes for tricky Makefile hacks.

`dockerfs` is a simple FUSE filesystem to make docker images accessible as
files, at least, enough to establish that they are present in `docker images`.

as of 2025-10-27, also supports containers under ~/mnt/docker-containers/.

[^1]: [Everything is a file](https://en.wikipedia.org/wiki/Everything_is_a_file)

## developer's notes

you must escape the colon in the target in a Makefile, e.g.:
```
IMAGE := alpine-ish-dev
TAG := $(IMAGE)\:latest
MOUNTPOINT := $(HOME)/mnt/docker-images
$(MOUNTPOINT)/$(TAG): Dockerfile | $(MOUNTPOINT)/README
    -docker stop $(IMAGE)
    -docker rm $(IMAGE)
    -docker rmi $(TAG)
# you also must build with --no-cache so Make knows when to rebuild
    docker build \
     --no-cache \
     --tag $(TAG) \
     .
$(MOUNTPOINT)/README: dockerfs.py $(MOUNTPOINT)
    $(PYTHON) $+
$(MOUNTPOINT): | $(HOME)
    mkdir -p $@
```
if you copy-and-paste the Makefile snippet, be sure to change the 4-space
indents to actual tabs. (don't do this; use the repo's Makefile instead and
edit as needed).

## bugs

* broken under SELinux
* doesn't umount on `make stop`; need to `make umount` after complete, and it
takes over a minute.
