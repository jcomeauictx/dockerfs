#!/usr/bin/python -OO
'''
implement simple docker filesystem
'''
import sys, os, stat, errno, logging, time  # pylint: disable=multiple-imports
import subprocess  # pylint: disable=multiple-imports
from datetime import datetime
# use posixpath to split, e.g., "wyaeld/sarge"
import posixpath as dockerpath
from collections import defaultdict
from copy import deepcopy
from fusepy import FUSE, FuseOSError, Operations

logging.basicConfig(level=logging.DEBUG if __debug__ else logging.INFO)

NOW = time.time()
MARKER = b'Presence of this virtual file means the DockerFS is mounted.\n'
README = {'inode': 1, 'size': len(MARKER), 'ctime': NOW, 'contents': MARKER}
IMAGES = {'README': README}
SUBDIRS = defaultdict(dict)
DIRECTORY = {
    'st_mode': (stat.S_IFDIR | 0o755),
    'st_nlink': 2,
    'st_size': 0,
    'st_ctime': NOW, 'st_mtime': NOW, 'st_atime': NOW,
    'st_uid': os.getuid(), 'st_gid': os.getgid()
}
FILE = {
    'st_mode': (stat.S_IFREG | 0o444),
    'st_nlink': 1,
    'st_size': 0,
    'st_ctime': NOW, 'st_mtime': NOW, 'st_atime': NOW,
    'st_uid': os.getuid(), 'st_gid': os.getgid()
}

class DockerFS(Operations):
    '''
    define the docker filesystem operations
    '''
    def getattr(self, path, fh=None):
        logging.debug('getattr(path=%s)', path)
        entry = None
        repo = path.lstrip(os.path.sep)
        subdir = None
        if dockerpath.sep in repo:
            subdir, repo = repo.split(dockerpath.sep)
        if repo == '':
            entry = deepcopy(DIRECTORY)
            entry['st_nlink'] += len(SUBDIRS)
        elif repo in IMAGES:
            image = IMAGES[repo]
            ctime = image['ctime']
            entry = {
                'st_mode': (stat.S_IFREG | 0o444),
                'st_nlink': 1,
                'st_size': image['size'],
                'st_ctime': ctime, 'st_mtime': ctime, 'st_atime': ctime,
                'st_uid': os.getuid(), 'st_gid': os.getgid()
            }
        elif subdir in SUBDIRS and repo in SUBDIRS[subdir]:
            image = SUBDIRS[subdir][repo]
            ctime = image['ctime']
            entry = {
                'st_mode': (stat.S_IFREG | 0o444),
                'st_nlink': 1,
                'st_size': image['size'],
                'st_ctime': ctime, 'st_mtime': ctime, 'st_atime': ctime,
                'st_uid': os.getuid(), 'st_gid': os.getgid()
            }
        elif subdir is None and repo in SUBDIRS:  # just the directory name
            entry = deepcopy(DIRECTORY)
        else:
            logging.error('%s not in %s', repo, list(IMAGES))
            raise FuseOSError(errno.ENOENT)
        return entry

    def readdir(self, path, fh):
        logging.debug('readdir (path=%s, fh=%s)', path, fh)
        cleanpath = path.lstrip(os.path.sep)
        update()
        if cleanpath == '':
            for child in ['.', '..', *SUBDIRS, *IMAGES]:
                logging.debug('yielding %s', child)
                yield child
        elif cleanpath in SUBDIRS:
            for child in ['.', '..', *SUBDIRS[cleanpath]]:
                logging.debug('yielding %s from %s', child, cleanpath)
                yield child
        else:
            raise FuseOSError(errno.ENOENT)

    def read(self, path, size, offset, fh):
        response = None
        repo = path.lstrip(os.path.sep)
        logging.debug('read (path=%s, size=%d, offset=%d, fh=%d',
                      path, size, offset, fh)
        if repo in IMAGES:
            contents = IMAGES[repo].get('contents')
            if contents is not None:
                response = contents[offset:offset + size]
            else:
                raise FuseOSError(errno.EAFNOSUPPORT)
        else:
            raise FuseOSError(errno.ENOENT)
        return response

def main(mountpoint=None):
    '''
    initialize and launch the filesystem
    '''
    # Create a mount point
    mountpoint = mountpoint or os.path.expanduser('~/mnt/docker-images')
    os.makedirs(mountpoint, exist_ok=True)

    # Create an instance of our filesystem
    filesystem = DockerFS()

    # Start the FUSE filesystem
    # foreground=True runs in the foreground for easier debugging.
    # auto_unmount=True allows automatic unmounting on exit.
    FUSE(
        filesystem,
        mountpoint,
        nothreads=True,
        foreground=__debug__,
        auto_unmount=__debug__
    )

def update():
    '''
    update global IMAGES with current list
    '''
    IMAGES.clear()
    IMAGES['README'] = README
    raw = subprocess.run([
        'docker', 'images', '--format',
        '{{.ID}}:{{.Repository}}:{{.Tag}}'
    ], capture_output=True, check=False).stdout.decode()
    logging.debug(raw)
    lines = raw.split('\n')
    logging.debug('lines: %s', lines)
    for line in filter(None, lines):
        dockerid, repo = line.split(':', 1)
        #repo = repo.replace(dockerpath.sep, '_')
        created, strsize = subprocess.run([
            'docker', 'inspect',
            '--format', '{{.Created}} {{.Size}}',
            dockerid
        ], capture_output=True, check=False).stdout.decode().split()
        created = datetime.fromisoformat(created).timestamp()
        inode = int(dockerid, 16)
        size = int(strsize)
        logging.debug('attributes: %s', (inode, repo, created, size))
        attributes = {'ctime': created, 'size': size, 'inode': inode}
        if dockerpath.sep in repo:
            subdir, repo = repo.split(dockerpath.sep)
            SUBDIRS[subdir][repo] = attributes
        else:
            IMAGES[repo] = attributes

if __name__ == "__main__":
    main(*sys.argv[1:])
