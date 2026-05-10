import json, argparse, sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from lib.encoding import detect_and_decode
from lib.chapter import detect_chapters
from lib.tagger import load_lexicon, tag_chapter


WORK_FILENAME = 'work.json'


def main():
    parser = argparse.ArgumentParser(description='NSFW tagger for Chinese web novels')
    parser.add_argument('--input', required=True)
    parser.add_argument('--lexicon', required=True)
    parser.add_argument('--work-dir', default='.novel-nsfw')
    args = parser.parse_args()

    input_path = Path(args.input)
    lexicon_path = Path(args.lexicon)
    novel_name = input_path.stem
    work_dir = Path(args.work_dir) / novel_name
    work_dir.mkdir(parents=True, exist_ok=True)
    work_path = work_dir / WORK_FILENAME

    wj = _load_or_create(work_path)

    wj['input'] = {'file': str(input_path), 'lexicon': str(lexicon_path)}

    text = detect_and_decode(input_path)
    wj['encoding'] = {
        'lines': len(text.split('\n')),
        'chars': len(text),
        'trad_to_simp': True,
    }

    l0, l1, l2 = load_lexicon(lexicon_path)
    wj['lexicon'] = {'L0': len(l0), 'L1': len(l1), 'L2': len(l2)}

    chapters = detect_chapters(text, wj)

    for ch in chapters:
        tag_chapter(ch, l0, l1, l2)

    merged = []
    for c in wj.pop('chapter_candidates', []):
        if c.get('filtered'):
            merged.append({'header': c['header'], 'line': c['line'],
                           'filtered': True, 'reason': c.get('reason')})
    for ch in chapters:
        merged.append({
            'index': ch.index, 'header': ch.original_title,
            'line': ch.start_line, 'filtered': False,
            'annotated_title': ch.annotated_title, 'is_nsfw': ch.is_nsfw,
            'nsfw_start_global': ch.nsfw_start_global,
            'nsfw_end_global': ch.nsfw_end_global,
            'nsfw_ratio': ch.nsfw_ratio,
        })
    merged.sort(key=lambda x: x['line'])
    for i, m in enumerate(m for m in merged if not m['filtered']):
        m['index'] = i
    wj['chapters'] = merged

    nsfw_count = sum(1 for c in wj['chapters'] if not c['filtered'] and c.get('is_nsfw'))

    _write_tagged_text(text, chapters, text.split('\n'), work_dir, novel_name)

    work_path.write_text(json.dumps(wj, ensure_ascii=False, indent=2))

    print(f"Done. {nsfw_count}/{len(chapters)} chapters tagged NSFW.")
    print(f"  Work file: {work_path}")
    print(f"  Annotated text: {work_dir / f'{novel_name}_tagged.txt'}")


def _write_tagged_text(text, chapters, lines, work_dir, novel_name):
    output = list(lines)
    for ch in chapters:
        if ch.original_title and ch.start_line < len(output):
            output[ch.start_line] = output[ch.start_line].replace(
                ch.original_title, ch.annotated_title, 1)
        if ch.is_nsfw and ch.nsfw_start_global >= 0:
            if ch.nsfw_start_global < len(output):
                output[ch.nsfw_start_global] = '<nsfw_start/>' + output[ch.nsfw_start_global]
            if ch.nsfw_end_global < len(output):
                output[ch.nsfw_end_global] = output[ch.nsfw_end_global] + '<nsfw_end/>'
    out_path = work_dir / f'{novel_name}_tagged.txt'
    out_path.write_text('\n'.join(output))


def _load_or_create(work_path):
    if work_path.exists():
        return json.loads(work_path.read_text())
    return {}


if __name__ == '__main__':
    main()
