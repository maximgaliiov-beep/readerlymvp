# Brighterly AI Knowledge Base — Proposal & Implementation Plan

**Date:** 2026-04-17
**Author:** Claude (AI Assistant)
**Status:** Draft for review

---

## 1. Goal

Build a structured knowledge base inside the Brighterly Notion workspace that:
- Serves as the **single source of truth** about the business, product, team, and operations
- Stores context as clean, structured **markdown-exportable pages** that people and AI assistants can consume
- Enables team members to pull context files for **training AI assistants** and **building new features**
- Prepares for **Stage 2: Obsidian sync** (bidirectional or one-way export)

---

## 2. Current State (What Already Exists)

### Existing Notion Structure
```
Brighterly General (corporate portal — about us, guides, contacts)
├── Departments/
│   ├── Brighterly / Sales
│   ├── Brighterly / Marketing
│   ├── Brighterly / Development (architecture, tools, infra, processes)
│   ├── Brighterly / CSD (Customer Success)
│   ├── Brighterly / Product Team (analytics, docs, funnels, KB)
│   ├── Brighterly / Communications (brand)
│   ├── Operations Team
│   └── Brighterly Board
├── Brighterly Brand (UVP, messaging, stats)
├── Brighterly <> Legal
├── Methodology Space
└── Brighterly AI Summary (GitHub-linked)
```

### Problems with current state
- Knowledge is **scattered across department silos** — no unified context layer
- Multiple "Knowledge Base" pages exist in different places (Product, SEO, Recruiting) with different meanings
- No standardized format for context files — mix of UA/EN, task boards, docs, and wikis
- No tagging or categorization system for AI consumption
- Brand/product info lives in Communications but overlaps with General and CSD pitches

---

## 3. Proposed Knowledge Base Structure

A new top-level page in Notion: **`Writerly Knowledge Base`** (or nested under Brighterly General).

```
📚 Writerly Knowledge Base
│
├── 🏢 Company/
│   ├── about-brighterly.md        — Mission, vision, history, market ($130B)
│   ├── company-structure.md       — SKELAR → Brighterly relationship, org chart
│   ├── key-people.md              — Leadership, roles, contacts
│   ├── values-and-culture.md      — Company values, ways of working
│   └── investments-and-traction.md — Funding rounds, growth metrics (3x YoY)
│
├── 🎯 Product/
│   ├── product-overview.md        — What Brighterly is, subjects, age range (6-17)
│   ├── customer-personas.md       — Who buys, parent profiles, student profiles
│   ├── methodology.md             — Teaching approach, SPARK framework
│   ├── platform-features.md       — Tutoring, homework help, quizzes, reading
│   ├── pricing-and-plans.md       — Subscription models, ESA eligibility
│   ├── competitive-landscape.md   — Key competitors, positioning
│   └── product-roadmap.md         — Current priorities, upcoming features
│
├── 📊 Metrics & Analytics/
│   ├── key-kpis.md                — LTV/CAC, conversion, retention, churn
│   ├── growth-metrics.md          — Revenue, lessons delivered (360K+), tutors (800+)
│   ├── marketing-metrics.md       — CAC, channel performance, SEO stats
│   ├── operational-metrics.md     — Tutor attendance, no-shows, delays
│   └── dashboards-and-tools.md    — Where to find data (Looker, GA, internal)
│
├── 💻 Development/
│   ├── tech-stack.md              — Languages, frameworks, infrastructure
│   ├── architecture-overview.md   — System design, services, integrations
│   ├── development-processes.md   — Git workflow, code review, CI/CD
│   ├── tools-and-access.md        — YouTrack, VPN, dev tools list
│   └── api-and-integrations.md    — Stripe, Mailkeeper, Rasayel, 100ms, etc.
│
├── 📣 Marketing & Brand/
│   ├── brand-guidelines.md        — Voice, tone, messaging, UVP
│   ├── content-guidelines.md      — Writing rules, SEO standards, compliance
│   ├── target-audience.md         — US market, K-12, parent demographics
│   ├── channels-and-funnels.md    — Paid, organic, landing pages, quizzes
│   └── press-and-media.md         — Fast Company, Tech.eu, press releases
│
├── 🤝 Sales & CSD/
│   ├── sales-process.md           — Funnel, CRM, onboarding flow
│   ├── customer-journey.md        — From quiz → trial → subscription → retention
│   ├── objection-handling.md      — Common objections, responses
│   ├── support-playbook.md        — Escalation, troubleshooting, policies
│   └── tutor-management.md        — Hiring, vetting, scheduling, TL structure
│
├── ⚖️ Legal & Compliance/
│   ├── legal-overview.md          — Company legal structure, jurisdiction
│   ├── compliance-requirements.md — Payment page rules, content standards
│   ├── esa-program.md             — ESA eligibility, state-by-state rules
│   └── data-and-privacy.md        — Student data handling, COPPA if applicable
│
└── 🔧 Operations/
    ├── team-operations.md         — HR processes, onboarding, offboarding
    ├── tools-and-systems.md       — Notion, Slack, HiBob, Freshservice, ClickUp
    ├── communication-channels.md  — Who to contact for what
    └── war-and-resilience.md      — Business continuity, relocation support
```

