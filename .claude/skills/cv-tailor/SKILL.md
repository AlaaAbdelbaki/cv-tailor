---
name: cv-tailor
description: Tailor the user's CV and write a cover letter for a specific job posting, rendered to PDF through LaTeX. Use when the user pastes a job posting / job description and wants a CV, cover letter, or application documents for it, or runs /cv-tailor.
---

# cv-tailor

Turns `data/master_cv.json` (all of the user's real CV content) plus a pasted job posting into
two PDFs in `applications/<folder>/`, named after the applicant (from `basics.name`, accents
removed) in the document's language:
- French: `CV_Jane_Doe.pdf` and `Lettre_de_motivation_Jane_Doe.pdf`
- English: `CV_Jane_Doe.pdf` and `Cover_Letter_Jane_Doe.pdf`

`scripts/render.py` sets these names automatically, so don't rename the files by hand.

All paths are relative to the project root (the folder containing `scripts/render.py`).

## Golden rule: never invent anything

The master JSON is the only source of facts. You may **select, reorder, shorten and reword**.
You may **not** add or change employers, job titles, dates, degrees, numbers/metrics, tools,
skills or responsibilities that aren't supported by the master. If a rewording would make a claim
stronger than the original (e.g. "contributed to" → "led"), don't make it. The same applies to the cover letter.

## Workflow

1. **Get the inputs**
   - If the user hasn't pasted the job posting, ask for it.
   - Read `data/master_cv.json`. If it doesn't exist, stop and tell the user to create it
     (copy `data/master_cv.example.json` and replace the content). Validate it with
     `python scripts/render.py --validate data/master_cv.json`.

2. **Analyse the posting.** Extract: company, role title, location, must-have requirements,
   nice-to-haves, key terms/technologies, seniority, and anything about culture or mission that
   is worth mentioning in the letter. If the role is unclear, ask.

   **Company details for the letter header.** Check whether the posting gives:
   - the company's **name** (not just "our client" or "a leading fintech", which recruiter postings often use)
   - the **postal address** (street, postcode, city), as used in the recipient block
   - the **recipient** (hiring manager or recruiter name and title), if any

   If the name or address is missing, **ask the user before writing anything**, in a single
   question that lists exactly what's missing. Also ask for the recipient's name, but make it
   optional (they can skip it). Never guess or look up an address on your own. If the user doesn't
   know the address, use only the company name (and city, if the posting gives one) in `recipient`.
   If there's no recipient name, use "Madame, Monsieur," (fr) or "Dear Hiring Team," (en).

3. **Create the application folder** `applications/YYYY-MM-DD_<company>_<role>/` (today's date,
   lowercase, hyphens for spaces, ASCII only). Save the posting verbatim to `job.txt` there.

4. **Write `tailored.json`** in that folder. It uses the same schema as the master
   (`schema/cv.schema.json`), plus:
   - `target`: `{company, role, date}`
   - `summary` (optional): the CV normally has no summary section. Add one only if it clearly
     helps (e.g. explaining a career change), at most 2 lines, facts only. Omit it otherwise.
   - `cover_letter`: `{date, recipient[], subject, greeting, paragraphs[], closing}`.
     `recipient` has one line per entry: contact name and title (if known), company name, street,
     postcode + city. Example: `["Mme Claire Dupont, Responsable RH", "Acme SAS", "12 rue de la Paix", "75002 Paris"]`.
     Put the date in the letter's language: "Paris, le 15 novembre 2026" (fr) or "15 November 2026" (en).
   Drop `summary_variants` and the `$comment`. You can keep or drop `tags`; the renderer ignores them.

   Schema reminders: `experience` and `internships` are separate lists with the same shape
   (`company, url, role, location, work_mode, start, end, bullets[], technologies[]`). Projects have
   `url` (links the name) and `links[]` (e.g. store pages, shown on the right). `basics.links[].icon` is a
   FontAwesome 4 name (`Github`, `LinkedinSquare`, `Globe`).

   **Language**: `lang` (`fr`/`en`) controls the section headings, hyphenation and file names.
   Set it to the posting's language. If that matches the master's language, keep the master's
   wording. Otherwise translate every text field faithfully (title, bullets, degree names, language
   levels, locations, work mode). Keep company and product names as they are. Translation must not
   strengthen any claim.

   Tailoring guidance:
   - Keep every entry in `experience` (dropping a job leaves gaps in the timeline), but keep only the
     3–5 most relevant bullets per role, with the most relevant first. Internships and projects can be
     dropped entirely if unrelated to the posting.
   - Use `tags` to find candidates quickly, but judge by the bullet text.
   - Where it's true, use the posting's own wording (e.g. "CI/CD" instead of "pipelines de déploiement") so
     ATS keyword filters match.
   - `technologies` per entry: reorder so the posting's technologies come first. You can remove
     irrelevant ones but never add one that isn't already in that entry.
   - `basics.title` may be adjusted to match the target role (e.g. "Développeur Mobile Flutter") only if
     the experience in the master actually supports that title.
   - Skills: put the most relevant categories first and the matching items first in each. Drop categories that add nothing for this role.
   - Include only relevant projects and certifications. Always keep education and languages.
   - The renderer uses pdflatex: stick to Latin characters (accents are fine). No emoji, and no
     Arabic or CJK script.
   - Cover letter: 3–4 short paragraphs, under ~350 words. (1) the role and why this company,
     using something specific from the posting; (2–3) 2–3 concrete achievements from the master that
     match the top requirements; (4) a short close. Plain, confident and specific: no clichés
     ("I am writing to express my keen interest…"), no repeating the CV line by line.
     Greet the recipient by name if you have one (from the posting or the user); otherwise use the default greeting from step 2.
     Write in the posting's language unless the user says otherwise.

5. **Render**: `python scripts/render.py applications/<folder>`.
   - Exit code 2 means a schema error: fix `tailored.json` and run it again.
   - Exit code 3 means a LaTeX error: the error lines are printed and the `.tex` is kept in `<folder>/build/`.
   - **Page limit**: the CV must be exactly 1 page.
     The cover letter must be 1 page. If either is too long, remove the least relevant bullets or
     shorten paragraphs, then render again.

6. **Report back** (short):
   - the paths to both PDFs (as printed by `render.py`)
   - **Matched**: the top requirements and the CV content that covers each
   - **Gaps**: requirements with no support in the master. Don't hide these; suggest how the user could
     address them (e.g. a real project they forgot to add to the master).
   - any rewording you weren't sure was still accurate, for the user to check

## Updating the master

If the user mentions experience that isn't in the master, offer to add it to `data/master_cv.json`
(with tags) so future applications can use it. Only add what the user actually states.
