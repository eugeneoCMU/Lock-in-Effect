"""Read-only Freddie quarter members inside stored annual ZIP members.

Only central directories and bounded streaming reads are used; no source is
extracted, copied to disk, or loaded in full. Row-layout and identity checks
remain the responsibility of the existing consumers.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import io
import os
import struct
from pathlib import Path
import re
import zipfile


def _info(archive, name):
    matches = [item for item in archive.infolist() if item.filename == name]
    if len(matches) != 1 or matches[0].is_dir():
        raise ValueError('Expected exactly one archive member: ' + name)
    if matches[0].flag_bits & 1:
        raise ValueError('Encrypted source archive member is unsupported: ' + name)
    return matches[0]


def _member_metadata(info):
    return dict(name=info.filename, size=info.file_size,
                compressed_size=info.compress_size, crc32=info.CRC,
                compression=info.compress_type)


class _StoredMemberView(io.RawIOBase):
    """A bounded seekable view of an already validated stored ZIP payload.

    ZipExtFile.seek discards intervening bytes even for ZIP_STORED. This view
    instead seeks the annual file directly and never reads outside the member.
    The enclosing annual ZipFile owns the file handle.
    """
    def __init__(self, file, offset, size):
        super().__init__()
        self._file, self._start, self._size, self._position = file, offset, size, 0
        if offset < 0 or size < 0 or offset + size > os.fstat(file.fileno()).st_size:
            raise zipfile.BadZipFile('Stored member exceeds annual archive bounds')

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        self._checkClosed()
        return self._position

    def seek(self, offset, whence=io.SEEK_SET):
        self._checkClosed()
        if whence == io.SEEK_SET:
            position = offset
        elif whence == io.SEEK_CUR:
            position = self._position + offset
        elif whence == io.SEEK_END:
            position = self._size + offset
        else:
            raise ValueError('Invalid seek origin')
        if position < 0:
            raise ValueError('Negative seek position')
        self._position = position
        return position

    def read(self, size=-1):
        self._checkClosed()
        remaining = max(0, self._size - self._position)
        size = remaining if size is None or size < 0 else min(size, remaining)
        self._file.seek(self._start + self._position)
        data = self._file.read(size)
        self._position += len(data)
        return data

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)


@dataclass(frozen=True)
class ArchiveMember:
    annual_zip: Path
    quarter: str
    kind: str

    def __post_init__(self):
        object.__setattr__(self, 'annual_zip', Path(self.annual_zip))
        if not isinstance(self.quarter, str) or not re.fullmatch(r'20\d{2}Q[1-4]', self.quarter):
            raise ValueError('Expected source quarter YYYYQn')
        if self.kind not in ('origination', 'performance'):
            raise ValueError('Expected origination or performance source kind')
        # Validate existence, archive structure, exact member names, encryption,
        # and seekable stored transport before a consumer starts processing.
        self.metadata()

    @property
    def parent(self):
        return self.annual_zip.parent

    @property
    def name(self):
        return ('orig_' if self.kind == 'origination' else 'perf_') + self.quarter + '.txt'

    @property
    def quarter_member(self):
        return 'historical_data_' + self.quarter + '.zip'

    def __str__(self):
        return str(self.annual_zip) + '::' + self.quarter_member + '::' + self.name

    @contextmanager
    def _nested(self):
        with zipfile.ZipFile(self.annual_zip, 'r') as annual:
            quarter_info = _info(annual, self.quarter_member)
            if quarter_info.compress_type != zipfile.ZIP_STORED:
                raise ValueError('Quarter ZIP must be stored in the annual archive')
            # Let ZipFile validate the exact local filename, header and overlap
            # constraints without reading or seeking through the payload.
            with annual.open(quarter_info, 'r'):
                pass
            annual.fp.seek(quarter_info.header_offset)
            header = annual.fp.read(30)
            if len(header) != 30 or header[:4] != b'PK\x03\x04':
                raise zipfile.BadZipFile('Invalid stored quarter local header')
            fields = struct.unpack('<4s5H3I2H', header)
            if fields[2] & 1 or fields[3] != zipfile.ZIP_STORED:
                raise zipfile.BadZipFile('Stored quarter local header disagrees with directory')
            offset = quarter_info.header_offset + 30 + fields[-2] + fields[-1]
            if quarter_info.compress_size != quarter_info.file_size:
                raise zipfile.BadZipFile('Stored quarter compressed and uncompressed sizes disagree')
            with _StoredMemberView(annual.fp, offset, quarter_info.file_size) as quarter_stream:
                with zipfile.ZipFile(quarter_stream, 'r') as nested:
                    yield nested, quarter_info

    @contextmanager
    def open(self, mode='rb'):
        if mode != 'rb':
            raise ValueError('Archive sources support only rb mode')
        with self._nested() as (nested, _):
            with nested.open(_info(nested, self.name), 'r') as source:
                yield source

    def metadata(self):
        stat = self.annual_zip.stat()
        with self._nested() as (nested, quarter_info):
            text_info = _info(nested, self.name)
            return dict(annual_zip=str(self.annual_zip), quarter=self.quarter, kind=self.kind,
                annual_metadata=dict(path=str(self.annual_zip), size=stat.st_size,
                    allocated_bytes=stat.st_blocks * 512, flags=getattr(stat, 'st_flags', 0),
                    mtime_ns=stat.st_mtime_ns),
                quarter_member=_member_metadata(quarter_info), text_member=_member_metadata(text_info))


def as_source(value):
    """Keep explicitly supported archive sources; coerce filesystem inputs normally."""
    return value if isinstance(value, ArchiveMember) else Path(value)
