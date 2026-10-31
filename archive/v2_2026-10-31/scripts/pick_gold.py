# New gold set: GOLD_NEW captchas picked where the models most likely fail, plus the old gold re-checked blind.
# Run from the notebook after hardness.py:  %run -i ../scripts/pick_gold.py
#
# Every captcha falls in one stratum (from HARDNESS_CSV): the CNNs in READERS disagree, or they agree but Vision reads
# something else, or everyone agrees; the last two split by the CNNs' weakest-character confidence (CONF_LOW).
# ALLOC captchas are drawn at random inside each stratum, most from the hard ones. Since each stratum's size is kept,
# gold gives two scores: accuracy on the (hard) gold itself, and a weighted estimate of accuracy on all captchas.
# Reviewed captchas are left out (they are trained on). The old gold (OLD_GOLD_CSV) is added unlabeled, so you
# re-check it without seeing its old label.
#
# Writes SHEET_CSV (serial, id, stratum, stratum_size, source) and SHEET_PDF (15 captchas per page, numbered by
# serial, no answers or instructions shown), also split one file per page into SHEET_PDF's "_pages" folder.
# Answer in chat as "serial text" lines.
from PIL import ImageDraw, ImageFont

CONF_LOW = 0.7
ALLOC = {"split": 230, "vision_low": 90, "agree_low": 80, "vision_high": 50, "agree_high": 50}   # sums to GOLD_NEW
GOLD_NEW = 500
assert sum(ALLOC.values()) == GOLD_NEW


def stratum(r):
    reads = {r[n] for n in READERS}
    if len(reads) > 1:
        return "split"
    low = min(float(r[f"{n}_conf"]) for n in READERS) < CONF_LOW
    if r["vision"] != reads.pop():
        return "vision_low" if low else "vision_high"
    return "agree_low" if low else "agree_high"


with open(HARDNESS_CSV) as f:
    strata = {r["id"]: stratum(r) for r in csv.DictReader(f)}
sizes = Counter(strata.values())
with open(OLD_GOLD_CSV) as f:
    old_gold = [r["id"] for r in csv.DictReader(f)]
reviews = json.load(open(REVIEWS)) if os.path.exists(REVIEWS) else {}

rng = random.Random(SEED)
picked = []
for s, n in ALLOC.items():
    pool = sorted((i for i, t in strata.items() if t == s and i not in reviews and i not in old_gold), key=int)
    picked += [(i, "new") for i in rng.sample(pool, n)]
picked += [(i, "old_gold") for i in old_gold]
rng.shuffle(picked)   # old and new mixed, strata mixed: nothing to tell them apart while answering

with open(SHEET_CSV, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["serial", "id", "stratum", "stratum_size", "source"])
    for serial, (i, src) in enumerate(picked, 1):
        w.writerow([serial, i, strata[i], sizes[strata[i]], src])

# PDF: A4 landscape, 3 columns x 5 rows, each captcha 4x its size under its serial
PER_PAGE, COLS, SCALE = 15, 3, 4
PAGE_W, PAGE_H, MARGIN, HEADER = 2000, 1414, 60, 70
cell_w, cell_h = (PAGE_W - 2 * MARGIN) // COLS, (PAGE_H - 2 * MARGIN - HEADER) // (PER_PAGE // COLS)
big, small = ImageFont.load_default(40), ImageFont.load_default(26)
pages, n_pages = [], math.ceil(len(picked) / PER_PAGE)
for p in range(n_pages):
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    d = ImageDraw.Draw(page)
    d.text((MARGIN, MARGIN), "Image processing experiment", fill="black", font=small)
    for k, (i, _) in enumerate(picked[p * PER_PAGE:(p + 1) * PER_PAGE]):
        serial = p * PER_PAGE + k + 1
        x = MARGIN + (k % COLS) * cell_w
        y = MARGIN + HEADER + (k // COLS) * cell_h
        img = prep.open_captcha(i).convert("RGB")
        img = img.resize((img.width * SCALE, img.height * SCALE), Image.LANCZOS)
        d.text((x, y), f"#{serial}", fill="black", font=big)
        page.paste(img, (x, y + 50))
        d.rectangle((x - 1, y + 49, x + img.width, y + 50 + img.height), outline="gray")
    pages.append(page)
pages[0].save(SHEET_PDF, save_all=True, append_images=pages[1:], resolution=PAGE_W / 11.69)
pages_dir = SHEET_PDF[:-4] + "_pages"   # the same sheet, one PDF per page
os.makedirs(pages_dir, exist_ok=True)
for p, page in enumerate(pages, 1):
    page.save(os.path.join(pages_dir, f"page_{p:02d}.pdf"), resolution=PAGE_W / 11.69)

print(f"wrote {SHEET_CSV} and {SHEET_PDF}: {len(picked)} captchas ({GOLD_NEW} new + {len(old_gold)} old gold), "
      f"{n_pages} pages")
for s, n in ALLOC.items():
    print(f"  {s:<12} {n:>4} picked of {sizes[s]:>6}")
