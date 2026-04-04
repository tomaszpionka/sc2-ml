---
paths:
  - "thesis/**/*"
---

# Thesis Writing Workflow

## Two-Pass Process (MANDATORY)

### Pass 1 — Claude Code (Category F session)
1. Read relevant phase entry in `reports/research_log.md`
2. Read report artifacts that feed the section
3. Read section description in `thesis/THESIS_STRUCTURE.md`
4. Draft in `thesis/chapters/XX_*.md`
5. Run Critical Review Checklist (below)
6. Plant `[REVIEW: ...]` flags for anything needing external validation
7. Update `thesis/WRITING_STATUS.md` → DRAFTED
8. Update `thesis/chapters/REVIEW_QUEUE.md` with Pending entry
9. Produce Chat Handoff Summary (format below)

### Pass 2 — Claude Chat (external validation)
User brings draft + artifacts to Claude Chat for literature validation,
citation checking, methodology alignment, and flag resolution.

## Critical Review Checklist (MUST complete before DRAFTED status)

1. **Numerical consistency:** Every number traces to a report artifact exactly
2. **Claim-evidence alignment:** Evidence supports the specific claim;
   hedge when suggestive ("consistent with..." not "demonstrates")
3. **Derivation traceability:** Every threshold has empirical or cited justification
4. **Statistical interpretation:** Effect sizes alongside p-values; non-significant
   ≠ "no effect"; note multiple comparison corrections
5. **Scope honesty:** Don't generalise beyond dataset; don't minimise limitations
6. **Missing context flags:** Insert `[REVIEW: ...]` for field-norm divergence

## Inline Flag Types
- `[REVIEW: <concern>]` — needs literature validation (Pass 2)
- `[UNVERIFIED: source?]` — number not traceable to artifact
- `[NEEDS JUSTIFICATION]` — threshold without derivation
- `[NEEDS CITATION]` — claim requires literature reference

## Writing Quality
- Third person or first person plural; academic register
- Present tense for established facts, past tense for actions taken
- Every figure/table has caption and number
- Citations: `[AuthorYear]` keys in `thesis/references.bib`
- Do NOT copy-paste from research_log.md — rewrite for thesis audience

## WRITING_STATUS.md Semantics
| Status | Meaning |
|--------|---------|
| SKELETON | Header exists, no prose |
| BLOCKED | Feeding phase incomplete |
| DRAFTABLE | Feeding phase complete, ready to write |
| DRAFTED | First draft exists, may need revision |
| REVISED | Updated after later-phase context |
| FINAL | Content-complete, reviewed, ready for typesetting |

## Chat Handoff Summary Format
```
## Chat Handoff Summary
### Section: §X.Y — [title] in thesis/chapters/XX_*.md
### Status: DRAFTED (first draft / revision)
### Flags: N [REVIEW], N [NEEDS CITATION], etc.
### Artifacts: [list with what each contains]
### Questions for Chat: [concrete questions]
### Numbers verified: [number] ← [artifact, line] ✓
```

## Phase-to-Section Mapping
After Phase 0 → §4.1.1 | After Phase 1 → §4.1.1 revision, §2.2 skeleton
After Phase 2 → §4.2.2 | After Phase 3 → §4.2 expansion
After Phase 4 → §4.3.2 | After Phase 5 → §4.3.1, §5.1 context
After Phase 6 → §4.2.3 | After Phase 7 → §4.3 completion
After Phase 8 → §4.4   | After Phase 9 → §5.1.1
After Phase 10 → §5.1.2–5.1.4, §6, §7
Cross-cutting: §1, §2, §3 — anytime
