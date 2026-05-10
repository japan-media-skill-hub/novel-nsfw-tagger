# Novel NSFW Tagger Skill

Pure-algorithm NSFW content tagging for Chinese web novels. This project provides a reusable skill package that marks NSFW chapters and inserts inline NSFW span markers without using an LLM.

## Features

- Detects chapter structure in common Chinese novel formats
- Uses a tiered lexicon (L0/L1/L2) with co-occurrence rules to reduce false positives
- Annotates chapter titles with `(nsfw XX)` ratio labels
- Inserts `<nsfw_start/>` and `<nsfw_end/>` inline markers into output text
- Supports `.txt` and `.epub` inputs (epub requires extra dependencies)
- Produces auditable work artifacts (`work.json`) per novel

## Project Structure

- `skills/novel-nsfw-tagger/SKILL.md`: skill definition and behavior documentation
- `skills/novel-nsfw-tagger/scripts/tag.py`: main tagging entrypoint
- `skills/novel-nsfw-tagger/scripts/validate.py`: validation script for generated outputs
- `skills/novel-nsfw-tagger/config/lexicon.json`: NSFW keyword lexicon
- `example/`: sample novel files for local testing

## Requirements

- Python 3.10+
- Optional for epub input:
  - `ebooklib`
  - `beautifulsoup4`

Install optional packages:

```bash
pip install ebooklib beautifulsoup4
```

## Quick Start

Run tagging:

```bash
python skills/novel-nsfw-tagger/scripts/tag.py \
  --input "example/放开那个女巫 八改豪华魔改修改整合版.txt" \
  --lexicon "skills/novel-nsfw-tagger/config/lexicon.json" \
  --work-dir .novel-nsfw
```

After completion, results are written to:

- `.novel-nsfw/<novel_name>/work.json`
- `.novel-nsfw/<novel_name>/<novel_name>_tagged.txt`

Run validation:

```bash
python skills/novel-nsfw-tagger/scripts/validate.py .novel-nsfw
```

## Output Format

- Chapter title annotation example:

```text
第0035章❤归宿（夜莺，安娜，娜娜瓦，百合）(nsfw 63)
```

- Inline marker example:

```text
<nsfw_start/>......
......<nsfw_end/>
```

## Disclaimer

This repository is intended for technical research, text processing, and content classification workflows only.

- It may process or label sexually explicit text.
- You are solely responsible for ensuring your input data, usage scenario, and distribution comply with all applicable laws and platform policies in your jurisdiction.
- Do not use this project to process illegal content, exploitative content, or any material involving minors.
- The keyword-based approach is heuristic and can produce false positives or false negatives; always perform human review before any high-impact decision.

See `DISCLAIMER.md` for the full disclaimer text.

## License

No license file is included by default in this repository state. Add a LICENSE file before public distribution if you want to define usage terms explicitly.
