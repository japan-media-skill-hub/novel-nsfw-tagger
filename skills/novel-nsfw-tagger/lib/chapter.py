import re

CHAPTER_PATTERN = re.compile(
    r'^[\t \u3000]*('
    r'(第?[\t \u3000]*[\d零一二三四五六七八九十百千万兩〇]+[\t \u3000]*[章回节卷篇部集])'
    r'|([章节卷篇部集][\t \u3000]*[\d零一二三四五六七八九十百千万兩〇]+)'
    r'|([\d零一二三四五六七八九十百千万兩〇]+[\t \u3000]*[章节回卷篇部集])'
    r'|(番外|序章|楔子|后记|尾声|终章|完结|引子|前言|跋|卷首|卷末|插曲|间章|结局)'
    r')[\t \u3000]*[^\n]{0,30}$',
    re.MULTILINE
)

CHINESE_NUMERAL_MAP = {
    '零': 0, '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '百': 100, '千': 1000, '万': 10000, '兩': 2,
}

FALSE_POSITIVE_MARKERS = re.compile(
    r'^(一|二|三|四|五|六|七|八|九|十|万一)[\s]*(回|篇|部|集|卷|节|章)'
)

STRICT_CHAPTER = re.compile(r'第[\s]*[\d零一二三四五六七八九十百千万兩〇]+[\s]*[章回节]')


class Chapter:
    __slots__ = ('index', 'original_title', 'annotated_title', 'start_line',
                 'end_line', 'body_lines', 'is_nsfw', 'nsfw_start_line',
                 'nsfw_end_line', 'nsfw_start_global', 'nsfw_end_global',
                 'nsfw_ratio', 'total_lines')

    def __init__(self, index=0, original_title='', start_line=0, end_line=0,
                 body_lines=None):
        self.index = index
        self.original_title = original_title
        self.annotated_title = original_title
        self.start_line = start_line
        self.end_line = end_line
        self.body_lines = body_lines or []
        self.is_nsfw = False
        self.nsfw_start_line = -1
        self.nsfw_end_line = -1
        self.nsfw_start_global = -1
        self.nsfw_end_global = -1
        self.nsfw_ratio = 0
        self.total_lines = len(self.body_lines)


def _clean_title(header):
    newline = header.find('\n')
    if newline >= 0:
        header = header[:newline]
    return header.strip()


def _is_special_chapter(header):
    return any(kw in header for kw in
               ['番外', '序章', '楔子', '后记', '尾声', '终章', '完结',
                '引子', '前言', '跋', '卷首', '卷末', '插曲', '间章', '结局'])


def detect_chapters(text, work_json):
    lines = text.split('\n')
    total_lines = len(lines)

    raw_matches = list(CHAPTER_PATTERN.finditer(text))
    candidates = []
    for m in raw_matches:
        line_no = text[:m.start()].count('\n')
        if line_no < total_lines:
            raw_header = m.group(0)
            candidates.append({
                'line': line_no,
                'header': _clean_title(raw_header),
                'filtered': False,
                'reason': None,
            })

    work_json['chapter_candidates'] = candidates

    for c in candidates:
        h = c['header']
        if FALSE_POSITIVE_MARKERS.match(h):
            c['filtered'] = True
            c['reason'] = 'false_marker'
            continue
        if len(h) < 3 and not _is_special_chapter(h):
            c['filtered'] = True
            c['reason'] = 'too_short'
            continue
        if len(h) > 30 and not STRICT_CHAPTER.search(h) and not _is_special_chapter(h):
            c['filtered'] = True
            c['reason'] = 'looks_like_body_text'
            continue

    kept = sorted([c for c in candidates if not c['filtered']], key=lambda x: x['line'])

    chapters = []
    for i, item in enumerate(kept):
        start_ln = item['line']
        end_ln = kept[i + 1]['line'] - 1 if i + 1 < len(kept) else total_lines - 1
        body = lines[start_ln + 1:end_ln + 1]
        ch = Chapter(index=i, original_title=item['header'],
                     start_line=start_ln, end_line=end_ln, body_lines=body)
        chapters.append(ch)

    _filter_by_length(chapters, lines, total_lines)

    for i, ch in enumerate(chapters):
        ch.index = i

    return chapters


def _filter_by_length(chapters, lines, total_lines):
    if len(chapters) < 5:
        return

    lengths = [c.total_lines for c in chapters]
    sorted_lens = sorted(lengths)
    n = len(sorted_lens)
    q1 = sorted_lens[n // 4]
    q3 = sorted_lens[3 * n // 4]
    median_len = sorted_lens[n // 2]
    iqr = q3 - q1

    upper_fence = q3 + 3 * iqr
    if upper_fence < median_len * 2:
        upper_fence = median_len * 2

    lower_fence = max(1, median_len * 0.1)

    for ch in chapters:
        too_short = ch.total_lines < lower_fence and ch.total_lines > 0
        too_long = ch.total_lines > upper_fence
        if too_short or too_long:
            has_strict = STRICT_CHAPTER.search(ch.original_title)
            is_special = _is_special_chapter(ch.original_title)
            if not has_strict and not is_special:
                ch.body_lines = []

    chapters[:] = [c for c in chapters if c.body_lines]
