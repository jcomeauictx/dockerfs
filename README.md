# dockerfs

In Unix, "everything is a file"[^1], except when it isn't, such as with
Docker images&mdash;and this makes for tricky Makefile hacks.

`dockerfs` is a simple FUSE filesystem to make docker images accessible as
files, at least, enough to establish that they are present in `docker images`.

[1]: [Everything is a file](https://en.wikipedia.org/wiki/Everything_is_a_file)
