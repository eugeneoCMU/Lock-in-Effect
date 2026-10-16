"""Bounded nested archive transport and real Release 47 consumer parity."""
import importlib
import io
from pathlib import Path
import struct
import zipfile

import pytest
import polars as pl
from polars.testing import assert_frame_equal
from test_freddie_release47 import files, modules


def archive(tmp_path, contents=None, quarter='2020Q1', outer_compression=zipfile.ZIP_STORED):
    if contents is None:
        o, p = files(tmp_path)
        contents = {f'orig_{quarter}.txt': o.read_bytes(), f'perf_{quarter}.txt': p.read_bytes()}
    nested = io.BytesIO()
    with zipfile.ZipFile(nested, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in contents.items():
            z.writestr(name, data)
    path = tmp_path / 'historical_data_2020.zip'
    with zipfile.ZipFile(path, 'w', compression=outer_compression) as z:
        z.writestr(f'historical_data_{quarter}.zip', nested.getvalue())
    return path


def transport():
    try:
        return importlib.import_module('freddie_archive_source')
    except ModuleNotFoundError:
        pytest.fail('Nested archive source transport is missing')


def test_archive_stream_reopens_and_closes_without_extracting(tmp_path):
    path = archive(tmp_path)
    before = sorted(tmp_path.iterdir())
    source = transport().ArchiveMember(path, '2020Q1', 'origination')
    expected = (tmp_path / 'release47-orig.txt').read_bytes()
    assert source.parent == tmp_path
    assert source.name == 'orig_2020Q1.txt'
    for _ in range(2):
        with source.open('rb') as stream:
            assert stream.read(7) + b''.join(stream) == expected
        assert stream.closed
    with pytest.raises(RuntimeError):
        with source.open('rb') as stream:
            raise RuntimeError('consumer failure')
    assert stream.closed
    assert sorted(tmp_path.iterdir()) == before
    info = source.metadata()
    assert info['annual_zip'] == str(path)
    assert info['quarter_member']['name'] == 'historical_data_2020Q1.zip'
    assert info['quarter_member']['compression'] == zipfile.ZIP_STORED
    assert info['text_member']['name'] == source.name
    assert info['text_member']['size'] == len(expected)
    assert info['text_member']['crc32'] == zipfile.crc32(expected)
    assert transport().as_source(source) is source
    assert transport().as_source(str(path)) == path


def test_nested_archive_schema_and_all_rebuild_artifacts_match_files(tmp_path):
    path = archive(tmp_path)
    cls = transport().ArchiveMember
    o, p = cls(path, '2020Q1', 'origination'), cls(path, '2020Q1', 'performance')
    _, audit, rebuild = modules()
    ro, rp = tmp_path / 'release47-orig.txt', tmp_path / 'release47-perf.txt'
    expected_audit, _ = audit.schema_audit(ro, rp, quarter='2020Q1', source_layout='release47')
    actual_audit, _ = audit.schema_audit(o, p, quarter='2020Q1', source_layout='release47')
    assert actual_audit == expected_audit
    expected = rebuild.build_quarter(ro, rp, tmp_path / 'files', '2020Q1', source_layout='release47')
    actual = rebuild.build_quarter(o, p, tmp_path / 'stream', '2020Q1', source_layout='release47')
    assert actual['source_sha256'] == expected['source_sha256']
    assert actual['counts'] == expected['counts']
    assert actual['schema'] == expected['schema']
    for name in expected['artifacts']:
        assert_frame_equal(pl.read_parquet(tmp_path / 'files' / name), pl.read_parquet(tmp_path / 'stream' / name))
    with pytest.raises(ValueError, match='32 fields'):
        rebuild.build_quarter(o, p, tmp_path / 'wrong-layout', '2020Q1')


@pytest.mark.parametrize('mode', ['r', 'w', 'wb', 'ab', 'r+b', None])
def test_archive_refuses_every_mode_except_binary_read(tmp_path, mode):
    source = transport().ArchiveMember(archive(tmp_path), '2020Q1', 'performance')
    with pytest.raises(ValueError):
        with source.open(mode):
            pass


@pytest.mark.parametrize('quarter,kind', [('2020Q0','origination'), ('../2020Q1','origination'), ('2020Q1','../perf'), ('2020Q1','perf')])
def test_archive_rejects_invalid_member_identifiers(tmp_path, quarter, kind):
    with pytest.raises(ValueError):
        transport().ArchiveMember(archive(tmp_path), quarter, kind)


def test_archive_requires_existing_file_exact_members_and_stored_outer_zip(tmp_path):
    cls = transport().ArchiveMember
    with pytest.raises(FileNotFoundError): cls(tmp_path / 'missing.zip', '2020Q1', 'origination')
    with pytest.raises((IsADirectoryError, ValueError)): cls(tmp_path, '2020Q1', 'origination')
    path = archive(tmp_path, {'../orig_2020Q1.txt': b'unsafe'})
    with pytest.raises(ValueError): cls(path, '2020Q1', 'origination')
    path = archive(tmp_path)
    with pytest.raises(ValueError): cls(path, '2020Q2', 'origination')
    path = archive(tmp_path, outer_compression=zipfile.ZIP_DEFLATED)
    with pytest.raises(ValueError, match='stored'): cls(path, '2020Q1', 'origination')


def test_archive_text_crc_failure_propagates_and_closes(tmp_path):
    # Stored inner payload makes a one-byte corruption deterministic, with valid directories.
    nested = io.BytesIO()
    with zipfile.ZipFile(nested, 'w') as z:
        z.writestr('orig_2020Q1.txt', b'UNIQUE_PAYLOAD\n')
    damaged = nested.getvalue().replace(b'UNIQUE_PAYLOAD', b'BROKEN_PAYLOAD', 1)
    path = tmp_path / 'bad.zip'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('historical_data_2020Q1.zip', damaged)
    source = transport().ArchiveMember(path, '2020Q1', 'origination')
    with pytest.raises(zipfile.BadZipFile, match='CRC'):
        with source.open('rb') as stream:
            stream.read(1024)
    assert stream.closed


def test_metadata_and_short_reads_seek_directly_over_large_stored_quarter(tmp_path, monkeypatch):
    # Replacing direct seek with ZipExtFile.seek would read the 4 MiB padding repeatedly.
    path = archive(tmp_path, {'padding.bin': b'x' * (4 * 1024**2), 'orig_2020Q1.txt': b'a|b\n'})
    # Use stored inner entries too, ensuring padding cannot compress away.
    nested = io.BytesIO()
    with zipfile.ZipFile(nested, 'w') as z:
        z.writestr('padding.bin', b'x' * (4 * 1024**2))
        z.writestr('orig_2020Q1.txt', b'a|b\n')
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('historical_data_2020Q1.zip', nested.getvalue())
    real_open = io.open
    reads, handles = [], []
    class CountReads:
        def __init__(self, file): self.file = file
        def read(self, size=-1):
            data = self.file.read(size)
            reads.append(len(data))
            return data
        def __getattr__(self, name): return getattr(self.file, name)
        def __enter__(self): return self
        def __exit__(self, *args): return self.file.__exit__(*args)
    def counted_open(file, *args, **kwargs):
        stream = real_open(file, *args, **kwargs)
        if Path(file) == path:
            handles.append(stream)
            return CountReads(stream)
        return stream
    monkeypatch.setattr(io, 'open', counted_open)
    source = transport().ArchiveMember(path, '2020Q1', 'origination')
    with source.open('rb') as stream:
        assert stream.read(2) == b'a|'
    assert sum(reads) < 100 * 1024
    assert handles and all(handle.closed for handle in handles)


def test_stored_view_bounds_seek_origins_and_closed_operations(tmp_path):
    path = tmp_path / 'range.bin'
    path.write_bytes(b'BEFOREpayloadAFTER')
    cls = transport()._StoredMemberView
    with path.open('rb') as file:
        with cls(file, 6, 7) as view:
            assert view.read(3) == b'pay'
            assert view.seek(-2, io.SEEK_CUR) == 1
            assert view.read(3) == b'ayl'
            assert view.seek(-2, io.SEEK_END) == 5
            assert view.read(100) == b'ad'
            assert view.read(1) == b''
            assert view.seek(100) == 100
            assert view.read(10) == b''
            with pytest.raises(ValueError): view.seek(-1)
            with pytest.raises(ValueError): view.seek(0, 99)
            view.seek(0)
            buffer = bytearray(20)
            assert view.readinto(buffer) == 7
            assert buffer[:7] == b'payload'
        with pytest.raises(ValueError): view.read(1)
        with pytest.raises(ValueError): view.seek(0)
        assert not file.closed
        with pytest.raises(zipfile.BadZipFile): cls(file, 6, 999)
        with pytest.raises(zipfile.BadZipFile): cls(file, -1, 7)


def test_duplicate_exact_quarter_and_text_members_are_rejected(tmp_path):
    cls = transport().ArchiveMember
    path = archive(tmp_path)
    with pytest.warns(UserWarning, match='Duplicate'):
        with zipfile.ZipFile(path, 'a') as z:
            z.writestr('historical_data_2020Q1.zip', b'ambiguous')
    with pytest.raises(ValueError, match='exactly one'):
        cls(path, '2020Q1', 'origination')
    nested = io.BytesIO()
    with pytest.warns(UserWarning, match='Duplicate'):
        with zipfile.ZipFile(nested, 'w') as z:
            z.writestr('orig_2020Q1.txt', b'first')
            z.writestr('orig_2020Q1.txt', b'second')
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('historical_data_2020Q1.zip', nested.getvalue())
    with pytest.raises(ValueError, match='exactly one'):
        cls(path, '2020Q1', 'origination')


def test_local_outer_compression_mismatch_is_rejected(tmp_path):
    path = archive(tmp_path)
    data = bytearray(path.read_bytes())
    struct.pack_into('<H', data, 8, zipfile.ZIP_DEFLATED)
    path.write_bytes(data)
    with pytest.raises(zipfile.BadZipFile, match='local header'):
        transport().ArchiveMember(path, '2020Q1', 'origination')
