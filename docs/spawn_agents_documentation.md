# Spawn Agents Script Customization for InnerCompass

**Last Updated**: February 2025

## Current State

[spawn_agents.sh](../spawn_agents.sh) is adapted from an "Astra" project: 4 parallel agents plan improvements for Intelligence, Emotions, States, and "Mama GPT Parenting." It uses the Cursor CLI `agent` in plan mode, then y/n review, then execute with `--force`. There is no branch check or InnerCompass-specific context.

## Key Changes

### 1. Main-Branch-Only Guard (Critical)

Add an explicit branch check at the top of the script (after `cd "$ROOT"`):

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
if [[ "$BRANCH" != "main" ]]; then
  echo "ERROR: spawn_agents.sh must run on main branch. Current: $BRANCH"
  echo "Switch with: git checkout main"
  exit 1
fi
```

**Rationale**: Background improvements are intended for main only; running on feature branches risks accidental merges or conflicts.

### 2. InnerCompass Agent Categories (6 Agents)

Align categories with product goals, docs structure, and ROADMAP priorities:

| Category | Focus | Key Docs |
| --- | --- | --- |
| **UX & Polish** | Loading states, error handling, accessibility, delight, progress indicators, transitions | [Design/](../Design/), [mobilescreenrules.mdc](../.cursor/rules/mobilescreenrules.mdc) |
| **Activities** | All 15 activities—engagement, consistency, tier gating, feature completeness | [activity-matrix-system](../Features/activity-matrix-system.md), [Activities/](../Activities/) |
| **Core App** | Auth, IAP/subscription, navigation, onboarding, profile, home | [product-spec](../Features/product-spec.md), [ROADMAP](../ROADMAP.md) |
| **Compliance & Privacy** | GDPR, CCPA, data safety, AI privacy, terms, deletion flows | [Compliance/](../Compliance/), [security-compliance](../Architecture/security-compliance.md) |
| **Security** | Auth hardening, API security, encryption, threat mitigation | [security-compliance](../Architecture/security-compliance.md) |
| **Performance** | App speed, Lambda optimization, caching, bundle size | Architecture, [loading-state-system](../../mobile-expo/loading-state-system.md) |

**Why 6 agents**: Covers main improvement areas without excessive overlap. AI/Content could be a 7th if desired, but Activities and Core App already touch AI usage.

### 3. Context-Rich Prompts for Plan Mode

Each prompt must:

- Identify InnerCompass and the category
- Point agents to relevant docs and rules
- Constrain behavior (no deployment, no `npm run lint:fix`, follow architecture)
- Ask for concrete, actionable plans
- Emphasize "improve" not "refactor for its own sake"

**Prompt template pattern**:

```
Plan mode: InnerCompass is a spiritual guidance mobile app (React Native, AWS Lambda, DynamoDB).
Focus: [CATEGORY]. Goal: [INSPIRATIONAL_GOAL_PHRASE].

Context:
- Read docs/[relevant-docs] and .cursor/rules/innercompass-architecture.mdc
- Follow architecture patterns (no lint:fix, no deployment, no risky scripts)
- Plans will run headless: only include steps that use file edits or non-interactive commands (no npm install, no prompts)
- Propose concrete, actionable improvements—not theoretical refactors