---

## 4. Page Format Standard

Every knowledge base page should follow this template for AI-readability:

```markdown
# [Topic Title]

> Last updated: YYYY-MM-DD
> Owner: [Name / Role]
> Status: Active | Draft | Needs Review

## Summary
[2-3 sentence overview — this is what AI assistants will use as quick context]

## Details
[Structured content with headers, bullet points, tables]

## Key Facts
- Fact 1
- Fact 2

## Related Pages
- [[page-link-1]]
- [[page-link-2]]

## Change Log
| Date | Change | By |
|------|--------|----|
```

This format is:
- **Obsidian-compatible** (uses standard markdown, wikilinks)
- **AI-parseable** (summary section = quick context, structured sections = deep context)
- **Human-maintainable** (owners, change log, status)

---

## 5. What I (Claude) Can Do Automatically

### CAN do via Notion MCP:
| Action | Feasibility |
|--------|-------------|
| Create the top-level "Writerly Knowledge Base" page | ✅ Yes |
| Create all sub-pages with the folder structure above | ✅ Yes |
| Pre-populate pages by pulling content from existing Notion pages | ✅ Yes |
| Read existing Brand, Development, Product pages and synthesize into context files | ✅ Yes |
| Apply the standard template to each page | ✅ Yes |
| Search and cross-reference existing content to avoid duplication | ✅ Yes |

### CANNOT do (needs human input):
| Action | Why |
|--------|-----|
| Access private/restricted pages I can't see via MCP | Permissions |
| Verify accuracy of financial/legal data | Business-critical |
| Decide which metrics are current vs. outdated | Domain knowledge |
| Set page owners and review schedules | Organizational decision |
| Grant team access / permissions in Notion | Admin-only |

---

## 6. Implementation Plan

### Phase 1: Foundation (Claude can do now)
1. Create the `Writerly Knowledge Base` root page in Notion
2. Create all category sub-pages with the template structure
3. Pull and synthesize content from existing pages:
   - `Brighterly General` → Company section
   - `Brighterly Brand` pages → Marketing & Brand section
   - `Brighterly / Development` → Development section
   - `Brighterly / Product Team` + `Product Documentation` → Product section
   - `Brighterly / CSD` → Sales & CSD section
   - `Brighterly / Communications` → Brand section
   - `Brighterly <> Legal` → Legal section
4. Fill in the "Summary" and "Key Facts" sections from available data

### Phase 2: Review & Enrich (Human + Claude)
5. You review each section, flag inaccuracies, add missing context
6. Assign page owners from each department
7. I refine and restructure based on your feedback
8. Fill gaps — especially Metrics & Analytics (needs access to dashboards)

### Phase 3: Obsidian Bridge (Stage 2)
9. Export pages as `.md` files to a git repo (can automate)
10. Set up Obsidian vault pointing to that repo
11. Optionally: build a sync script (Notion API → .md files) on a cron
12. Connect Obsidian vault as context for Claude Code / other AI tools

---

## 7. Estimated Scope

| Phase | Pages | Effort |
|-------|-------|--------|
| Phase 1 — Structure + initial content | ~30 pages | Claude can do in one session |
| Phase 2 — Review & enrich | ~30 pages | Needs 1-2 review cycles with you |
| Phase 3 — Obsidian sync | Config + script | Separate technical task |

---

## 8. Decision Needed From You

Before I start building:

1. **Where to place the root page?** Options:
   - New top-level teamspace page `Writerly Knowledge Base`
   - Nested under `Brighterly General`
   - Nested under `Departments`

2. **Naming:** "Writerly Knowledge Base" or "Brighterly Knowledge Base" or "Brighterly Context Hub"?

3. **Language:** Pages in English only? Or bilingual (EN for AI context, UA for internal notes)?

4. **Should I start building Phase 1 now?** I can create the structure and start pulling content from existing pages immediately.

---

*This document lives at: `docs/knowledge-base-proposal.md` in the Writerly_MVP repo.*
