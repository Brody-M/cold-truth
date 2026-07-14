# CHANNEL_SYSTEM — LEGACY OPERATING NOTE

> [!CAUTION]
> **Superseded for active work.** This note is preserved as historical channel-planning context. Its legacy runtime, word-count, Shorts-reuse, batch-production, direct voice-generation, visual, upload, and scheduling instructions must not be used as execution authority.
>
> Active work is controlled by [[../0_ADMIN/CONTENT_FORMAT_STANDARD|Content Format Standard]], [[../0_ADMIN/COLD_TRUTH_MASTER_EXECUTION_PLAN|Cold Truth Master Execution Plan]], [[WORKFLOW_PER_VIDEO|Workflow Per Video]], `AGENTS.md`, and the relevant current role instructions. In particular: long-form targets 8–10 minutes with a `480.000`-second measured-audio floor; scripts normally draft at 1,150–1,450 words; every Short has a standalone source-backed script and separately measured narration; long-form and Shorts visual assets never overlap; reverse outline and full draft require paired human approval before `Script_Final.md`; and every narration, media, render, upload, schedule, or publish action requires its own explicit gate.
>
> The “Active Production,” tool-status, weekly-batch, script-template, and upload sections below are not current state. Consult [[../0_ADMIN/COLD_TRUTH_EXECUTION_STATE.json|Cold Truth Execution State]] for current status. No account, provider, production, or publishing permission is conveyed by this file.

## System Links

**Vault map:** [[VAULT_INDEX]] · **Full workflow:** [[WORKFLOW_PER_VIDEO]] · **Channel goals:** [[GOALS]] · **API Keys:** [[API_KEYS]]

**Roles:** [[ROLE_STRATEGIST]] · [[ROLE_WRITER]] · [[ROLE_EDITOR]] · [[ROLE_FILMER]] · [[ROLE_UPLOAD_MANAGER]] · [[ROLE_SHORTS_EDITOR]]

**Prompts:** [[PROMPT_GENERATE_IDEAS]] · [[PROMPT_WRITE_SCRIPT]] · [[PROMPT_EDIT_SCRIPT]] · [[PROMPT_PLAN_VISUALS]] · [[PROMPT_WRITE_METADATA]] · [[PROMPT_EXTRACT_SHORTS]]

**Active Production:** [[Asha_Degree_Script_v1]] · [[Asha_Degree_Shot_List]]

---

## Channel Identity

| Field | Value |
|---|---|
| Channel name | Cold Truth |
| Handle | @ColdTruth |
| Niche | True crime — lesser-known cases, mysteries, unsolved |
| Audience | Moms and women 25–45, background listeners |
| Tone | Calm, narrative, trustworthy. Not sensational. Not clickbait. |
| Format | Faceless narration, AI voiceover, stock footage, clean editing |

---

## Content Rules (Never Break These)

1. **No recycled mega-cases.** Avoid Dahmer, Ted Bundy, Making a Murderer. The whole angle is lesser-known.
2. **Calm tone, always.** No screaming thumbnails. No "YOU WON'T BELIEVE THIS." The audience listens while doing dishes — don't startle them.
3. **Background-friendly pacing.** The story should work even if someone isn't watching. Strong narration carries the video.
4. **One case per video.** Don't cram two stories in. Give each case room to breathe.
5. **Always end with resolution or context.** Even if a case is unsolved, tell the audience where it stands now.

---

## Shorts Strategy

### How Shorts Fit Cold Truth

Shorts serve one purpose: discovery. Long-form videos build watch hours and ad revenue. Shorts put Cold Truth in front of people who haven't found it yet and funnel them to the full episode. They are not a separate channel — they are a top-of-funnel for the main content.

Target output: 3–5 shorts per week. These are produced alongside long-form, not instead of it. The batch system handles this — after every long-form video, you extract shorts from the same material.

### Two Types of Cold Truth Shorts

**Type 1 — Cut-downs (preferred)**
Take a moment from a finished long-form video and build a standalone short around it. No new research. No new script writing. You already have the voiceover — you clip it, add context text, and post it.

Best moments to cut: the hook, a shocking twist, the unresolved ending, a detail that makes no sense until you hear the full story.

**Type 2 — Standalone teasers**
A short written from scratch about a case you haven't covered yet — or may never cover in long-form. One chilling detail. One unresolved question. One reason to be curious. No resolution. The short IS the hook.

