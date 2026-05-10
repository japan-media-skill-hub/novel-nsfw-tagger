import json, re
from pathlib import Path
from lib.chapter import Chapter


def load_lexicon(path):
    with open(path) as f:
        data = json.load(f)
    return data.get('L0', []), data.get('L1', []), data.get('L2', [])


def tag_chapter(ch, l0, l1, l2):
    if not ch.body_lines:
        return

    lines = ch.body_lines
    total = len(lines)
    hot_paragraphs = []

    for i, line in enumerate(lines):
        if _is_hot(line, l0, l1, l2):
            hot_paragraphs.append(i)

    if hot_paragraphs:
        first_hit = hot_paragraphs[0]
        last_hit = hot_paragraphs[-1]
        span = last_hit - first_hit + 1
        ratio = round(span / max(total, 1) * 100)
        ch.nsfw_start_line = first_hit
        ch.nsfw_end_line = last_hit
        ch.nsfw_start_global = ch.start_line + 1 + first_hit
        ch.nsfw_end_global = ch.start_line + 1 + last_hit
        ch.nsfw_ratio = ratio
        if ratio >= 5:
            ch.is_nsfw = True
            ch.annotated_title = _annotate_title(ch.original_title, ratio)


def _count_hits(line, keywords):
    return sum(1 for kw in keywords if kw in line)


def _is_hot(line, l0, l1, l2):
    hits_l0 = _count_hits(line, l0)
    hits_l1 = _count_hits(line, l1)
    hits_l2 = _count_hits(line, l2) if (hits_l0 > 0 or hits_l1 > 0) else 0
    if hits_l0 >= 1:
        return True
    if hits_l1 >= 3:
        return True
    if hits_l1 >= 2 and hits_l2 >= 2:
        return True
    if hits_l1 >= 1 and hits_l2 >= 4:
        return True
    return False


def _annotate_title(title, ratio):
    clean = title.rstrip()
    clean = re.sub(r'\(nsfw\s*\d+\)$', '', clean).rstrip()
    return f"{clean}(nsfw {ratio})"
