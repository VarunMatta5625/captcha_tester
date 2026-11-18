"""Checks the Markdown after an edit.

    python3 tools/readme_visuals/check_docs.py            (from the repository root)
    python3 tools/readme_visuals/check_docs.py --no-diagrams    skip the Mermaid and math parse (needs node + npm)

1. Every relative link, image path and #anchor in README.md and docs/*.md exists, and no image in docs/images/ is unused.
2. Every ```mermaid block parses and every ```math block parses in KaTeX. This installs @mermaid-js/mermaid-cli and
   katex into a temporary folder; mermaid-cli needs a Chromium: set CHROME to its path
   (for Playwright's: ~/Library/Caches/ms-playwright/chromium-*/chrome-mac*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing).
GitHub's own rendering of Mermaid cannot be checked offline: look at the page after pushing.
"""
import glob, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
DOCS = ["README.md", "extension/README.txt", "archive/README.md"] + sorted(glob.glob("docs/*.md"))


def slug(h):
    h = re.sub(r"[`*_]", "", h.strip().lower())
    return re.sub(r"[^\w\- ]", "", h).replace(" ", "-")


def headings(text):
    return {slug(m.group(2)) for m in re.finditer(r"^(#{1,6})\s+(.*)$", text, re.M)}


def links():
    bad, used = 0, set()
    for f in DOCS:
        base, text = os.path.dirname(f), open(f).read()
        own = headings(text)
        for r in re.findall(r'(?:src|href)="([^"]+)"', text) + re.findall(r"\]\(([^)\s]+)\)", text):
            if r.startswith(("http", "mailto:")):
                continue
            path, _, frag = r.partition("#")
            if not path:
                if frag and frag not in own:
                    print("BAD ANCHOR", f, r); bad += 1
                continue
            target = os.path.normpath(os.path.join(base, path))
            if not os.path.exists(target):
                print("MISSING", f, r); bad += 1
                continue
            used.add(target)
            if frag and target.endswith(".md") and frag not in headings(open(target).read()):
                print("BAD ANCHOR", f, r); bad += 1
    unused = sorted(set(glob.glob("docs/images/*")) - used)
    for u in unused:
        print("UNUSED IMAGE", u)
    print(f"links: {bad} problems, {len(unused)} unused images")
    return bad + len(unused)


def diagrams():
    mer, maths = [], []
    for f in DOCS:
        text = open(f).read()
        mer += re.findall(r"```mermaid\n(.*?)```", text, re.S)
        maths += re.findall(r"```math\n(.*?)```", text, re.S)
    tmp = tempfile.mkdtemp(prefix="docs_check_")
    subprocess.run(["npm", "init", "-y"], cwd=tmp, capture_output=True, check=True)
    subprocess.run(["npm", "i", "katex", "@mermaid-js/mermaid-cli"], cwd=tmp, capture_output=True, check=True)
    fails = 0
    chrome = os.environ.get("CHROME")
    cfg = os.path.join(tmp, "pp.json")
    json.dump({"args": ["--no-sandbox"], **({"executablePath": chrome} if chrome else {})}, open(cfg, "w"))
    for n, src in enumerate(mer, 1):
        path = os.path.join(tmp, f"{n}.mmd")
        open(path, "w").write(src)
        r = subprocess.run([os.path.join(tmp, "node_modules", ".bin", "mmdc"), "-p", cfg, "-i", path, "-o", path + ".svg", "-q"],
                           capture_output=True, text=True)
        print(f"mermaid {n}: {'ok' if r.returncode == 0 else 'FAILED ' + r.stderr[-300:]}")
        fails += r.returncode != 0
    json.dump(maths, open(os.path.join(tmp, "maths.json"), "w"))
    r = subprocess.run(["node", "-e", 'const k=require("katex");const m=require("./maths.json");'
                        'm.forEach((x,i)=>{k.renderToString(x,{throwOnError:true,displayMode:true});console.log("math",i+1,"ok")})'],
                       cwd=tmp, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr[-400:])
    return fails + (r.returncode != 0)


if __name__ == "__main__":
    problems = links()
    if "--no-diagrams" not in sys.argv:
        problems += diagrams()
    sys.exit(1 if problems else 0)
