# Claude Code → Claude Chat Handoff Protocol

This file tells Claude Code what to prepare when a session produces work
that needs Claude Chat review (Pass 2 of the thesis writing workflow).

---

## When to prepare a handoff

After any Category F (thesis writing) session where:
- A section was drafted or revised
- `[REVIEW: ...]` flags were planted
- Statistical interpretations were made that need literature validation
- Methodological choices were made that might diverge from field norms

## What Claude Code must produce at end of session

At the end of any session that triggers a handoff, Claude Code appends a
structured summary block to the session output. This block is what the user
copy-pastes into Claude Chat. Format:

```
## Chat Handoff Summary

### Section drafted
- File: `thesis/chapters/XX_*.md`
- Section: §X.Y.Z — [title]
- Status: DRAFTED (first draft / revision)

### Inline flags planted
1. `[REVIEW: ...]` — [line number or context] — [what needs checking]
2. `[NEEDS CITATION]` — [line number or context] — [what claim needs a source]
3. `[NEEDS JUSTIFICATION]` — [line number or context] — [what threshold/parameter]
4. `[UNVERIFIED: source?]` — [line number or context] — [what number is untraceable]

### Report artifacts referenced
- `src/rts_predict/sc2/reports/XX_artifact.md` — [what data it contains]
- `src/rts_predict/sc2/reports/XX_artifact.csv` — [what data it contains]

### Specific questions for Claude Chat
1. [Concrete question about methodology, interpretation, or literature]
2. [Another concrete question]

### Numbers verified against artifacts (Pass 1 checklist item 1)
- [number] ← [artifact file, line/key] ✓
- [number] ← [artifact file, line/key] ✓
```

## What Claude Code must NOT do

- Do not attempt to resolve `[REVIEW: ...]` flags — these require literature access
- Do not invent citations — plant `[NEEDS CITATION]` and let Claude Chat find them
- Do not guess whether a methodology is standard — flag it for review
- Do not produce thesis text that claims alignment with "common practice" unless
  the practice is documented in the project's own scientific invariants

## REVIEW_QUEUE.md update

After producing the handoff summary, Claude Code must also update
`thesis/chapters/REVIEW_QUEUE.md` with a new row in the Pending table.
