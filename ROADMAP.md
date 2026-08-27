# ChoralChart — Roadmap

Effort and impact are rated Low / Med / High.
★ = came directly from assistant director feedback (Feb 2026).
▲ = BYU client requirement (Sep 1, 2026 deadline).

---

## Sep 1 Sprint — High Priority

These are high-leverage features to build before the BYU semester starts.

| Branch | Feature | Effort | Why |
|--------|---------|--------|-----|
| `feature/find-by-name` | **Find singer by name** — search box that highlights their seat ▲ | Low | Essential for large choirs; director needs to locate people fast during rehearsal |
| `feature/absent-mode` | **Mark absent** — grey out a seat without removing the singer; they keep their position ▲ | Low | Day 1 of class someone won't show up; removing loses their seat permanently |
| `feature/part-highlight` | **Highlight by voice part** — click a legend item to dim all other parts ▲ | Low | Directing people to seats in a live rehearsal; "tenors, look at your highlighted seats" |
| `feature/seat-lock` | **Lock a seat** — pin a singer so they don't move when reshuffling ▲ | Low | Section leaders and soloists must stay anchored across arrangement changes |
| `feature/share-password` | **Password-protect share links** — director sets a password; viewers must enter it ▲ | Low | FERPA: names on a public URL without access control is non-compliant |
| `feature/data-deletion` | **Delete a shared chart** — remove it by ID so names come off the server ▲ | Low | FERPA: directors need a way to remove student data they no longer need |
| `qa/cross-platform` | **Cross-platform QA** — Windows, macOS, iOS Safari, Android Chrome; drag-and-drop on iPad ▲ | Med | BYU students will use every platform; touch drag must work reliably |

---

## Sep 1 Sprint — Useful but Lower Urgency

| Branch | Feature | Effort | Notes |
|--------|---------|--------|-------|
| `feature/student-view` | **Student "where do I sit" view** — read-only share page with name search, returns row + seat number | Low | Cleaner than sending the full editable chart; avoids sharing the whole roster |
| `feature/autosave` | **Autosave to localStorage** — crash recovery prompt on next load | Med | Tab closes unexpectedly = all work lost; this is a silent safety net |
| `feature/annotations` | **Notes per singer** — small text field in the edit modal ("new student", "solo upcoming") | Low | Singer-specific context without cluttering the chart |
| `feature/pdf-export` | **PDF export** — page margins, title, legend, fits one sheet | High | PNG works for most cases but PDF is easier to print at scale |
| `feature/url-share` | **URL-encoded share** — compress chart into URL param, no server storage ▲ | Med | Eliminates server-side name storage entirely; full FERPA resolution |
| `feature/byu-roster-import` | **BYU roster import** — import from their actual roster format (confirm format with dept) ▲ | Med | Directors shouldn't be re-entering names they already have in a university system |

---

## Post-September

| Branch | Feature | Effort | Notes |
|--------|---------|--------|-------|
| `feature/venue-templates` | BYU venue layout templates — HFAC concert hall, rehearsal room, etc. ▲ | High | Correct row shapes and counts pre-built; director picks the hall |
| `feature/ensemble-label` | Ensemble name / semester label on the chart | Low | "BYU Singers — Fall 2026" as a subtitle below the title |
| `feature/height-suggest` | "Fix height warnings" button — auto-swaps flagged pairs to resolve violations | Med | Currently the director has to identify and fix manually |
| `feature/keyboard-nav` | Full keyboard navigation — Tab through seats, Enter to select/swap | Med | Accessibility; also faster for directors who prefer keyboard |
| `feature/qr-code` | QR code on chart — links to live share; print it at the bottom | Low | Students scan from the printed chart instead of typing a URL |
| `feature/local-chart-list` | localStorage "your charts" list on home page — no login required | Low | Directors return to recent charts without bookmarking share links |
| `feature/preserve-edits` | Re-applying an arrangement preserves manual seat swaps | High | Currently reshuffling discards all manual adjustments |
| `feature/snapshots` | Named chart snapshots — "save as December concert" | Med | Multiple pieces per semester need separate charts without re-entering rosters |
| `feature/ferpa-mode` | "Seats only" share — positions visible, names hidden from shared view | Med | Alternative to password-protect for public concert programs |
| `feature/roster-merge` | Merge two rosters — combined ensemble import | Med | Mass choir or combined ensemble scenario |
| `feature/fork-chart` | "Use as template" — fork a shared chart to customize for a different piece | Low | Reuse layout between similar-sized choirs or semesters |
| `feature/print-css` | CSS `@print` stylesheet — clean browser print without PNG export | Low | Fallback for directors without time to export |

---

## Known Bugs

| Branch | Bug | Effort |
|--------|-----|--------|
| ~~`fix/aisle-persist`~~ | ~~Aisle position not saved to SQLite or `.choralchart`~~ | ✓ already working |
| ~~`fix/export-completeness`~~ | ~~PNG export captures only the seat grid~~ | ✓ legend/conductor always in panel; title fixed |
| ~~`fix/part-rename`~~ | ~~Changing a singer's voice part to one outside `part_order` orphans them~~ | ✓ modal is a select — can't pick outside part_order |
| `fix/concurrent-edit` | Concurrent "Update" on the same share link silently overwrites — last write wins, no warning | Low |
| `fix/height-warning-mode` | Height warning fires if taller than *any* person behind (`.some()`); should require *all* people behind to be shorter? Needs director input | Low |

