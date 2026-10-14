# Button

A flat slab with a hard offset shadow and no ornament; the press is the whole interaction.

Four variants, and the ground decides which:

- **`.btn`** — `lime` fill, `black` label (16.6:1), `shadow-press` in `paper`. The primary
  action on `ink` or `ink-2`. One per view: it is "Start free trial" almost everywhere.
- **`.btn .btn-ghost`** — transparent, `paper` label, `muted` border and shadow. The
  secondary beside it, so `lime` stays the only lead.
- **`.btn .btn-ink`** — `black` fill, `white` label, `pink` shadow. The variant for a `lime`
  slab, where a lime button would vanish. Its focus ring switches to `black` for the same
  reason.
- **`.btn .btn-sm`** — 44px instead of 48px, 16px padding, a 3px shadow. The nav only.

**Motion:** at rest the shadow is 4px (3px small). Hover translates the button 2px and
shortens the shadow to 2px; active translates 4px and drops it entirely, so the button lands
flush where its shadow was. 150ms on the transform and shadow, 200ms on colour, all on
`cubic-bezier(0.2, 0, 0, 1)`.

**You provide:** the label, and an `<a>` or a `<button>` — the class styles either. A trailing
arrow goes in `<span class="arr" aria-hidden="true">&rarr;</span>`; it slides on hover and is
the only arrow the system uses inside a control.

**Rules:** labels are sentence case and never wrap (`white-space: nowrap`); minimum target is
48px, 44px for the small one; the label is `control` type (body face, 500). Never add a
radius, a gradient, a blurred shadow, an icon other than the arrow, or a third tier of
emphasis — if something needs less weight than ghost, it is a link.
