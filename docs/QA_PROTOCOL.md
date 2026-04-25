# QA Protocol — ScoreLock

Hard QA gate active for schema + provider work through v0.6. This file is the contract. The gate cannot be bypassed by interpretation, urgency, scope-blur, or "QA appears unresponsive".

## 1. Scope

| Work area | Gate |
|---|---|
| Schema (models, migrations, enum widening, FK additions, JSONB columns) | HARD |
| Provider abstraction code under `backend/app/providers/` | HARD |
| `backend/app/services/{api_football,football_data,odds_api}.py` edits | HARD |
| `backend/app/services/tasks.py` rewiring | HARD |
| Anything wired via the provider registry | HARD |
| Read-only API endpoints (no schema change) | SOFT post-v0.6 |
| Frontend components, copy, styling, i18n keys | SOFT post-v0.6 |
| Bug fixes that touch zero schema/provider files | SOFT post-v0.6 |
| Documentation outside `docs/PROVIDER_ABSTRACTION_*` and `docs/METADATA_SCHEMA_*` | SOFT |

**Default at any ambiguity: HARD.** All gates remain HARD until v0.6 is closed — defined as: v0.5c metadata tables fully landed + v0.5d provider integration complete + v0.6 endpoints serving real provider data.

## 2. Pre-push checklist

Each item is mandatory. None are best-effort. A failed item blocks push.

1. **One thing per commit.** Migration OR endpoint OR UI — never combined.
2. **No endpoint/UI against an incomplete schema phase.** Schemas land as a complete group first; consumption code lands after.
3. **`docs/MIGRATIONS_LEDGER.md` updated** in the same commit as any migration that adds/removes/changes tables.
4. **Non-negotiables actively verified.** "Risk noted" does not count. Each of the 6 in `docs/PROVIDER_ABSTRACTION_V0.4.md § Non-Negotiables` checked with a command and quoted output in the sync report.
5. **Open architectural question = no code on the dependent stack.** The question is resolved (Said gives an explicit answer) before any line of code that depends on it.
6. **Scope-creep check.** Files outside the declared scope of the task = back out or split into a separate commit. No exceptions for "while I was there".

## 3. Sync report format (per hard-gate task, before push request)

```
## 0. VOKABULÄR-CHECK
Spec-namn (v0.5a/b/c/d/e → v0.6) följs konsekvent? YES / NO + diff list.

## 1. PHASE STATE
- Current phase per docs/PROVIDER_ABSTRACTION_V0.4.md § Migration Strategy
- DoD bullets cited verbatim
- % complete + one-sentence reason

## 2. WHAT IS LANDED
Per commit since last sync: hash | one-line | files (short) | spec section

## 3. UNCOMMITTED / HALF-DONE
- git status --short
- git stash list
- Files started but not added
- Things considered but not typed

## 4. SCHEMA / DB STATE
- alembic current + alembic heads
- Per migration since last sync: local-green | dev-green | prod-green | downgrade-tested
- Dev↔prod drift list

## 5. NON-NEGOTIABLE COMPLIANCE
6 rows from § Non-Negotiables → COMPLIANT / VIOLATED / NOT-YET-APPLICABLE
Verification command + quoted output for each non-trivial item.

## 6. TESTS + LINT
- make test → X/Y
- make lint → PASS/FAIL
- Skipped/xfailed tests flagged

## 7. OPEN QUESTIONS
Architectural or schema-affecting only. Cosmetic excluded.

## 8. NEXT MOVE
Single sentence: what the next commit would be.
```

## 4. Migrations ledger

`docs/MIGRATIONS_LEDGER.md` is the source-of-truth for migration deployment status. Update rule: edits to the ledger live in the **same commit** as the migration that changes it. Not separately, not after, not before. UNKNOWN is a valid status — honesty over false certainty.

## 5. Vocabulary

| Canonical (use in new files + chat) | Retired (do not use in new work) |
|---|---|
| v0.5a, v0.5b, v0.5c, v0.5d, v0.5e, v0.6 | "Phase 1/2/.../12" from build plan |
| Migration revision IDs (12-char hex) | "v0.6a1", "v0.6a2", "v0.6a3", "Phase X migration" |

Existing filenames containing retired vocab (e.g. `b6a1f5d4c302_v0_6a1_add_reference_data.py`) stay as-is — history is not rewritten. **New files and all communication** use canonical vocab.

## 6. Escalation

- A QA flag = full stop on the affected work item until explicit OK from Said in chat.
- Two valid forms of OK: (a) Said says "OK", (b) Said says "kör".
- "QA appears unresponsive", "Said is offline", "minor change", "obvious win" are **not** bypass triggers. Wait.
- Disagreement with a flag is permitted; the disagreement is raised as a chat question, not as a unilateral action.

## 7. Soft gate (post-v0.6)

When the gate is soft for the work item:
- Push without pre-approval is permitted.
- Sync report is still required, post-hoc, before the next task starts.
- Post-hoc review can still trigger a revert request. Soft gate ≠ no review.
