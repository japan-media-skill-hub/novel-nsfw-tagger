from pathlib import Path
import re


def _t2s_convert(text):
    try:
        from lib.t2s import T2S
    except ImportError:
        return text
    return ''.join(T2S.get(ch, ch) for ch in text)


def detect_and_decode(filepath, trad_to_simp=True):
    p = Path(filepath)
    raw = p.read_bytes()
    candidates = ['utf-8-sig', 'utf-16le', 'utf-16be', 'utf-8', 'gb18030', 'gbk']
    for enc in candidates:
        try:
            text = raw.decode(enc)
            if len(text) > 100 and ('章' in text[:5000] or '第' in text[:5000]):
                return _normalize(text, trad_to_simp)
        except (UnicodeDecodeError, UnicodeError):
            continue
    for enc in candidates:
        try:
            text = raw.decode(enc, errors='replace')
            if len(text) > 100:
                return _normalize(text, trad_to_simp)
        except Exception:
            continue
    raise ValueError(f"Could not detect encoding for {filepath}")


def _normalize(text, trad_to_simp=True):
    if text.startswith('\ufeff'):
        text = text[1:]
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    if trad_to_simp:
        text = _t2s_convert(text)
    return text