Use standalone teasers sparingly. They take more production time and don't recycle existing work. Save them for cases with a single killer detail that's impossible to ignore.

### What Makes a Good Cold Truth Short

- **First 3 seconds decide everything.** Open on the most disturbing or unresolved detail — not the setup.
- **No resolution.** The short raises a question it doesn't answer. The long-form video (or curiosity) is the answer.
- **Background-listener friendly audio, but visual-first format.** Shorts are watched on phones, often with sound. Text overlays on every key fact are non-negotiable.
- **One idea only.** One case, one detail, one question. Do not try to summarize a full story in 60 seconds.
- **End with a hook line, not a CTA.** Avoid "like and subscribe." Instead: "The full story is on the channel." Or just let it end on the unresolved question.

### Shorts vs. Long-Form Balance

| | Long-form | Shorts |
|---|---|---|
| Frequency | 1–2 per week | 3–5 per week |
| Source | Original production | Cut from long-form OR standalone |
| Time to produce | Full workflow (3 days) | 30–60 min per short after long-form is done |
| Primary goal | Watch hours, ad revenue, subscribers | Discovery, reach, funnel to long-form |
| Script length | 1,500–2,000 words | Under 150 words |
| Video length | 10–15 min | Under 60 seconds |

### Burnout Prevention Rules

1. **Never produce shorts before the long-form video is done.** Long-form is the priority. Shorts are extracted from finished work, not built in parallel.
2. **Batch shorts on the same day as packaging** (Phase 8.5 of the workflow). The material is fresh, the files are open. Don't come back to it later.
3. **3 shorts per long-form video is the target.** 5 is the ceiling. If a video only has 2 good moments, post 2. Don't force bad shorts.
4. **Standalone teasers are optional.** Only write them when a case idea is too good not to tease and you're not planning a full episode anytime soon.

### Shorts Format Specs

