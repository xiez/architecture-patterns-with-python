import shutil
import tempfile
from pathlib import Path

from .sync import determine_actions, sync, AbstractFileSystem


def test_when_a_file_exists_in_the_source_but_not_the_destination():
    src_hashes = {"hash1": "fn1"}
    dst_hashes = {}
    actions = determine_actions(src_hashes, dst_hashes, Path("/src"), Path("/dst"))

    expected_actions = [("copy", Path("/src/fn1"), Path("/dst/fn1"))]
    assert list(actions) == expected_actions


def test_when_a_file_has_been_renamed_in_the_source():
    src_hashes = {"hash1": "fn1"}
    dst_hashes = {"hash1": "fn2"}
    actions = determine_actions(src_hashes, dst_hashes, Path("/src"), Path("/dst"))

    expected_actions = [("move", Path("/dst/fn2"), Path("/dst/fn1"))]
    assert list(actions) == expected_actions


class FakeFileSystem(AbstractFileSystem, list):
    def copy(self, src, dest):
        self.append(("COPY", src, dest))

    def move(self, src, dest):
        self.append(("MOVE", src, dest))

    def delete(self, dest):
        self.append(("DELETE", dest))


def test_when_a_file_exists_in_the_source_but_not_the_destination2():
    source = {"sha1": "fn1"}
    dest = {}
    reader = {"/source_dir": source, "/dst_dir": dest}

    filesystem = FakeFileSystem()
    sync("/source_dir", "/dst_dir", reader.pop, filesystem)

    assert filesystem == [("COPY", Path("/source_dir/fn1"), Path("/dst_dir/fn1"))]


def test_when_a_file_has_been_renamed_in_the_source2():
    src_hashes = {"hash1": "fn1"}
    dst_hashes = {"hash1": "fn2"}
    reader = {"/source_dir": src_hashes, "/dst_dir": dst_hashes}

    filesystem = FakeFileSystem()
    sync("/source_dir", "/dst_dir", reader.pop, filesystem)
    assert filesystem == [("MOVE", Path("/dst_dir/fn2"), Path("/dst_dir/fn1"))]


def test_when_a_file_has_been_deleted_in_the_source():
    src_hashes = {}
    dst_hashes = {"hash1": "fn1"}
    reader = {"/source_dir": src_hashes, "/dst_dir": dst_hashes}

    filesystem = FakeFileSystem()
    sync("/source_dir", "/dst_dir", reader.pop, filesystem)
    assert filesystem == [
        ("DELETE", Path("/dst_dir/fn1")),
    ]


class TestE2E:
    @staticmethod
    def test_when_a_file_exists_in_the_source_but_not_the_destination():
        try:
            source = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()

            content = "I am a very useful file"
            (Path(source) / "my-file").write_text(content)

            sync(source, dest)

            expected_path = Path(dest) / "my-file"
            assert expected_path.exists()
            assert expected_path.read_text() == content

        finally:
            shutil.rmtree(source)
            shutil.rmtree(dest)

    @staticmethod
    def test_when_a_file_has_been_renamed_in_the_source():
        try:
            source = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()

            content = "I am a file that was renamed"
            source_path = Path(source) / "source-filename"
            old_dest_path = Path(dest) / "dest-filename"
            expected_dest_path = Path(dest) / "source-filename"
            source_path.write_text(content)
            old_dest_path.write_text(content)

            sync(source, dest)

            assert old_dest_path.exists() is False
            assert expected_dest_path.read_text() == content

        finally:
            shutil.rmtree(source)
            shutil.rmtree(dest)
