# Source

These files are an unmodified copy from the private repository
[`grepvine-ai/grepvine-design-system`](https://github.com/grepvine-ai/grepvine-design-system)
at commit `abe245372f136f057c6d080dc77f4ae90c7c8a4f`. The documentation build reads only this
copy and never checks out that repository.

| File | Used for |
| --- | --- |
| `tokens.css` | Colour, type, spacing and shadow tokens for both themes; first in the cascade. |
| `components/bundle.css` | Component rules (Logo, ThemeToggle, Markdown, Button, CodeBlock) and the Google Fonts import; second in the cascade. |
| `assets/Logos/grepvine-favicon.svg` | The browser-tab icon. |
| `assets/Logos/grepvine-mark.svg`, `assets/Logos/grepvine-mark-edged.svg` | Reference copies of the mark. Pages draw the inline version from `components/Logo/preview.html` so it follows the theme. |
| `assets/Icons/icon-sun.svg`, `assets/Icons/icon-moon.svg` | The theme toggle glyphs, inlined so they paint with `currentColor`. |
| `README.md`, `assets/Logos/README.md`, `assets/Icons/README.md`, `components/*/README.md`, `components/Logo/preview.html` | The rules and markup patterns the theme follows. |

`docs/theme/templates/logo-mark.svg` is the inline mark copied from
`components/Logo/preview.html`. The rest of the theme, under `docs/theme/templates`, is
written for pdoc and maps its classes onto these tokens and components.

## Refreshing

Copy the same paths from a newer commit, then update the commit above:

```sh
git clone https://github.com/grepvine-ai/grepvine-design-system /tmp/grepvine-design-system
git -C /tmp/grepvine-design-system checkout <commit>
cd /tmp/grepvine-design-system
for path in tokens.css components/bundle.css README.md \
    components/Logo/README.md components/Logo/preview.html components/ThemeToggle/README.md \
    components/Markdown/README.md components/CodeBlock/README.md components/Button/README.md \
    assets/Logos/README.md assets/Logos/grepvine-favicon.svg assets/Logos/grepvine-mark.svg \
    assets/Logos/grepvine-mark-edged.svg assets/Icons/README.md assets/Icons/icon-sun.svg \
    assets/Icons/icon-moon.svg; do
  install -D -m 644 "$path" "$OLDPWD/docs/theme/design-system/$path"
done
```

Run that from the SDK repository root (it sets `$OLDPWD` with the `cd`). If the mark changed,
copy its `<svg class="logo-mark">` element from `components/Logo/preview.html` into
`docs/theme/templates/logo-mark.svg`. Then rebuild with
`uv run --frozen python scripts/build_docs.py` and check both themes.
