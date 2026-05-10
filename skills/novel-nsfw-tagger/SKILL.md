---
name: novel-nsfw-tagger
description: Detects NSFW content in Chinese web novels using a pure-algorithm keyword lexicon approach. Tags chapter titles with (nsfw XX) notation and inserts <nsfw_start/>/<nsfw_end/> inline markers. Use when the user needs to scan Chinese novels for adult content, mark NSFW chapters and passages, analyze content composition, or prepare annotated novel files. Triggers on: NSFW detection, adult content tagging, Chinese novel scanning, 加料 detection, 色情标记, chapter content analysis.
---

# Novel NSFW Tagger

Pure-algorithm NSFW content detection for Chinese web novels. Uses a tiered keyword lexicon (L0/L1/L2) with paragraph-level co-occurrence rules. No LLM required.

## When to use

- Scanning Chinese web novels for adult/explicit content
- Tagging chapter titles with NSFW percentage
- Inserting inline NSFW span markers into novel text
- Preparing annotated novel files for reading/curation
- Analyzing content composition across a novel collection

## How it works

The pipeline has 4 stages, each producing audit artifacts in a working directory:

1. **Encoding detection & normalization** — auto-detects UTF-16LE/UTF-8/GBK → normalized UTF-8, then converts Traditional Chinese to Simplified (zhconv)
2. **Chapter detection** — comprehensive regex matching Chinese chapter patterns, with false-positive filtering
3. **Paragraph-level NSFW scoring** — L0/L1/L2 tiered keyword matching with co-occurrence rules
4. **Span extraction & annotation** — first hot paragraph to last hot paragraph, with ratio calculation

### Keyword tiers

| Tier | Weight | Examples | Rule |
|------|--------|----------|------|
| **L0** | Strong | 肉棒, 蜜穴, 精液, 淫水, 抽插, 肏 | 1 hit = paragraph is hot |
| **L1** | Medium | 插入, 高潮, 呻吟, 乳房, 乳头, 舔舐, 揉捏 | 3+ hits = hot, or 2+ L1 + 2+ L2 |
| **L2** | Weak | 抚摸, 赤裸, 接吻, 巨龙, 花径, 酥软 | Only counted when L0 or L1 present |

L2 keywords are **anchored** — they only contribute to the paragraph score when at least one L0 or L1 keyword is also present in the same paragraph. This prevents neutral words like 巨龙 (dragon) or 赤裸 (naked) from triggering false positives in non-sexual contexts.

### Span logic

For each chapter, find the **first paragraph** with any hot match and the **last paragraph** with any hot match. The span from first to last (inclusive) is the NSFW passage. Ratio = span paragraphs / total paragraphs × 100.

A chapter is tagged NSFW only if ratio ≥ 5%.

### Output format

**Title annotation** (modified in-place on the original title line):
```
第0035章❤归宿（夜莺，安娜，娜娜瓦，百合）(nsfw 63)
```

**Inline markers** (inserted at the start/end lines of the NSFW span, not on separate lines):
```
<nsfw_start/>夜莺行走在「迷雾」中。从这里看去，世界只剩下黑白二色...
...夜莺不禁又好气又好笑，自己一晚上让这两个丫头爽了个够。<nsfw_end/>
```

**JSON summary** per novel (in working directory):
```json
{
  "total_chapters": 1506,
  "nsfw_count": 142,
  "chapters": [
    {
      "index": 0,
      "original_title": "第0001章从今天开始做王子",
      "annotated_title": "第0001章从今天开始做王子",
      "is_nsfw": false,
      "nsfw_ratio": 0,
      "nsfw_start_global": -1,
      "nsfw_end_global": -1
    }
  ]
}
```

## Usage

```bash
python scripts/tag.py \
  --input "/path/to/novel.txt" \
  --lexicon config/lexicon.json \
  --work-dir .novel-nsfw
```

The working directory `.novel-nsfw/{novel_name}/` contains audit artifacts:
- `00_input.json` — input file metadata
- `01_encoding.json` — detected encoding and text stats
- `02_lexicon.json` — lexicon tier counts
- `01_chapter_candidates.json` — raw regex matches before filtering
- `02_chapters_cleaned.json` — after false-positive removal
- `03_chapters.json` — chapter count
- `04_summary.json` — full results with per-chapter details

The annotated text is at `.novel-nsfw/{novel_name}/{novel_name}_tagged.txt`.

## Lexicon customization

Edit `config/lexicon.json` to add or remove keywords. The file has three arrays:
- `L0`: unambiguous explicit terms (strongest signal)
- `L1`: sexual but context-dependent terms
- `L2`: suggestive/ambiguous terms (anchored, requires L0/L1 co-occurrence)

Only multi-character words are used. The single character `肏` is the sole exception in L0.

## Chapter detection regex

The chapter regex handles these Chinese novel chapter header patterns:
- `第001章` / `第1章` / `第一章` / `第一回` / `第1节`
- `章一` / `卷一` / `篇一`
- `番外` / `序章` / `楔子` / `后记` / `尾声` / `终章` / `完结`
- With up to 50 characters of title text after the marker

False-positive filtering removes short matches like `一回`, `一篇`, `万一回` that appear as body text rather than actual chapter headers.

## Supported encodings

- UTF-8 (with/without BOM)
- UTF-16LE (most common for Chinese web novels)
- UTF-16BE
- GB18030 / GBK

## Supported input formats

- Plain text (.txt) — any supported encoding
- EPUB (.epub) — requires `pip install ebooklib` and `beautifulsoup4`; text is extracted from HTML chapters