---

## FERPA / Privacy Summary

The tool currently stores student names on Fly.io with public share links and no access control. Priority order for compliance:

1. `feature/share-password` — password-protect links (low effort, immediate improvement)
2. `feature/data-deletion` — directors can remove stored charts
3. `feature/url-share` — eliminate server-side name storage entirely
4. `feature/ferpa-mode` — names-only-for-director option
5. `feature/byu-sso` — BYU CAS/SSO gate (right answer long-term, overkill before accounts exist)

---

## Accounts — Phased Approach

Don't add accounts until localStorage soft-identity is in place. Zero-friction onboarding is a competitive advantage — don't gate it early.

| Phase | Branch | What | Effort |
|-------|--------|------|--------|
| 1 | `feature/local-chart-list` | localStorage "your charts" — no login required | Low |
| 2 | `feature/ensembles` | Ensemble grouping — when soft identity stops being enough | High |
| 3 | `feature/accounts` | Google OAuth only, no passwords. Migrate localStorage on first sign-in | High |

---

## From the Assistant Director ★

All done.

| Feature | Status |
|---------|--------|
| Never allow a section to be one person wide (warn) | ✓ |
| Up/down row ordering, not just left/right | ✓ |
| Singer withdrawal: adjust row without full rebuild | ✓ |
| .xlsx input support | ✓ |
| Shuffle/mix mode: no same-voice-part neighbors | ✓ |
| Undo/redo for drag-and-drop and edits | ✓ |
| Shareable link to send chart to students | ✓ |
| "Living document" link that updates in place | ✓ |
| Save and reload charts across sessions | ✓ |
| Piece-specific role assignment (cross-part roles) | ✓ |

---

## To Reconsider

| Area | Note |
|------|------|
| Undo/redo | Stack has no limit or persistence — history is lost on tab close |
| Arrangement panel discoverability | Collapsed by default; new users may not find it — consider a one-time hint |
| Share link server dependency | All links break if Fly.io goes down — `feature/url-share` is the durable fallback |
| Height warning sensitivity | `.some()` vs `.every()` — get director input before changing; intentional placements exist |

---

## Tabled

| Branch | Idea | Notes |
|--------|------|-------|
| `feature/curved-rows` | Curved rows | Code on branch, known visual bugs — removed from UI |
| `feature/byu-sso` | BYU CAS/SSO login | Right answer long-term but overkill before ensembles exist |
| `feature/multi-chart` | Side-by-side chart comparison | Complex for limited benefit vs snapshots |
| `feature/chart-diff` | Diff two `.choralchart` files | Niche; snapshots + visual comparison handles most cases |

---

## Done ✓

| Feature | Notes |
|---------|-------|
| Uniform row widths | Side-by-side now fills all rows evenly (Bresenham) — 40 SATB → 4×10, not 2×12+2×8 |
| Chart title persistence | Title survives Apply arrangement and page reloads |
| 102 pytest tests | Algorithm, routes, encode/decode, stagger offsets, random roster, variable row sizes, share flow |
| Pointer Events drag/drop | Mouse + touch/iPad; float clone follows pointer; double-tap opens modal |
| Favicon | SVG grid icon matching app colors |
| Sample rosters | SATB (40), Men's (20), Women's (20) |
| Roster preview | Collapsible singer list on configure page |
| Seat number toggle | Left edge / right edge / both edges |
| Ghost-stagger fix | Non-staggered rows left-align within centered block |
| Empty chairs option | Dashed placeholder seats at row edges |
| Flip animation | Smooth scaleY flip when toggling chart direction |
| Swap flash | Brief brightness flash on seat swap |
| Height fade | Height labels fade in/out |
| html2canvas full-width fix | windowWidth hint forces full render |
| .xlsx input | Upload Excel rosters in addition to CSV |
| Undo/redo | Ctrl+Z / Ctrl+Y; ↩ ↪ buttons |
| Shareable link | "Share link" generates a public URL |
| Living document | Re-sharing the same URL updates what viewers see |
| Chart persistence | Charts saved by ID in SQLite |
| Piece/Title field | Per-chart title |
| Single-wide section warning | Banner when any part is only 1 seat wide |
| 2D grid voice part arrangement | Drag parts into row groups |
| Mixed/shuffle mode | No same-voice-part neighbors |
| JSON save/load (.choralchart) | Save and restore full chart state |
| Height warning | Orange highlight when front-row singer is taller than row behind |
| Singer withdrawal | Remove button in modal compacts seats |
| Scrollbar-gutter stable | Prevents layout shift when scrollbar appears |
| Conductor centering | Properly centered under the choir |
| Hosting | Fly.io — auto-deploys on push to main via GitHub Actions |
| Navbar / Footer | Shared across all pages |
| README | Setup, CSV format, tech stack |
| Manual roster entry | Paste-by-part with optional height parsing (`Name, 5'10"`) |
| Optional heights | Unknown heights sort to middle of group |
| Random roster | ±5 variation per section, diverse names |
| PNG export | html2canvas — full chart width, title, legend, conductor |
| Dark mode | Full dark/light theme with toggle |
