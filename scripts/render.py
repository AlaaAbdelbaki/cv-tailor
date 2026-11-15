"""Render a CV JSON file into CV_<Name>.pdf (and Lettre_de_motivation_<Name>.pdf / Cover_Letter_<Name>.pdf
if the JSON has a cover letter). File names follow the JSON's "lang".

Usage:
    python scripts/render.py <application_dir>     # reads <dir>/tailored.json, writes PDFs into <dir>
    python scripts/render.py --example             # renders data/master_cv.example.json into applications/_example
    python scripts/render.py --validate <file.json> # schema check only, no PDF
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

import jinja2
import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema" / "cv.schema.json"
TEMPLATES = ROOT / "templates"
CLASS_FILE = TEMPLATES / "developercv.cls"

LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_SPECIALS_RE = re.compile("|".join(re.escape(c) for c in LATEX_SPECIALS))


def tex(s: str) -> str:
    """Escape text for LaTeX body content."""
    return _SPECIALS_RE.sub(lambda m: LATEX_SPECIALS[m.group()], s)


def tex_url(s: str) -> str:
    """Escape a URL for use as the first argument of \\href."""
    return s.replace("\\", "/").replace("%", r"\%").replace("#", r"\#")


def escape_tree(obj, key=None):
    if isinstance(obj, dict):
        return {k: escape_tree(v, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [escape_tree(v, key) for v in obj]
    if isinstance(obj, str):
        return tex_url(obj) if key == "url" else tex(obj)
    return obj


def validate(data: dict, source: Path) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    if errors:
        print(f"Schema errors in {source}:", file=sys.stderr)
        for e in errors:
            where = "/".join(str(p) for p in e.path) or "(root)"
            print(f"  - {where}: {e.message}", file=sys.stderr)
        sys.exit(2)


LABELS = {
    "fr": {
        "summary": "À propos", "skills": "Compétences Techniques",
        "experience": "Expériences professionnelles", "internships": "Stages",
        "education": "Parcours académique", "projects": "Projets",
        "certifications": "Certifications", "languages": "Langues",
        "technologies": "Technologies", "present": "Présent",
    },
    "en": {
        "summary": "Profile", "skills": "Technical Skills",
        "experience": "Professional Experience", "internships": "Internships",
        "education": "Education", "projects": "Projects",
        "certifications": "Certifications", "languages": "Languages",
        "technologies": "Technologies", "present": "Present",
    },
}


def build_context(data: dict) -> dict:
    b = data["basics"]
    # Header layout from the original template: phone + location | email + links
    col1, col2 = [], []
    if b.get("phone"):
        tel = "tel:" + re.sub(r"[^\d+]", "", b["phone"])
        col1.append({"icon": "Phone", "text": rf"\href{{{tel}}}{{{tex(b['phone'])}}}"})
    if b.get("location"):
        col1.append({"icon": "MapMarker", "text": tex(b["location"])})
    col2.append({"icon": "Envelope", "text": rf"\href{{mailto:{tex_url(b['email'])}}}{{{tex(b['email'])}}}"})
    for link in b.get("links", []):
        col2.append({
            "icon": link.get("icon", "Globe"),
            "text": rf"\href{{{tex_url(link['url'])}}}{{{tex(link['label'])}}}",
        })

    ctx = escape_tree(data)
    ctx["contact_col1"], ctx["contact_col2"] = col1, col2
    ctx["labels"] = LABELS[data.get("lang", "fr")]
    ctx["babel_lang"] = {"fr": "french", "en": "english"}[data.get("lang", "fr")]
    return ctx


def ttlist(items) -> str:
    """Comma-separated list in typewriter font (replaces the original \\printlist macro)."""
    return ", ".join(rf"\texttt{{{i}}}" for i in items)


def make_env() -> jinja2.Environment:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES)),
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    env.filters["ttlist"] = ttlist
    return env


DOC_PREFIX = {
    "fr": {"cv": "CV", "cover_letter": "Lettre_de_motivation"},
    "en": {"cv": "CV", "cover_letter": "Cover_Letter"},
}


def output_name(doc: str, data: dict) -> str:
    """e.g. CV_Jane_Doe.pdf / Lettre_de_motivation_Lea_Moreau-Nunez.pdf (ASCII, no spaces)."""
    name = unicodedata.normalize("NFKD", data["basics"]["name"]).encode("ascii", "ignore").decode()
    name = re.sub(r"[^A-Za-z0-9-]+", "_", name).strip("_")
    return f"{DOC_PREFIX[data.get('lang', 'fr')][doc]}_{name}.pdf"


def compile_pdf(tex_source: str, name: str, out_dir: Path, out_file: str) -> int:
    """Compile with pdflatex into out_dir/out_file; return page count. Leaves build files only on failure."""
    build = out_dir / "build"
    build.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CLASS_FILE, build / CLASS_FILE.name)
    tex_file = build / f"{name}.tex"
    tex_file.write_text(tex_source, encoding="utf-8")
    proc = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_file.name],
        cwd=build, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    log_file = build / f"{name}.log"
    log = log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() else proc.stdout
    if proc.returncode != 0 or not (build / f"{name}.pdf").exists():
        print(f"LaTeX failed for {name}. Error lines from {log_file}:", file=sys.stderr)
        lines = log.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("!"):
                print("\n".join(lines[i:i + 4]), file=sys.stderr)
        sys.exit(3)
    shutil.copy2(build / f"{name}.pdf", out_dir / out_file)
    m = re.search(r"Output written on .*?\((\d+) pages?", log.replace("\n", ""))  # log wraps at 79 cols
    return int(m.group(1)) if m else -1


def render(json_path: Path, out_dir: Path) -> None:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    validate(data, json_path)
    ctx = build_context(data)
    env = make_env()
    out_dir.mkdir(parents=True, exist_ok=True)

    for doc in ("cv", "cover_letter"):
        if doc == "cover_letter" and "cover_letter" not in ctx:
            continue
        out_file = output_name(doc, data)
        pages = compile_pdf(env.get_template(f"{doc}.tex.j2").render(**ctx), doc, out_dir, out_file)
        print(f"{doc}: {pages} page(s) -> {out_dir / out_file}")
    if "cover_letter" not in ctx:
        print("No cover_letter in JSON; skipped cover letter.")
    shutil.rmtree(out_dir / "build", ignore_errors=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("app_dir", nargs="?", type=Path, help="application folder containing tailored.json")
    g.add_argument("--example", action="store_true", help="render the fictional sample")
    g.add_argument("--validate", type=Path, metavar="JSON", help="only validate a JSON file")
    args = ap.parse_args()

    if args.validate:
        validate(json.loads(args.validate.read_text(encoding="utf-8")), args.validate)
        print(f"{args.validate}: valid")
    elif args.example:
        render(ROOT / "data" / "master_cv.example.json", ROOT / "applications" / "_example")
    else:
        src = args.app_dir / "tailored.json"
        if not src.exists():
            sys.exit(f"Not found: {src}")
        render(src, args.app_dir)


if __name__ == "__main__":
    main()
