# Documentation theme

The documentation site is styled with the Grepvine design system, which the
Grepvine team maintains. The files below are copies of its tokens, components
and assets.

This directory holds only what the pdoc build needs, so building the docs never
reads the design-system repository.

## Files

All files are in `templates/`, pdoc's template directory.

| File | Role |
| --- | --- |
| `tokens.css` | The design system's `tokens.css`: colour, type, spacing and shadow tokens for both themes. First in the cascade. |
| `components.css` | The design system's `components/bundle.css`: Logo, ThemeToggle, Markdown, Button and CodeBlock rules, and the Google Fonts import. Second in the cascade. |
| `favicon.svg` | The design system's `assets/Logos/grepvine-favicon.svg`. |
| `icon-sun.svg`, `icon-moon.svg` | The design system's ThemeToggle glyphs from `assets/Icons/`, inlined so they paint with `currentColor`. |
| `logo-mark.svg` | The inline mark from the design system's `components/Logo/preview.html`, painted from tokens. |
| `theme.css` | Maps pdoc's colour variables onto the tokens. |
| `custom.css` | Maps pdoc's classes onto the components; last in the cascade. |
| `syntax-highlighting.css` | The CodeBlock colours for Pygments output. |
| `frame.html.jinja2`, `module.html.jinja2` | pdoc template overrides: page frame, header with the Logo and ThemeToggle, and the guide landing page. |

## Changing the theme

- Follow the design system's rules rather than inventing new styles: its
  tokens for every colour, size and shadow, square corners, 2px rules, hard
  offset shadows, Tektur for headings and Martian Mono for everything else,
  lime as the one primary accent, and readable contrast in both themes.
- Keep `tokens.css`, `components.css` and the SVGs identical to the design
  system's files. To adopt a newer design system, copy those files again from
  the paths in the table above, then rebuild and check both themes.
- Put docs-specific rules in `theme.css` or `custom.css`, mapped onto the
  tokens, never as literal colours.
- Build with `uv run --frozen python scripts/build_docs.py` and check the
  pages in both themes at desktop and phone width.