Output your plan as markdown. Do not make any edits or run commands yet.
```

**Per-category goal phrases** (aligned with SWAN_SONG_MASTER_PLAN, product-spec):

- **UX & Polish**: "as delightful, accessible, and error-resilient as we can—next-generation feel"
- **Activities**: "as engaging, consistent, and feature-complete across all 15 activities as we can"
- **Core App**: "as reliable and seamless in auth, IAP, navigation, and onboarding as we can"
- **Compliance & Privacy**: "as compliant, transparent, and privacy-respectful as we can for store and regulations"
- **Security**: "as secure and threat-resilient as we can without over-engineering"
- **Performance**: "as fast and resource-efficient as we can on mobile and backend"

### 4. Execute Phase: No-Hang and Constraint Rules (Critical)

The `--force` flag only bypasses Cursor's confirmation for **file edits**. The agent can still run **terminal commands** that prompt for user input (e.g., `npm install` with prompts, `git commit` without `-m`, interactive scripts), causing the script to hang indefinitely in the background.

**Add explicit no-hang rules to the execute prompt**:

```
CRITICAL - Non-interactive only: You MUST NOT run any command that prompts for user input, confirmation, or approval.
- Never run: npm install, npm run lint:fix, eslint --fix, cdk deploy, git commit (without -m), or any interactive script.
- Only run commands that complete without stdin input (e.g., npm run build, npm run lint, read-only git commands).
- Prefer file edits over terminal commands. If a command might hang, skip it and document in comments.

InnerCompass constraints: Do NOT run lint:fix. Do NOT deploy. Follow .cursor/rules/innercompass-architecture.mdc.
```

**Additional safeguards in script**:

- Redirect stdin for execute phase: `agent ... >> "$exec_log" 2>&1 </dev/null` so any accidental interactive prompt receives EOF instead of blocking (plan phase is read-only so less critical)

### 5. Plan Persistence and Archiving

Replace ephemeral `mktemp -d` with a persistent plans directory:

**Directory structure**:

```
<repo>/.spawn-agents/
  plans/           # Current cycle plans (plan_0.txt ... plan_5.txt)
  archive/         # Previous cycle, timestamped
    2025-02-01T22-30-00/
      plan_0.txt
      ...
      execute_0.log
      ...
```

**Logic per cycle**:

1. If `plans/` exists and has content: move `plans/` → `archive/YYYY-MM-DDTHH-MM-SS/`
2. Create fresh `plans/` for this cycle
3. Write plans to `plans/plan_0.txt`, etc.
4. Write execute logs to `plans/execute_0.log`, etc.

**Resume capability**: If the script is killed mid-cycle, the last complete cycle lives in `archive/`. A future `--resume` flag could re-show plans from the most recent archive and re-run execute for approved ones (out of scope for initial implementation, but structure enables it).

**Add `.spawn-agents/` to `.gitignore`** so plans and logs stay local.

### 6. Script Header and Cycle Message

- Update header to describe InnerCompass background improvements
- Change cycle message to: `"--- InnerCompass cycle complete. Starting again (Ctrl+C to exit). ---"`

### 7. Documentation

Add or update a doc under [docs/Development/](../Development/) (e.g., `spawn-agents-background-improvements.md`) that describes:

- Purpose: evening spawn, review plans, approve, wake to improved codebase
- Branch requirement: main only
- Categories and what each agent focuses on
- No-hang rules (non-interactive only, banned commands, stdin redirect)
- Plan persistence and archiving (`.spawn-agents/`, archive-before-write, resume capability)
- Constraints (no deployment, no lint:fix)
- Reference to relevant docs for each category

---

## File Changes Summary

| File | Change |
| --- | --- |
| [spawn_agents.sh](../../spawn_agents.sh) | Branch guard; persistent `.spawn-agents/` dir with archive-before-write; no-hang execute prompt (CRITICAL block); `</dev/null` stdin redirect for execute phase; new AGENT_TOPICS and prompts; header/cycle text |
| [.gitignore](../../.gitignore) | Add `.spawn-agents/` so plans and logs stay local |
| [docs/Development/spawn-agents-background-improvements.md](../Development/spawn-agents-background-improvements.md) | New doc: purpose, branch requirement, categories, no-hang rules, plan persistence, constraints |

---

## Optional Enhancements (Out of Scope for Initial Plan)

- **7th agent (AI & Content)**: Prompts, personalization, tier-based logic, prompt builder
- **Category selection flag**: Run subset of agents via `--categories ux,activities`
- **Single-cycle mode**: `--once` to run one cycle then exit (vs infinite loop)
