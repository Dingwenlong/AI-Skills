---
name: beautiful-brochure-pdf
description: "Create polished marketing brochure PDFs, product catalogs, company profiles, pitch handouts, event brochures, service booklets, and Chinese 宣传册/产品册/招商手册/型录. Use when Codex needs to turn a brief, rough copy, brand assets, product images, or web/source material into a visually designed multi-page PDF with cover, page architecture, HTML/CSS layout, export, and rendered visual QA."
---

# Beautiful Brochure PDF

## Purpose

Create brochure-grade PDFs that feel designed, not merely exported. Prioritize art direction, page rhythm, typography, image treatment, and final rendered QA.

Use the local `pdf` skill for PDF generation/checking mechanics and `frontend-design` judgment for HTML/CSS visual quality when those skills are available.

## Output Convention

Write working files under the current workspace:

```text
output/pdf/beautiful-brochure-pdf/{project-slug}/
```

Keep source files beside the PDF:

- `brief.json` or `brief.md` for normalized requirements
- `index.html` and `styles.css` for editable layout source
- `assets/` for logo, product images, generated imagery, icons, and exported charts
- `renders/` for page PNGs used during visual QA
- `{project-slug}.pdf` for the final brochure

## Workflow

1. Normalize the brief.
   - Identify brochure purpose, audience, offer, page count, format, language, brand constraints, required content, and available assets.
   - If page count is missing, choose a practical default: 6 pages for a compact brochure, 8 pages for a product/service brochure, or 12 pages for a richer company profile.
   - If visual style is missing, infer one from the domain and content, then state the chosen direction briefly.

2. Plan the brochure before layout.
   - Produce a page map with each page's job, dominant visual, main headline, and proof/detail elements.
   - Put the brand/product/service signal on page 1. Do not start with a generic landing page.
   - Keep selling points concrete: outcomes, differentiators, process, proof, cases, specs, team, and contact/action.

3. Choose a deliberate art direction.
   - Prefer one clear design personality: refined luxury, editorial magazine, technical precision, warm service, cultural craft, financial trust, medical clarity, education-friendly, or industrial product.
   - Use the user provided logo/product/brand assets first. For specific real products or venues, prefer real images over generated mood images.
   - Use generated imagery only for conceptual backgrounds, covers, abstract visuals, or missing non-specific illustrations.

4. Build with HTML/CSS first.
   - Use `scripts/create_brochure_scaffold.py` to create a starting project when helpful.
   - Use fixed print page dimensions with CSS `@page` and `.page` containers.
   - Use CSS variables for color, spacing, type scale, and theme.
   - Keep all image URLs local to the project before final export.
   - Avoid nested cards, generic purple gradients, decorative orbs, and text-heavy pages that look like slides pasted into a PDF.

5. Export to PDF.
   - Preferred: Playwright/Chromium `page.pdf()` with `printBackground: true`, then save to the project folder.
   - Good fallback: system Chrome/Edge headless print-to-PDF.
   - Use `reportlab` only when the layout is mostly document-like or HTML export is unavailable.

6. Render and inspect every page.
   - Render PDF pages to PNG with `pdftoppm` when available.
   - If Poppler is unavailable, use PyMuPDF (`fitz`) or another local renderer.
   - Inspect the PNGs visually before delivery. Iterate until there are no clipped titles, text overflow, broken glyphs, blurry assets, awkward widows/orphans, or inconsistent margins.

## Design Rules

- Design for print first: stable page size, safe margins, consistent footer/page numbering, and image resolution appropriate for the final size.
- Give every page a clear hierarchy: one lead message, supporting copy, and a visual anchor.
- Use restrained body copy. Turn long paragraphs into proof blocks, specs, timelines, callouts, or comparison tables.
- Keep Chinese brochure typography clean: prefer `Microsoft YaHei`, `Source Han Sans SC`, `Noto Sans CJK SC`, or another available CJK font; avoid tiny body text below 8.5pt equivalent.
- Make covers inspectable: the object, brand, offer, or place should be obvious in the first viewport/page.
- Keep page-to-page rhythm varied: cover, overview, feature spread, detail/spec, proof/case, process, closing/contact.
- Check mobile/web screenshots only as a layout aid; the PDF render is the source of truth.

## Resources

- Read `references/brochure_design_playbook.md` when the user gives only a rough idea, asks for a beautiful result, or needs page architecture/style choices.
- Run `scripts/create_brochure_scaffold.py` to bootstrap editable HTML/CSS source:

```bash
python scripts/create_brochure_scaffold.py output/pdf/beautiful-brochure-pdf/my-brochure --title "Brand Name"
```

Then replace placeholders with the real content and assets before exporting.

## Final Quality Gate

Do not call the brochure finished until:

- The latest PDF has been rendered to page images.
- Each page was visually checked for spacing, alignment, legibility, and asset quality.
- The final PDF, source HTML/CSS, local assets, and rendered previews are all in the project output folder.
