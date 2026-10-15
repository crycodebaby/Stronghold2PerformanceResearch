"""One local write lock for ingest.py (import, annotate, rebuild --write), D012. Library; stdlib only.

The lock is an operating-system byte-range lock on a small file (msvcrt on Windows, flock elsewhere). The OS drops it when
the holding process ends - normally, by kill or by crash - so a dead importer can never block the tools for good.
A waiting process polls until `timeout` seconds have passed and then raises Busy; it has changed nothing by then.
The file itself is left in place (it only carries the holder's pid for the message at byte 16 on, outside the locked byte).
"""
import contextlib
import os
import time

try:
    import msvcrt
except ImportError:          # not Windows
    msvcrt = None
    import fcntl


class Busy(Exception):
    """The lock is held by another live process."""

    def __init__(self, path, holder, waited):
        super().__init__(f"{path} is held by {holder}")
        self.path, self.holder, self.waited = path, holder, waited


def _try_lock(f):
    f.seek(0)
    if msvcrt:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(f):
    f.seek(0)
    if msvcrt:
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def _holder(path):
    try:
        with open(path, "rb") as f:
            f.seek(16)
            text = f.read(40).decode("ascii", "replace").strip("\0 \r\n")
            return text or "another process"
    except OSError:
        return "another process"


@contextlib.contextmanager
def exclusive(path, timeout=60.0, poll=0.05):
    """Hold the write lock `path` while the with-block runs. Raises Busy after `timeout` seconds."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    f = os.fdopen(os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0)), "r+b")   # not append mode: writes must land at offset 16
    start = time.monotonic()
    try:
        while True:
            try:
                _try_lock(f)
                break
            except OSError:
                waited = time.monotonic() - start
                if waited >= timeout:
                    raise Busy(str(path), _holder(path), waited)
                time.sleep(poll)
        f.seek(16)
        f.write(f"pid {os.getpid()}".encode("ascii").ljust(24))
        f.flush()
        try:
            yield
        finally:
            _unlock(f)
    finally:
        f.close()
