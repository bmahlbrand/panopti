import sys
import threading
import io
import re
from typing import List, Dict

_orig_stdout = sys.stdout
_orig_stderr = sys.stderr

ANSI_COLOR_MAP = {
    '\033[37m': 'white',
    '\033[31m': 'red',
    '\033[32m': 'green',
    '\033[33m': 'yellow',
    '\033[34m': 'blue',
    '\033[35m': 'magenta',
    '\033[36m': 'cyan',
    '\033[30m': 'black',
    '\033[97m': 'bright-white',
    '\033[91m': 'bright-red',
    '\033[92m': 'bright-green',
    '\033[93m': 'bright-yellow',
    '\033[94m': 'bright-blue',
    '\033[95m': 'bright-magenta',
    '\033[96m': 'bright-cyan',
    '\033[90m': 'bright-black',
}

ANSI_RESET = '\033[0m'
COLOR_MARKER_REGEX = re.compile(r'\[COLOR:([^\]]+)\](.*?)\[/COLOR\]', re.DOTALL)

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
        def _split_ansi(text: str) -> List[Dict[str, str]]:
            """Split text into segments based on ANSI color codes."""
            segments = []
            current_text = ''
            current_color = None
            i = 0
            while i < len(text):
                matched = False
                for code, color_name in ANSI_COLOR_MAP.items():
                    if text.startswith(code, i):
                        # Flush existing buffer
                        if current_text:
                            segments.append({'text': current_text, 'color': current_color})
                            current_text = ''
                        current_color = color_name
                        i += len(code)
                        matched = True
                        break
                if matched:
                    continue
                if text.startswith(ANSI_RESET, i):
                    # Flush buffer and reset color
                    if current_text:
                        segments.append({'text': current_text, 'color': current_color})
                        current_text = ''
                    current_color = None
                    i += len(ANSI_RESET)
                    continue
                # Regular character
                current_text += text[i]
                i += 1
            if current_text:
                segments.append({'text': current_text, 'color': current_color})
            return segments

        class _CB:
            def __init__(self):
                self._buffer = ""
            
            def write(self, d):
                self._buffer += d
                
                while '\n' in self._buffer:
                    line, remainder = self._buffer.split('\n', 1)
                    self._buffer = remainder
                    
                    # Process the complete line
                    segments: List[Dict[str, str]] = []

                    pos = 0
                    for match in COLOR_MARKER_REGEX.finditer(line):
                        if match.start() > pos:
                            plain = line[pos:match.start()]
                            segments.extend(_split_ansi(plain))
                        color_name = match.group(1).lower()
                        inner_text = match.group(2)
                        segments.append({'text': inner_text, 'color': color_name})
                        pos = match.end()
                    if pos < len(line):
                        segments.extend(_split_ansi(line[pos:]))

                    if not segments:
                        segments = [{'text': line, 'color': None}]

                    callback(segments)
            
            def flush(self):
                # Send any remaining buffered content without newline
                if self._buffer:
                    segments: List[Dict[str, str]] = []

                    pos = 0
                    for match in COLOR_MARKER_REGEX.finditer(self._buffer):
                        # Text before marker
                        if match.start() > pos:
                            plain = self._buffer[pos:match.start()]
                            segments.extend(_split_ansi(plain))
                        color_name = match.group(1).lower()
                        inner_text = match.group(2)
                        segments.append({'text': inner_text, 'color': color_name})
                        pos = match.end()
                    # Remainder after last marker
                    if pos < len(self._buffer):
                        segments.extend(_split_ansi(self._buffer[pos:]))

                    # If no markers or ANSI codes detected, fallback to plain text
                    if not segments:
                        segments = [{'text': self._buffer, 'color': None}]

                    callback(segments)
                    self._buffer = ""
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

def split_text_to_segments(text):
    """Split a text buffer into segments as the callback would."""
    def _split_ansi(text: str) -> List[Dict[str, str]]:
        segments = []
        current_text = ''
        current_color = None
        i = 0
        while i < len(text):
            matched = False
            for code, color_name in ANSI_COLOR_MAP.items():
                if text.startswith(code, i):
                    if current_text:
                        segments.append({'text': current_text, 'color': current_color})
                        current_text = ''
                    current_color = color_name
                    i += len(code)
                    matched = True
                    break
            if matched:
                continue
            if text.startswith(ANSI_RESET, i):
                if current_text:
                    segments.append({'text': current_text, 'color': current_color})
                    current_text = ''
                current_color = None
                i += len(ANSI_RESET)
                continue
            current_text += text[i]
            i += 1
        if current_text:
            segments.append({'text': current_text, 'color': current_color})
        return segments
    
    lines = text.split('\n')
    all_segments = []
    
    for line in lines:
        segments = []
        pos = 0
        for match in COLOR_MARKER_REGEX.finditer(line):
            if match.start() > pos:
                plain = line[pos:match.start()]
                segments.extend(_split_ansi(plain))
            color_name = match.group(1).lower()
            inner_text = match.group(2)
            segments.append({'text': inner_text, 'color': color_name})
            pos = match.end()
        if pos < len(line):
            segments.extend(_split_ansi(line[pos:]))
        if not segments:
            segments = [{'text': line, 'color': None}]
        
        # Add newline to the last segment of each line (except the last line if it doesn't end with newline)
        if segments and (line != lines[-1] or text.endswith('\n')):
            if segments:
                segments[-1]['text'] += '\n'
        
        all_segments.extend(segments)
    
    return all_segments