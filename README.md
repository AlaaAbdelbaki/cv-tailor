# cv-cover-gen

A [Claude Code](https://claude.com/claude-code) skill that tailors your CV and writes a cover letter for a specific job posting, then renders both to PDF with LaTeX.

All your CV content lives in **one structured JSON file** (your "master CV"). For each job, Claude selects, reorders and rewords the most relevant parts. It never invents experience. The result is rendered through LaTeX templates, so the layout is the same every time.

```
master_cv.json + job posting  →  Claude (/cv-tailor)  →  tailored.json  →  render.py + LaTeX  →  PDFs
```

## Features

- `/cv-tailor` skill: paste a job posting and get a tailored CV plus a cover letter
- Strict "no invention" rule: facts, dates and numbers only come from your master CV
- Asks for missing company details (name, address, contact) before writing the letter
- Reports which requirements you match and where you have **gaps**
- French and English output (section headings, hyphenation, file names)
- Keeps the CV to one page
- Files named after the applicant: `CV_Jane_Doe.pdf`, `Lettre_de_motivation_Jane_Doe.pdf` / `Cover_Letter_Jane_Doe.pdf`

## Requirements

- [Claude Code](https://claude.com/claude-code)
- Python 3.10+ with `jinja2` and `jsonschema`: `pip install jinja2 jsonschema`
- A LaTeX distribution with `pdflatex` ([MiKTeX](https://miktex.org/) or [TeX Live](https://tug.org/texlive/)), including the `raleway`, `fontawesome`, `moresize`, `tikz`, `babel-french` and `longtable` packages. MiKTeX can install missing packages on first run.

## Setup

1. Copy the sample and replace its content with your own:
   ```sh
   cp data/master_cv.example.json data/master_cv.json
   ```
   Put **everything** in it: every job, internship, project and bullet you might ever want to use. Add a few `tags` per bullet (e.g. `mobile`, `testing`, `leadership`) to help Claude pick the right ones. Delete the `$comment`, `target` and `cover_letter` fields; those are only there so the sample renders a letter.
2. Validate it:
   ```sh
   python scripts/render.py --validate data/master_cv.json
   ```
3. Check that the templates render on your machine:
   ```sh
   python scripts/render.py --example   # writes applications/_example/*.pdf
   ```

`data/master_cv.json` and `applications/` are git-ignored, so your personal data stays local.

## Usage

Open Claude Code in this folder and run:

```
/cv-tailor <paste the job posting>
```

Claude will:
1. analyse the posting and ask for anything missing (company address, contact name),
2. create `applications/<date>_<company>_<role>/` with `job.txt` and `tailored.json`,
3. render the CV and cover letter PDFs and keep the CV to one page,
4. report the requirements you match, the gaps, and any wording you should double-check.

To re-render after editing a `tailored.json` by hand:

```sh
python scripts/render.py applications/<folder>
```

## Project layout

| Path | Purpose |
|---|---|
| `.claude/skills/cv-tailor/SKILL.md` | The skill: workflow and rules Claude follows |
| `data/master_cv.example.json` | Fictional sample master CV |
| `schema/cv.schema.json` | JSON Schema for master and tailored files |
| `scripts/render.py` | Validates JSON, fills the templates, compiles PDFs with pdflatex |
| `templates/cv.tex.j2`, `cover_letter.tex.j2` | Jinja2 + LaTeX templates (`\VAR{}` inserts a value, `\BLOCK{}` adds logic) |
| `templates/_header.tex.j2`, `_language.tex.j2` | Shared header and language setup |
| `templates/developercv.cls` | LaTeX class used for the layout |

## Credits

The layout uses the **Developer CV** LaTeX class from [LaTeXTemplates.com](https://www.latextemplates.com/) by Omar Roldan, based on templates by Jan Vorisek and Jan Küster, modified by Vel. It is used under the MIT License; see [`templates/LICENSE-developercv.txt`](templates/LICENSE-developercv.txt).
