# Roles and reusable prompts

[[00_START_HERE|Home]] · [[0_ADMIN/COLD_TRUTH_EXECUTION_PLAN_V2|Working plan]] · [[0_ADMIN/CONTENT_FORMAT_STANDARD|Format standard]]

Roles describe responsibilities. One agent may perform them in sequence; role names do not require separate agents or tasks.

| Order | Role | Reusable prompt | Handoff |
|---|---|---|---|
| 1 | [[0_ADMIN/ROLE_STRATEGIST|Strategist]] | [[0_ADMIN/PROMPTS/PROMPT_GENERATE_IDEAS|Candidate research]] | Verified ledger, risks, viability |
| 2 | [[0_ADMIN/ROLE_WRITER|Writer]] | [[0_ADMIN/PROMPTS/PROMPT_WRITE_SCRIPT|Draft]] | Full source-bound draft |
| 3 | [[0_ADMIN/ROLE_EDITOR|Editor]] | [[0_ADMIN/PROMPTS/PROMPT_EDIT_SCRIPT|Review]] | Reverse outline + full draft for paired human approval |
| 4 | [[0_ADMIN/ROLE_FILMER|Visual producer]] | [[0_ADMIN/PROMPTS/PROMPT_PLAN_VISUALS|Long-form visual plan]] | B-roll/case graphics after production prerequisites |
| 5 | [[0_ADMIN/ROLE_SHORTS_EDITOR|Shorts editor]] | [[0_ADMIN/PROMPTS/PROMPT_EXTRACT_SHORTS|Standalone Shorts]] | Separate scripts and Orbital-only visual track |
| 6 | [[0_ADMIN/ROLE_UPLOAD_MANAGER|Upload manager]] | [[0_ADMIN/PROMPTS/PROMPT_WRITE_METADATA|Metadata draft]] | Reviewable packaging; explicit publishing gate |

The local `skills/` directory contains corresponding execution instructions. Prompts are input templates, not approval records. Use the ledger as factual evidence even after the final script is approved.
