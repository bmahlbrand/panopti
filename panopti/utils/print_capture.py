import sys
import threading
import io

_orig_stdout = sys.stdout
_orig_stderr = sys.stderr

class _TeeTextIO:
    def __init__(self, *writers):
        self._writers = writers
        self._lock = threading.Lock()

    def write(self, data):
        with self._lock:
            for w in self._writers:
                try:
                    w.write(data)
                except Exception:
                    pass

    def flush(self):
        with self._lock:
            for w in self._writers:
                try:
                    w.flush()
                except Exception:
                    pass

_capture_buffer = None

def capture_prints(buffer=None, capture_stderr=False, callback=None):
    """Tee stdout (and optionally stderr) to a buffer and optional callback."""
    global _capture_buffer
    if buffer is None:
        _capture_buffer = io.StringIO()
    else:
        _capture_buffer = buffer

    def _cb_writer():
        class _CB:
            def write(self, d):
                callback(d)
            def flush(self):
                pass
        return _CB()

    writers = [_orig_stdout, _capture_buffer]
    if callback:
        writers.append(_cb_writer())

    sys.stdout = _TeeTextIO(*writers)
    if capture_stderr:
        err_writers = [_orig_stderr, _capture_buffer]
        if callback:
            err_writers.append(_cb_writer())
        sys.stderr = _TeeTextIO(*err_writers)

    return _capture_buffer