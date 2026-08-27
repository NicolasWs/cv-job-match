# Interview Prep — UpSlide, Senior Product Manager

## Q&A Set

### "Tell me about yourself" (60-90s)
- 15+ years building product for financial-markets professionals — first inside vendors serving trading/risk desks (Reuters, Sophis, Finastra), then as a SaaS PM at Opensee onboarding HSBC as their first cloud client.
- Since mid-2025, gone independent by design: shipped an AI-native broker-voting app end-to-end in under two months, working across several parallel engagements in AI/data.
- What ties it together: understanding what a finance professional needs from a deliverable — a deck, a model, a report — and building product/process to get it there faster and more reliably.
- Landing line: UpSlide's Refine team is the first role I've seen that asks for exactly that combination — AI agents, financial deliverables, and a quality bar set by what a top institution expects.

### Strengths (3, each with proof + metric)
1. **Discovery with finance users, fast.** Onboarded HSBC GAM as Opensee's first cloud + first AM client, defining the metrics that mattered to them directly. Five years at Finastra running workshops across 30+ institutions, translating real analyst workflows into product requirements (+65% qualified opportunities from that discovery-led approach).
2. **Shipping AI-native product, not a wrapper.** Broker-voting app: full AI SDLC, design to production go-live in under two months.
3. **Quality-at-scale discipline.** Led functional QA coordinating 80+ FTEs validating analytics and financial-model libraries before release at Reuters — the same instinct the eval/QA loop for AI agents needs, applied pre-AI but at real scale.

### Weaknesses (2, honest, with mitigation)
1. No direct experience building an eval loop *specifically for AI agent output* (golden datasets, regression testing on generative output) — my QA experience is deep but from a pre-AI era. Mitigation: I've spent the last year deliberately building AI/agentic skills (LangChain/RAG, crewAI, KNIME agentic AI, Dataiku GenAI certifications) precisely to close this gap, and the broker-voting project forced me to think about output correctness under an AI SDLC in practice.
2. My total experience (15+ yrs) sits above the posting's stated 4-8y band. Mitigation: reframe as ramp-speed — less time needed to build credibility with finance users and understand the deliverables, more time available to focus on the agent/eval build from day one.

### "Why UpSlide / why this role?"
- Genuine overlap of domain (financial deliverables) and method (AI agents) that I haven't found elsewhere in my search.
- B-Corp / employee-owned framing (30% employee-owned) resonates with how I want to work post-corporate-vendor life.
- The "own the agent library end-to-end" scope is exactly the ownership/autonomy model I've chosen deliberately since going independent.

### "Recent experience" — freelance framing
- Since July 2025, freelance by deliberate strategic choice, not a gap: chose to run several concentrated, high-intensity engagements (broker-voting app, Natixis credit derivatives transition, TradeValue/Woon AI POCs) rather than one fixed seat, specifically to build direct, hands-on AI-shipping experience fast.

### Role-specific behavioural questions
1. **"Walk us through how you'd scope the first 3 agents for Refine."** → Start from user discovery (which deliverable step causes the most rework today — comps table formatting? number-checking in a model?), pick the highest-frequency/highest-error step, define a golden dataset from real (anonymized) client decks, ship narrow, measure before expanding scope.
   - Follow-up: "How do you avoid scope creep across the agent library?" → Treat each agent as its own small product with its own usage/quality metrics; kill or merge low-usage agents quarterly.
2. **"How do you know an agent's output is good enough for a top financial institution?"** → Borrow directly from the Reuters QA model: define acceptance criteria with domain experts up front, build a golden/regression set from real cases, track error categories not just pass/fail, involve the finance domain expert in every methodology review, not just engineering.
   - Follow-up: "What if experts disagree on what 'good' looks like?" → Document the disagreement as a versioned rubric decision, don't let it block shipping — revisit after real usage data.
3. **"Tell me about a time you had to say no to a stakeholder."** → (use a Finastra RFP example: competitive positioning conversations where I had to push back on over-promising scope to close a deal, protecting delivery credibility over a short-term win) — adapt live from real Finastra RFP coordination experience, keep numbers honest (don't invent a specific declined deal size not in the CV).

## Project Storytelling (STAR)

### 1. Broker-voting app — AI-native shipping (Situation→Task→Action→Result→Learning)
- **S:** French asset manager needed a broker-voting tool, no existing solution fit their process.
- **T:** Deliver a working, production-grade web app fast, using AI-assisted development end to end.
- **A:** Owned design through build using a full AI SDLC — from requirements to shipped Angular/.NET app in the client's own Azure cloud.
- **R:** Live in production in under two months, from initial design to go-live.
- **L:** AI-native delivery collapses timeline but raises the bar on catching errors early — directly informs how I'd think about agent QA at UpSlide.

### 2. HSBC GAM onboarding — discovery-led product (Opensee)
- **S:** Opensee's first cloud deployment, first asset-manager client — no playbook.
- **T:** Define the product/metrics that would make this a reference deployment.
- **A:** Ran direct discovery with HSBC's data/reporting teams, defined key metrics for reporting automation and adoption, drove workshops training 100+ users.
- **R:** Delivered 99% uptime vs a 95% contractual target across the first 6 months.
- **L:** The best product decisions come from sitting with the actual users of the deliverable — the same instinct the posting asks for with finance analysts.

### 3. QA leadership at scale — Reuters
- **S:** Reuters 3000 Xtra shipped 30-60 updates a year to financial-market clients globally; any error in an analytics/model library was high-stakes.
- **T:** Guarantee release quality at scale before financial professionals touched the output.
- **A:** Led functional QA coordinating 80+ FTEs validating analytics and financial-model libraries pre-release.
- **R:** Sustained tier-1 client retention through the release cadence.
- **L:** This is the closest real precedent I have for building an agent eval/golden-dataset loop — pre-AI, but the discipline transfers directly.

## Interview Support Sheet (one page)

**Key stories:** 1) Broker-voting app — AI SDLC, <2 months to production. 2) HSBC GAM onboarding — 99% uptime vs 95% target. 3) Reuters QA at scale — 80+ FTEs validating financial-model libraries pre-release.

**Key metrics to have ready:** <2 months (design→production, broker app); 99% vs 95% contractual uptime (Opensee/HSBC); +65% qualified opportunities (Finastra workshops); 30+ institutions discovery (Finastra); 80+ FTEs QA coordination (Reuters); $500K-$3M deal range (Finastra RFPs); 45 consultants mentored (Misys).

**Talking points:**
- Domain + method overlap is rare — say it plainly, it's the honest reason this role stands out.
- Lead with the broker-voting app every time AI-native shipping comes up — it's the single strongest, most concrete proof point.
- Name the eval-loop gap myself before being asked — own it, then pivot straight to the Reuters QA precedent and the AI certifications closing it.
- Ask about the current agent library's usage data — shows I think in metrics, not features.

**Questions to ask them:**
1. What does the agent library look like today — how many agents, and what's the current usage/quality signal you're tracking?
2. How do domain experts (the finance-side reviewers) get looped into methodology review today — ad hoc, or a standing process?
3. What's the single most common rework/error UpSlide sees in customer decks or models today that no agent addresses yet?
4. How does the Refine team's roadmap get prioritized against the rest of UpSlide's product (the core Office add-ins)?
5. What would "shipped and clearly working" look like for my first 90 days, from your side?
