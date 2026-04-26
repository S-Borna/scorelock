# Migrations Ledger

Source-of-truth for Alembic migration deployment status. Update rule: edits to this file live in the **same commit** as the migration that changes it.

Status values: YES / NO / UNKNOWN. UNKNOWN is valid — honesty over false certainty.

| revision | description | local-green | dev-green | prod-green | downgrade-tested | deployed_at | notes |
|---|---|---|---|---|---|---|---|
| 246c910cfb31 | initial schema (leagues, teams, users, fixtures, standings, odds, predictions, sentiment_scores, prediction_views) | YES | YES | UNKNOWN | NO | UNKNOWN | Pre-session. Some tables likely created via `Base.metadata.create_all()` startup fallback (now removed in `7b44d44`); alembic-stamped after the fact. |
| 1f5b8ca20887 | add articles table | YES | YES | UNKNOWN | NO | UNKNOWN | Pre-session. `articles` table exists locally but 0 rows. |
| 3a7c2e1f5d89 | add affiliate tables (`affiliate_links`, `affiliate_clicks`) + 4 SE bookmaker seed | YES | YES | UNKNOWN | NO | UNKNOWN | Pre-session. **Seed for 4 SE bookmakers did not run locally** — `affiliate_links` is 0 rows. Likely `create_all` race ate it. Re-seed action item. |
| 5b8d3a2f7e91 | add user_predictions table | YES | YES | UNKNOWN | NO | UNKNOWN | Pre-session. Per memory at session-start, last known prod head. Not re-verified this session. |
| b6a1f5d4c302 | v0.5c (formerly "v0.6a1") add reference data: sports, countries, seasons + seed | YES | YES | NO | YES | NEVER | Local-only. Seed produced 1 sport + 6 countries + 8 seasons. Downgrade tested clean. |
| c8e2b4a6d105 | v0.5b (formerly "v0.6a2") add provider identity: provider_payloads, provider_entity_mappings, provider_conflicts | YES | YES | NO | YES | NEVER | Local-only. `provider_entity_mappings` still empty — backfill from existing `api_football_id` columns deferred. Downgrade tested clean. |
| e4d7c2a8b510 | v0.5c add fixture_broadcasts + 10 SE broadcast seed | YES | YES | NO | YES | NEVER | Local-only. Allsvenskan seed branch produced 0 rows (no Allsvenskan fixtures locally). Downgrade tested clean. |
| f9c2e4a7b803 | v0.5c add players + fixture_events + Man City 2-1 Arsenal seed (fixture 328) | YES | YES | NO | YES | NEVER | Local-only. 26 players (City + Arsenal rosters) + 10 events (3 goals, 3 yellows, 4 subs). Downgrade tested clean. |

## Notes

- `local-green` and `dev-green` are equivalent here — same docker-compose stack.
- `prod-green` is **UNKNOWN** for all four pre-session migrations because Railway-prod state was not re-verified this session. Memory says prod was at `5b8d3a2f7e91` at session start; not a verified-this-session fact.
- `downgrade-tested` is **NO** for the four pre-session migrations — they have `downgrade()` functions but were not actively exercised in any session memory.
- `deployed_at` is **UNKNOWN** for everything pre-session because no deployment timestamp records exist.
- Spec-vocabulary note: the migration filenames carry retired vocab (`v0_6a1`, `v0_6a2`). Per `docs/QA_PROTOCOL.md § 5`, filenames stay as-is; the `description` column above maps them to canonical spec versions.