- Aspect ratio: 9:16 (vertical)
- Resolution: 1080×1920
- Length: 45–58 seconds (YouTube counts anything under 60 — stay under to be safe)
- Captions: burn in text overlays for every key fact (name, date, location)
- Music: optional, low volume, same royalty-free sources as long-form
- No end screen (Shorts don't support them)
- Title: under 40 characters, written as a hook not a label
---
## Tool Stack

| Tool | Purpose | Status |
|---|---|---|
| Claude Pro | Research, scripting, ideation, system thinking | Active |
| Obsidian | Script writing, idea vault, case notes | Active |
| ElevenLabs | AI voiceover generation | Get this next |
| DaVinci Resolve | Video editing (free version) | Install and learn |
| YouTube Studio | Publishing, scheduling, analytics | Active (Cold Truth) |
| Canva or Photopea | Thumbnail creation | Optional, free |

**Monthly budget:** $20–75. ElevenLabs Creator plan ($22/mo) covers this well.

---

## Weekly Batch Workflow

The system runs on 3 production days per week, roughly 10–12 hours total. No daily grinding.

### Day 1 — Research & Script (4–5 hours)
1. Pull 2–3 case ideas from the Obsidian idea vault
2. Research the best one using Claude + web sources
3. Build the full script using the script template
4. Review and refine in Obsidian — read it aloud mentally, check pacing
5. Save final script as `[CASE NAME] - Script FINAL.md`

### Day 2 — Voice & Edit (4–5 hours)
1. Paste script into ElevenLabs, generate voiceover
2. Listen through full audio — catch mispronunciations, re-generate sections if needed
3. Import audio into DaVinci Resolve
4. Layer stock footage (Pexels, Pixabay, Storyblocks if budget allows)
5. Add lower thirds, text overlays for names/dates where needed
6. Export at 1080p, 30fps

### Day 3 — Package & Schedule (1–2 hours)
1. Create thumbnail (Canva or Photopea — simple, dark, readable text)
2. Write YouTube title (see Title Formula below)
3. Write description (see Description Template below)
4. Add tags (see Tag Bank)
5. Schedule upload in YouTube Studio (aim for Tuesday or Thursday, 10am–12pm ET)

---

## Script Template

Use this structure for every video. Total length: 1,200–1,800 words for a 10–15 minute video.

```
[HOOK — 30–60 seconds]
Open with the most compelling detail of the case. Not the beginning — the moment that makes someone stop and listen.
Example: "In [year], [name] vanished from [town]. The police closed the case in [X days]. But there was one detail they never explained."

[CASE INTRO — 1–2 minutes]
Who was the victim? Where did they live? What was their life like?
Keep it human. Make the audience care before the crime happens.

[THE INCIDENT — 2–3 minutes]
What happened? Walk through the timeline clearly.
One event at a time. Don't jump around.

[THE INVESTIGATION — 2–3 minutes]
What did police find? What went wrong? Were there suspects?
This is where friction lives — missed clues, wrong turns, cold leads.

[TWISTS OR TURNING POINTS — 1–2 minutes]
What changed? New evidence, a tip, a confession, a suspect cleared?
Not every case has this section — skip if it doesn't fit.

[RESOLUTION OR CURRENT STATUS — 1–2 minutes]
What is the outcome? Solved? Convicted? Unsolved?
If unsolved: what do investigators believe now? Is anyone still looking?

[CLOSING CTA — 30 seconds]
Invite them to stay. Don't beg for likes — make it feel natural.
Example: "If you know this case or want to hear more like it, let me know in the comments. I'll see you next time."
```

---

## Title Formula

Test these formats. Pick the one that fits the case best.

- `The [Town/State] [Crime Type] Nobody Talked About`
- `She Disappeared in [Year]. No One Was Ever Charged.`
- `The [Case Nickname] Case: What Really Happened`
- `A [Crime] That Should Have Been Solved 20 Years Ago`
- `They Found [evidence]. The Killer Was Never Found.`

**Rules:**
- Under 60 characters if possible
- No ALL CAPS
- No question marks as clickbait (avoid "Did they find the killer??")
- The title should match what the video actually delivers

---

## Description Template

```
[1–2 sentence summary of the case — what happened, where, when]

In this episode of Cold Truth, we cover [case name] — [brief hook sentence].

[3–4 sentences expanding on the story — what makes it unusual, what went wrong, what the outcome was]

---
Subscribe for new episodes every week.
Lesser-known cases. Real stories. Cold Truth.

[Affiliate links if applicable]
[Relevant links: case sources, news articles — do not link to graphic content]

---
#TrueCrime #ColdCase #TrueCrimeNarration #Mystery #Unsolved #ColdTruth
```

---

## Tag Bank (Rotate and Mix)

Core tags (use every video):
`true crime, cold case, unsolved mystery, true crime narration, cold truth`

Case-specific tags (add per video):
`[state] true crime, [decade] cold case, missing persons, murder mystery, real crime stories`

Audience tags:
`true crime podcast, background true crime, true crime for women, calm true crime`

---

## Idea Vault System (Obsidian)

Folder structure:
```
Cold Truth/
├── Ideas/
│   ├── Backlog.md          ← running list of all case ideas
│   ├── [Case Name].md      ← one file per case being researched
├── Scripts/
│   ├── [Case Name] - Script FINAL.md
├── Published/
│   ├── [Case Name] - Published [DATE].md
└── System/
    ├── CHANNEL_SYSTEM.md
    ├── GOALS.md
```

When adding a case idea to the backlog, include:
- Case name
- Location + year
- Why it fits Cold Truth (lesser-known, good story, clear arc)
- Source link if you have one

---

## Quality Checklist (Before Every Upload)

- [ ] Script follows the template structure
- [ ] Voiceover sounds natural — no weird pauses or mispronounced names
- [ ] Footage matches the story (don't use generic city footage for a rural case)
- [ ] No copyrighted music — use royalty-free only (YouTube Audio Library, Epidemic Sound free tier)
- [ ] Title under 60 characters, no clickbait
- [ ] Description filled in with tags
- [ ] Thumbnail is readable at small size
- [ ] Video is scheduled, not set to public immediately (give it time to process)

---

## Metrics to Track (Monthly Review)

Pull these from YouTube Studio once a month:

| Metric | What It Tells You |
|---|---|
| Average view duration | Are people staying? Is the hook working? |
| Click-through rate (CTR) | Are thumbnails + titles compelling? |
| Top performing video | What case type/format is resonating? |
| Subscriber source | Where are new subscribers coming from? |
| Watch hours total | Progress toward monetization threshold |

**Monthly review question:** What's working? Do more of that.

---

## When the System Feels Broken

If you're stuck, come back to this:

1. You don't need a perfect video. You need a published video.
2. One script at a time. One case at a time.
3. Overthinking is the enemy. The batch system exists to remove decisions.
4. Post the video. Improve the next one.
