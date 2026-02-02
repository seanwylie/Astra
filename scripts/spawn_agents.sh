#!/usr/bin/env bash
# Spawn Agents: Config-driven multi-agent Cursor CLI for background improvements.
# Agents plan in parallel; you review y/n per plan; approved ones execute.
# Uses --force for headless file edits; no-hang rules + </dev/null for execute phase.
# Plans persist in .spawn-agents/plans/; previous cycle archived to .spawn-agents/archive/.
#
# Usage: ./spawn_agents.sh [--config path] [--dry-run]
#   --config path  Config file (default: ./spawn_agents.config or ./.spawn_agents.config)
#   --dry-run      Print prompts only; make no agent calls
#
# Copy spawn_agents.example.config to spawn_agents.config and customize for your project.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=false
CONFIG_PATH=""

args=("$@")
for i in "${!args[@]}"; do
  case "${args[i]}" in
    --dry-run) DRY_RUN=true ;;
    --config)
      if [[ $((i + 1)) -lt ${#args[@]} ]]; then
        CONFIG_PATH="${args[i+1]}"
      fi
      ;;
  esac
done

# Resolve config file and ROOT
if [[ -n "$CONFIG_PATH" ]]; then
  if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "ERROR: Config file not found: $CONFIG_PATH"
    exit 1
  fi
  CONFIG_FILE="$(cd "$(dirname "$CONFIG_PATH")" && pwd)/$(basename "$CONFIG_PATH")"
  ROOT="$(cd "$(dirname "$CONFIG_PATH")" && pwd)"
else
  ROOT="$(cd "$SCRIPT_DIR" && pwd)"
  if [[ -f "$ROOT/spawn_agents.config" ]]; then
    CONFIG_FILE="$ROOT/spawn_agents.config"
  elif [[ -f "$ROOT/.spawn_agents.config" ]]; then
    CONFIG_FILE="$ROOT/.spawn_agents.config"
  else
    echo "ERROR: No config found. Create spawn_agents.config from spawn_agents.example.config"
    echo "  cp spawn_agents.example.config spawn_agents.config"
    echo "  # Edit spawn_agents.config, then run again"
    exit 1
  fi
fi

cd "$ROOT"
# shellcheck source=/dev/null
source "$CONFIG_FILE"

# Apply defaults for optional config vars
: "${PROJECT_NAME:=Unnamed}"
: "${PROJECT_DESCRIPTION:=this project}"
: "${REQUIRED_BRANCH:=}"
: "${PLAN_CONTEXT:=Read project docs. Propose concrete, actionable improvements.}"
: "${EXTRA_EXEC_CONSTRAINTS:=}"
: "${AGENT_TOPICS:=()}"

if [[ ${#AGENT_TOPICS[@]} -eq 0 ]]; then
  echo "ERROR: AGENT_TOPICS is empty in $CONFIG_FILE"
  exit 1
fi

# Format PLAN_CONTEXT: each line -> "- line"
FORMATTED_CONTEXT=$(echo "$PLAN_CONTEXT" | sed 's/^/- /')

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
if [[ -n "$REQUIRED_BRANCH" ]] && [[ "$BRANCH" != "$REQUIRED_BRANCH" ]] && [[ "$DRY_RUN" != "true" ]]; then
  echo "ERROR: Must run on branch '$REQUIRED_BRANCH'. Current: $BRANCH"
  echo "Switch with: git checkout $REQUIRED_BRANCH"
  exit 1
fi

if [[ "$DRY_RUN" != "true" ]] && ! command -v agent &>/dev/null; then
  echo "Cursor CLI 'agent' not found on PATH."
  echo "Install with: curl https://cursor.com/install -fsSL | bash"
  echo "Ensure ~/.local/bin is in your PATH."
  exit 1
fi

# Ensure Cursor CLI can write cli-config.json (avoids ENOENT when agents run in parallel)
mkdir -p "$HOME/.cursor"

PLANS_BASE="$ROOT/.spawn-agents"
PLANS_DIR="$PLANS_BASE/plans"
ARCHIVE_DIR="$PLANS_BASE/archive"
NO_HANG_RULES="CRITICAL - Non-interactive only: You MUST NOT run any command that prompts for user input, confirmation, or approval.
- Never run: npm install, npm run lint:fix, eslint --fix, cdk deploy, git commit (without -m), or any interactive script.
- Only run commands that complete without stdin input (e.g., npm run build, npm run lint, read-only git commands).
- Prefer file edits over terminal commands. If a command might hang, skip it and document in comments.
${EXTRA_EXEC_CONSTRAINTS:+$'\n'$EXTRA_EXEC_CONSTRAINTS}"

build_plan_prompt() {
  local topic="$1"
  local goal="$2"
  echo "Plan mode: $PROJECT_NAME is $PROJECT_DESCRIPTION.
Focus: $topic. Goal: $goal.

Context:
$FORMATTED_CONTEXT

Output your plan as markdown. Do not make any edits or run commands yet."
}

if [[ "$DRY_RUN" == "true" ]]; then
  echo "=== DRY RUN: Prompts that would be sent (no agent calls) ==="
  echo "Config: $CONFIG_FILE"
  echo ""
  for i in "${!AGENT_TOPICS[@]}"; do
    entry="${AGENT_TOPICS[$i]}"
    topic="${entry%%|*}"
    goal="${entry##*|}"
    n=$((i + 1))
    echo "=============================================="
    echo "  PLAN PROMPT $n of ${#AGENT_TOPICS[@]}: $topic"
    echo "=============================================="
    echo "agent --mode=plan -p \"...\""
    echo ""
    build_plan_prompt "$topic" "$goal"
    echo ""
  done
  echo "=============================================="
  echo "  EXECUTE PROMPT (appended to each approved plan)"
  echo "=============================================="
  echo "agent -p \"...\" --force --output-format text"
  echo ""
  echo "Execute the following plan. Do not ask for confirmation.

$NO_HANG_RULES

Plan:
[Plan content from plan_N.txt would be inserted here]"
  echo ""
  echo "=== DRY RUN complete. No agent calls were made. ==="
  exit 0
fi

while true; do
  if [[ -d "$PLANS_DIR" ]] && [[ -n "$(ls -A "$PLANS_DIR" 2>/dev/null)" ]]; then
    ARCHIVE_SUBDIR="$ARCHIVE_DIR/$(date +%Y-%m-%dT%H-%M-%S)"
    mkdir -p "$ARCHIVE_SUBDIR"
    mv "$PLANS_DIR"/* "$ARCHIVE_SUBDIR/" 2>/dev/null || true
    rmdir "$PLANS_DIR" 2>/dev/null || true
  fi
  mkdir -p "$PLANS_DIR"
  PIDS=()

  for i in "${!AGENT_TOPICS[@]}"; do
    entry="${AGENT_TOPICS[$i]}"
    topic="${entry%%|*}"
    goal="${entry##*|}"
    plan_file="$PLANS_DIR/plan_$i.txt"
    plan_prompt=$(build_plan_prompt "$topic" "$goal")
    (
      agent --mode=plan -p "$plan_prompt" --output-format text > "$plan_file" 2>&1
    ) &
    PIDS+=($!)
  done

  TOTAL="${#AGENT_TOPICS[@]}"
  echo "All $TOTAL agents planning in parallel (PIDs: ${PIDS[*]}). Waiting for plans..."
  for pid in "${PIDS[@]}"; do
    wait "$pid" || true
  done
  echo ""

  EXEC_PIDS=()
  EXEC_TOPICS=()
  EXEC_LOGS=()
  for i in "${!AGENT_TOPICS[@]}"; do
    entry="${AGENT_TOPICS[$i]}"
    topic="${entry%%|*}"
    plan_file="$PLANS_DIR/plan_$i.txt"
    n=$((i + 1))
    echo ""
    echo "=============================================="
    echo "  Plan $n of $TOTAL: $topic"
    echo "=============================================="
    if [[ ! -f "$plan_file" ]]; then
      echo "No plan file for $topic, skipping."
      continue
    fi
    cat "$plan_file"
    echo ""
    echo "----------------------------------------------"
    read -rp "Approve plan for $topic? (y/n): " ans
    if [[ "$ans" != [yY]* ]]; then
      echo "Skipping execute for $topic."
      continue
    fi
    exec_log="$PLANS_DIR/execute_$i.log"
    echo ">>> Starting execute for $topic (output in log)."
    plan_content=$(cat "$plan_file")
    (
      agent -p "Execute the following plan. Do not ask for confirmation.

$NO_HANG_RULES

Plan:
$plan_content" --force --output-format text >> "$exec_log" 2>&1 </dev/null
    ) &
    EXEC_PIDS+=($!)
    EXEC_TOPICS+=("$topic")
    EXEC_LOGS+=("$exec_log")
  done

  if [[ ${#EXEC_PIDS[@]} -gt 0 ]]; then
    echo ""
    echo "Waiting for ${#EXEC_PIDS[@]} execute(s) to finish..."
    for pid in "${EXEC_PIDS[@]}"; do
      wait "$pid" || true
    done
    echo ""
    for j in "${!EXEC_TOPICS[@]}"; do
      echo "========== Execute output: ${EXEC_TOPICS[$j]} =========="
      cat "${EXEC_LOGS[$j]}"
      echo ""
    done
    echo ">>> All executes complete."
  fi

  echo "--- $PROJECT_NAME cycle complete. Starting again (Ctrl+C to exit). ---"
done
