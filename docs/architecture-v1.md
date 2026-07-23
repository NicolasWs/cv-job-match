# CV & Cover Letter Tool — Architecture v1

Multi-agent system to support Nicolas Wajs's search for Product Manager / Product
Owner roles in AI/Data, plus interview prep.

Status: **v1 — awaiting user feedback before refinement.**

---

## 1. Agent Architecture

Seven components. One orchestrator + six specialists. Data flows through a shared
`structured_profile` object produced once and reused everywhere.

```
                         ┌──────────────────────────┐
                         │   ORCHESTRATOR (main)     │
                         │  routes + assembles output│
                         └────────────┬─────────────┘
        ┌──────────────┬──────────────┼──────────────┬───────────────┐
        ▼              ▼              ▼              ▼               ▼
 CV_ANALYZER     JOB_MATCH       WRITING       NARRATIVE_COACH   INTERVIEW_QA
        │              │              │              │               │
        └──────────────┴──────────────┴──────────────┴───────────────┘
                         ▼                              ▼
                   LEARNING_PLAN               JOB_TRACKER_DESIGN
```

| # | Agent | Role | Key inputs | Key outputs |
|---|-------|------|-----------|-------------|
| 0 | ORCHESTRATOR | Route a request to the right agents, in order; merge results | user request, job posting | assembled deliverable |
| A | CV_ANALYZER | Parse CV → structured profile; suggest edits vs a JD | raw_cv_text, job_description_text | structured_profile, relevance_map, cv_edit_suggestions |
| B | JOB_MATCH | Score fit, find gaps, recommend positioning | structured_profile, job_description_text | match_score, gap_analysis, recommended_positioning |
| C | WRITING | Draft cover letter, recruiter email, LinkedIn message | structured_profile, JD, tone + narrative guidelines | cover_letter_draft, recruiter_email_draft, linkedin_message_draft |
| D | NARRATIVE_COACH | Turn experiences into spoken interview narratives | list_of_experiences, interview_question | answer_outline (context/action/result/learning) |
| E | INTERVIEW_QA | Generate PM interview Q&A sets | target_company, target_role, structured_profile | list_of_questions, suggested_answers, follow_ups |
| F | LEARNING_PLAN | Rank hard skills, map to free resources | target_role, current_skills | ranked_skill_list with resources |
| G | JOB_TRACKER_DESIGN | Define the Sheets/Excel tracker model | user_preferences | columns, sample_rows, formulas |

### Shared schema: `structured_profile`

```json
{
  "identity": { "name": "Nicolas Wajs", "target_titles": ["Product Manager AI/Data", "Product Owner"] },
  "summary": "string (2-3 lines, adaptable per role)",
  "skills": {
    "hard": ["product discovery", "data platforms", "SQL", "AI/LLM product", "roadmapping"],
    "soft": ["stakeholder mgmt", "storytelling", "autonomy"],
    "tools": ["Jira", "Figma", "Notion", "..."]
  },
  "experiences": [
    {
      "id": "opensee",
      "org": "Opensee",
      "role": "Product Manager",
      "period": "…",
      "context": "SaaS analytics platform launch",
      "actions": ["…"],
      "results": [{ "metric": "…", "value": "…" }],
      "learnings": ["…"],
      "themes": ["SaaS", "data", "0-to-1"]
    }
  ],
  "certifications": ["…"],
  "narrative_principles": [
    "emphasize skills & learning over duration",
    "stay positive; each mission is an opportunity",
    "freelance is a deliberate, strategic choice",
    "lead with impact and value delivered"
  ]
}
```

### Prompt style per agent
- **CV_ANALYZER / JOB_MATCH / LEARNING_PLAN / JOB_TRACKER_DESIGN** — analytical,
  structured. "Return valid JSON only, matching this schema. No prose."
- **WRITING / NARRATIVE_COACH / INTERVIEW_QA** — generative, human. "Professional,
  positive, impact-focused. Reuse the narrative principles. Return labelled sections."

### Handoffs
1. CV_ANALYZER → produces `structured_profile` (cached, reused by all).
2. JOB_MATCH consumes profile + JD → `recommended_positioning`.
3. WRITING consumes profile + positioning → drafts.
4. NARRATIVE_COACH + INTERVIEW_QA consume profile for prep.
5. LEARNING_PLAN + JOB_TRACKER_DESIGN run independently on demand.

---

## 2. Claude Orchestrator Prompt (v1)

See `prompts/orchestrator-v1.md`.

## 3. Job Tracker Sheet Model

See `tracker/job-tracker-model.md`.
