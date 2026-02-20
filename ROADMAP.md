# Seating Chart Generator — Roadmap

Ideas grouped by rough git branch scope. Sourced from personal brainstorming + user feedback (Feb 2026).

---

## `feature/curved-rows` ⏸ Tabled
- Curved rows toggle removed from UI — feature exists on the `feature/curved-rows` branch
- Known issues to fix before re-introducing:
  - Row labels way off in curved mode
  - Flipped version broken in curved mode
  - Everything shifts slightly left when curved is toggled
  - Closer seat spacing in curved rows

---

## `fix/layout-polish`
- Conductor label not centered with singers (row label throws it off)
- Seat number toggle should be from either edge (or both)
- Include empty chairs on edges option
- Never allow a section to be one person wide (validate/warn)
- Weird horizontal scrolling sometimes required — chart overflows viewport awkwardly

---

## `fix/stagger`
- Stagger toggle should be a proper stagger/grid switch, not just a CSS offset
- Bug: in "unstaggered" mode, a centered odd-count row next to a centered even-count row
  will still appear staggered due to centering math — needs grid alignment to fix properly

---

## `fix/export`
- Current export is just `window.print()` — not a real PDF, formatting is poor
- Needs a proper print stylesheet or server-side PDF generation

---

## `feature/navbar`
- Add a navigation bar as the app grows beyond a single flow

---

## `feature/sample-rosters`
- Ship sample roster CSVs with the app so new users can try it immediately
- Could include generic SATB, Men's Chorus (T1/T2/Bar/Bass), Women's Chorus, etc.

---

## `feature/ordering`
- Up/down ordering in addition to left/right voice part ordering

---

## `feature/undo-redo`
- Undo/redo for drag-and-drop and other edits

---

## `feature/animations`
- Animate flip
- Animate drag and drop
- Animate show-heights toggle

---

## `feature/roster-management`
- Handle singer withdrawal gracefully (adjust row without full rebuild)
- .xlsx input support (currently CSV only; real-world rosters come from Excel, formatted strangely)

---

## `feature/mixed-seating`
- Shuffle/mix mode: no same-voice-part neighbors
- Could be a toggle on the configure page

---

## `feature/piece-specific-roles`
- **The problem:** Some pieces assign singers to non-standard roles that cut across base voice parts
  - e.g. a piece might need 90 "refrain chorus," 15 "1st high" (drawn from T1), 20 "2nd middle" (drawn from B2), etc.
  - Roles change piece to piece within the same rehearsal
- **Feature idea:** Multi-role assignment mode
  - Define roles and counts per piece
  - Assign singers from base parts to roles
  - Generate seating that satisfies spatial role groupings
  - Possibly find one arrangement that works across multiple pieces

---

## `feature/sharing`
- Shareable link to send chart to students
- "Living document" link that updates in place (students can check the current version)
- PDF / print export

---

## `feature/persistence`
- Save and reload a chart from a previous rehearsal
- Accounts, or some account-lite alternative (magic links? local save?)
- Save roster separately from chart

---

## ~~`feature/hosting`~~ ✓ Done
- Live at https://choralchart.onrender.com (Render, free tier)

---

## Unresolved / needs more thought
- Piece-specific role assignment (see feature/piece-specific-roles above — needs design work before implementation)
- Complicated/combined ensemble arrangements (sometimes multiple choirs combined, director has unusual spatial requirements)
- What does "correct" seating mean when roles span base parts?
