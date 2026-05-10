import json, sys, re, glob
from pathlib import Path

WORK_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.novel-nsfw')
PASS, FAIL = 0, 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} — {detail}")

print("=" * 60)
print("NSFW TAGGER VALIDATION")
print("=" * 60)

# --- Eval 1: ❤ chapter recall ---
print("\n[Eval 1] ❤ Chapter Recall")
for novel_dir in WORK_DIR.iterdir():
    if not novel_dir.is_dir():
        continue
    summary = novel_dir / "04_summary.json"
    if not summary.exists():
        continue
    with open(summary) as f:
        data = json.load(f)
    chs = data.get('chapters', [])
    hearts = [c for c in chs if '❤' in c.get('original_title', '') or '♥' in c.get('original_title', '')]
    if not hearts:
        continue
    missed = [c for c in hearts if not c.get('is_nsfw')]
    check(
        f"All {len(hearts)} ❤ chapters detected in {novel_dir.name[:30]}",
        len(missed) == 0,
        f"Missed {len(missed)}: {[c['original_title'][:60] for c in missed]}"
    )
    # Also check ratio >= 5
    low_ratio = [c for c in hearts if c.get('is_nsfw') and c.get('nsfw_ratio', 0) < 5]
    check(
        f"All detected ❤ chapters have ratio >= 5",
        len(low_ratio) == 0,
        f"{len(low_ratio)} with ratio < 5"
    )

# --- Eval 2: weapon chapter NOT tagged ---
print("\n[Eval 2] Weapon Chapter False Positive Check")
for novel_dir in WORK_DIR.iterdir():
    if not novel_dir.is_dir():
        continue
    summary = novel_dir / "04_summary.json"
    if not summary.exists():
        continue
    with open(summary) as f:
        data = json.load(f)
    chs = data.get('chapters', [])
    weapon = [c for c in chs if '火炮试射' in c.get('original_title', '')]
    if weapon:
        check(
            f"火炮试射 NOT tagged NSFW",
            not weapon[0].get('is_nsfw'),
            f"Tagged with ratio={weapon[0].get('nsfw_ratio')}"
        )

# --- Eval 3: output format ---
print("\n[Eval 3] Output Format Correctness")
tagged_files = list(WORK_DIR.glob("*/*_tagged.txt"))
check(f"Tagged output files exist", len(tagged_files) > 0)
for tf in tagged_files[:1]:
    text = tf.read_text()
    has_title_anno = bool(re.search(r'\(nsfw\s+\d+\)', text))
    has_start = '<nsfw_start/>' in text
    has_end = '<nsfw_end/>' in text
    check(f"Title annotation format (nsfw XX)", has_title_anno)
    check(f"<nsfw_start/> markers present", has_start)
    check(f"<nsfw_end/> markers present", has_end)

# --- Eval 4: cross-novel adult rate ---
print("\n[Eval 4] Cross-Novel Consistency")
for novel_dir in WORK_DIR.iterdir():
    if not novel_dir.is_dir():
        continue
    summary = novel_dir / "04_summary.json"
    if not summary.exists():
        continue
    with open(summary) as f:
        data = json.load(f)
    chs = data.get('chapters', [])
    nsfw = [c for c in chs if c.get('is_nsfw')]
    name = novel_dir.name[:40]
    check(f"{name}: {len(nsfw)}/{len(chs)} NSFW chapters", len(chs) > 0)

# --- Eval 5: encoding detection ---
print("\n[Eval 5] Encoding Detection")
for novel_dir in WORK_DIR.iterdir():
    if not novel_dir.is_dir():
        continue
    enc_file = novel_dir / "01_encoding.json"
    if not enc_file.exists():
        continue
    with open(enc_file) as f:
        data = json.load(f)
    check(f"{novel_dir.name[:30]}: lines={data.get('lines', 0)}", data.get('lines', 0) > 100)

# --- Summary ---
print("\n" + "=" * 60)
total = PASS + FAIL
print(f"RESULTS: {PASS}/{total} passed ({FAIL} failed)")
if FAIL == 0:
    print("ALL CHECKS PASSED")
else:
    print(f"{FAIL} CHECK(S) FAILED — review details above")
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
