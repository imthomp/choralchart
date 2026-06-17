# ChoralChart — Roadmap

Effort and impact are rated Low / Med / High.
★ = came directly from assistant director feedback (Feb 2026).

---

## From the Assistant Director

| Branch | Idea | Effort | Impact |
|--------|------|--------|--------|
| ~~`fix/layout-polish`~~ | ~~Never allow a section to be one person wide (warn) ★~~ | ~~Low~~ | ~~High~~ |
| ~~`feature/ordering`~~ | ~~Up/down row ordering, not just left/right ★~~ | ~~Med~~ | ~~High~~ |
| ~~`feature/roster-management`~~ | ~~Singer withdrawal: adjust row without full rebuild ★~~ | ~~Med~~ | ~~High~~ |
| ~~`feature/roster-management`~~ | ~~.xlsx input support (real-world rosters from Excel) ★~~ | ~~Med~~ | ~~Med~~ |
| ~~`feature/mixed-seating`~~ | ~~Shuffle/mix mode: no same-voice-part neighbors ★~~ | ~~Med~~ | ~~Med~~ |
| ~~`feature/undo-redo`~~ | ~~Undo/redo for drag-and-drop and edits ★~~ | ~~High~~ | ~~High~~ |
| ~~`feature/sharing`~~ | ~~Shareable link to send chart to students ★~~ | ~~High~~ | ~~High~~ |
| ~~`feature/sharing`~~ | ~~"Living document" link that updates in place ★~~ | ~~High~~ | ~~High~~ |
| ~~`feature/persistence`~~ | ~~Save and reload charts across sessions ★~~ | ~~High~~ | ~~High~~ |
| ~~`feature/piece-specific-roles`~~ | ~~Piece-specific role assignment (cross-part roles) ★~~ | ~~High~~ | ~~Med~~ |

---

## High Impact

| Branch | Idea | Effort | Impact |
|--------|------|--------|--------|
| `feature/annotations` | Per-singer or per-section notes | Med | High |
| `feature/pdf-export` | PDF export — page margins, legend, header, fits one sheet | High | High |
| `feature/chart-diff` | Diff view — compare two `.choralchart` files, highlight changes | High | High |

---

## Medium Impact

| Branch | Idea | Effort | Impact |
|--------|------|--------|--------|
| `feature/fork-chart` | "Use as template" on read-only shared view — fork and customize | Low | Med |
| `feature/custom-colors` | Custom part colors — directors map voice parts to their own palette | Med | Med |
| `qa/mobile` | Touch/mobile pass — drag-and-drop on tablets, narrow layout for shared view | Med | Med |

---

## Small But Useful

| Branch | Idea | Effort | Impact |
|--------|------|--------|--------|
| `feature/headcount-bar` | Section headcount summary (e.g. S: 12 · A: 11 · T: 8 · B: 9) above the chart | Low | Med |
| `fix/dismissible-warnings` | Per-pair height warning dismissal — suppress intentional placements (soloists, etc.) | Med | Med |
| `fix/bulk-paste` | Narrow accepted height formats; inline validation instead of silent fallback | Low | Low |

---

## To Reconsider

| Area | Note |
|------|------|
| Undo/redo | Stack has no limit or persistence — clarify in UI that history is lost on tab close |
| Arrangement panel discoverability | Collapsed by default helps power users but new users won't find it — consider one-time hint |

---

## Other Ideas

