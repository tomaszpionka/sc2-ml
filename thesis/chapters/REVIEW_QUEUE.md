# Thesis Review Queue — Pass 1 → Pass 2 Handoff

This file tracks thesis sections that Claude Code has drafted (Pass 1) and
that need external validation in Claude Chat (Pass 2).

## Workflow

1. Claude Code drafts a section and runs the Critical Review Checklist
   (see `.claude/thesis-writing.md`)
2. Claude Code plants `[REVIEW: ...]` and other inline flags
3. Claude Code appends an entry to the Pending table below
4. User brings the section + referenced artifacts to Claude Chat for Pass 2
5. After Pass 2 corrections are applied, move the entry to Completed

## Pending Pass 2 reviews

| Section | Chapter file | Drafted date | Flag count | Key artifacts | Pass 2 status |
|---------|-------------|-------------|------------|---------------|---------------|
| §1.1 Background and motivation | thesis/chapters/01_introduction.md | 2026-04-13 | 0 | — (literature section, no data artifacts) | Pending — Pass 2 blocking items resolved |

## Completed Pass 2 reviews

| Section | Reviewed date | Reviewer notes |
|---------|--------------|----------------|
| *(none yet)* | | |

## How to use this in Claude Chat

When bringing a section for Pass 2 review, provide Claude Chat with:
1. The section text from `thesis/chapters/XX_*.md`
2. The report artifacts listed in the "Key artifacts" column
3. The specific `[REVIEW: ...]` flags from the draft
4. Any `[NEEDS CITATION]` flags (Claude Chat will search the literature)

Claude Chat will return: resolved flags, suggested citations, methodology
alignment checks, and any corrections to statistical interpretation.
