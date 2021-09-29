import abc
import hashlib
import os
import shutil
from pathlib import Path

BLOCKSIZE = 65536


def hash_file(path):
    hasher = hashlib.sha1()
    with path.open("rb") as file:
        buf = file.read(BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()


class AbstractFileSystem(abc.ABC):
    @abc.abstractmethod
    def copy(self, src, dest):
        ...

    @abc.abstractmethod
    def move(self, src, dest):
        ...

    @abc.abstractmethod
    def delete(self, dest):
        ...


class LocalFileSystem(AbstractFileSystem):
    def copy(self, src, dest):
        shutil.copyfile(src, dest)

    def move(self, src, dest):
        shutil.move(src, dest)

    def delete(self, dest):
        os.remove(dest)


def read_paths_and_hashes(root):
    hashes = {}
    for folder, _, files in os.walk(root):
        for fn in files:
            hashes[hash_file(Path(folder) / fn)] = fn
    return hashes


def sync(source, dest, reader=read_paths_and_hashes, filesystem=LocalFileSystem()):
    src_hashes = reader(source)
    dst_hashes = reader(dest)

    actions = determine_actions(src_hashes, dst_hashes, source, dest)

    for action, *paths in actions:
        if action == "copy":
            filesystem.copy(*paths)
        if action == "move":
            filesystem.move(*paths)
        if action == "delete":
            filesystem.delete(paths[0])


def determine_actions(src_hashes, dst_hashes, src_folder, dst_folder):
    for sha, filename in src_hashes.items():
        if sha not in dst_hashes:
            sourcepath = Path(src_folder) / filename
            destpath = Path(dst_folder) / filename
            yield "copy", sourcepath, destpath

        elif dst_hashes[sha] != filename:
            olddestpath = Path(dst_folder) / dst_hashes[sha]
            newdestpath = Path(dst_folder) / filename
            yield "move", olddestpath, newdestpath

    for sha, filename in dst_hashes.items():
        if sha not in src_hashes:
            yield "delete", Path(dst_folder) / filename