| Branch | Idea | Effort | Impact |
|--------|------|--------|--------|
| ~~`feature/save-load`~~ | ~~Save chart to a file and reload it later (JSON export/import)~~ | ~~Low~~ | ~~High~~ |
| ~~`fix/layout-polish`~~ | ~~View full roster with scrolling on smaller windows~~ | ~~Low~~ | ~~Med~~ |
| ~~`fix/export`~~ | ~~Save full image snapshot from smaller windows (html2canvas clips on small viewports)~~ | ~~Low~~ | ~~Med~~ |
| ~~`fix/layout-polish`~~ | ~~Centeredness shifts when scrollbar appears/disappears~~ | ~~Low~~ | ~~Med~~ |
| ~~`fix/layout-polish`~~ | ~~Conductor label not centered (row label throws it off)~~ | ~~Low~~ | ~~Med~~ |
| ~~`feature/branding`~~ | ~~Add favicon~~ | ~~Low~~ | ~~Low~~ |
| `feature/branding` | Add logo | Low | Med |
| ~~`fix/layout-polish`~~ | ~~"Enter your roster" input styling matches other text boxes~~ | ~~Low~~ | ~~Low~~ |
| ~~`feature/sample-rosters`~~ | ~~Ship sample CSVs (SATB, Men's, Women's, etc.)~~ | ~~Low~~ | ~~Med~~ |
| ~~`fix/layout-polish`~~ | ~~Seat number toggle from either edge or both~~ | ~~Low~~ | ~~Low~~ |
| ~~`feature/height-warning`~~ | ~~Warn when a tall singer is placed in front of a shorter one~~ | ~~Low~~ | ~~High~~ |
| ~~`fix/stagger`~~ | ~~Stagger/grid switch (fix odd/even centering ghost-stagger)~~ | ~~Med~~ | ~~Med~~ |
| ~~`fix/layout-polish`~~ | ~~Include empty chairs on edges option~~ | ~~Med~~ | ~~Low~~ |
| ~~`feature/animations`~~ | ~~Animate flip, drag-and-drop, height toggle~~ | ~~Med~~ | ~~Low~~ |
| `qa/cross-platform` | Test on Windows, macOS, iOS, Android browsers | Med | High |

---

## Tabled

| Branch | Idea | Notes |
|--------|------|-------|
| `feature/curved-rows` | Curved rows | Removed from UI — code on branch, known visual bugs |
| `feature/piece-specific-roles` | Complicated/combined ensemble layouts | Needs design work before implementation |

---

## Done ✓

| Feature | Notes |
|---------|-------|
| Favicon | SVG grid icon matching app colors |
| Sample rosters | SATB (40), Men's (20), Women's (20) CSVs downloadable from upload form |
| Roster preview | Collapsible singer list on configure page to verify imports |
| Seat number toggle | Left edge / right edge / both edges picker in edit page |
| Ghost-stagger fix | Non-staggered rows now left-align within centered block; no centering drift |
| Empty chairs option | "Show empty chairs" toggle reveals placeholder dashed seats at row edges |
| Flip animation | Smooth scaleY flip when toggling chart direction |
| Swap flash | Brief brightness flash when two seats swap positions |
| Height fade | Height labels fade in/out instead of snapping |
| html2canvas small-viewport fix | windowWidth hint forces full render width regardless of viewport |
| .xlsx input | Upload real Excel rosters in addition to CSV |
| Undo/redo | Ctrl+Z / Ctrl+Y on the edit page; ↩ ↪ buttons |
| Shareable link | "Share link" button generates a public URL for the chart |
| Living document | Updating and re-sharing the same URL updates what viewers see |
| Chart persistence | Charts saved by ID in SQLite, reload across sessions via URL |
| Piece-specific arrangement | "Piece / Title" field on edit page; voice parts changeable per singer per chart |
| Single-wide section warning | Banner in edit page when any part occupies only 1 seat wide |
| 2D grid voice part arrangement | Drag parts into row groups (back/front) on configure page |
| Mixed/shuffle mode | No same-voice-part neighbors using greedy max-heap interleaving |
| JSON save/load (.choralchart) | Save and restore full chart state via file download/upload |
| Height warning | Orange highlight when front-row singer is taller than the row behind |
| Singer withdrawal | Remove button in modal compacts remaining seats |
| Scrollbar-gutter stable | Prevents layout shift when scrollbar appears |
| Conductor centering | Conductor label properly centered under the choir |
| pytest test suite | 71 tests covering algorithm and Flask routes |
| Hosting | Live at https://choralchart.onrender.com (Render, free tier) |
| Navbar | Sticky ChoralChart navbar on every page |
| Footer | Shared footer with copyright and GitHub link |
| README | Setup instructions, CSV format, tech stack |
| Manual roster entry | Paste-by-part textarea entry with optional height parsing (`Name, 5'10"`) |
| Optional heights | Singer height is optional; unknown heights sort to the middle of their group |
| Random roster polish | ±5 variation per section, diverse names, unknown parts get random gender |
| Unified `/configure` route | Both entry methods post to the same URL |
| PNG export | Replaced `window.print()` with html2canvas PNG download (full chart, not just visible area) |
| Dual scrollbar fix | Chart scrolls within panel, no body-level horizontal scroll |
| Edit page URL | Configure now posts directly to `/edit` (was `/preview`) |
| ✕ button fix | Remove-section button width and height corrected on roster entry page |
| ~~PDF export~~ | ~~Replaced by PNG export~~ |
| ~~Navbar feature~~ | ~~Done~~ |
