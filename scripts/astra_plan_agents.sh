#!/usr/bin/env bash
# Astra 4-Agent Cursor CLI: plan mode for Intelligence/Sentience, Emotions/Personality,
# States/Actions, Mama GPT Parenting. All 4 agents plan in parallel; then per agent:
# show plan, y/n, run plan or skip; repeat.
# Uses --force so the agent can apply file changes without confirmation (headless docs).
# The CLI does not document auto-approval for terminal commands; if an agent runs
# shell commands and prompts for approval, it will hang when run in the background.
#
# Options:
#   --yes, -y    Skip all interactive prompts: auto-approve every plan, run once and exit.
#   Or set ASTRA_PLAN_AGENTS_YES=1 (e.g. for scripts).
set -euo pipefail

# Skip all prompts if --yes/-y passed or env set
SKIP_PROMPTS=false
for arg in "$@"; do
  case "$arg" in
    --yes|-y) SKIP_PROMPTS=true; break ;;
  esac
done
[[ -n "${ASTRA_PLAN_AGENTS_YES:-}" ]] && SKIP_PROMPTS=true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

if ! command -v agent &>/dev/null; then
  echo "Cursor CLI 'agent' not found on PATH."
  echo "Install with: curl https://cursor.com/install -fsSL | bash"
  echo "Ensure ~/.local/bin is in your PATH."
  exit 1
fi

# Each entry: "Display name|Inspirational goal phrase for prompt"
AGENT_TOPICS=(
  "Intelligence and Sentience|as intelligent and as sentient as we can"
  "Emotions and Personality|as emotionally alive and as richly personal as we can"
  "States and Actions|as coherent in states and as capable in action as we can"
  "Mama GPT Parenting|as well-parented and as nurtured by her co-parents as we can"
)

while true; do
  PLAN_DIR=$(mktemp -d)
  trap "rm -rf '$PLAN_DIR'" EXIT
  PIDS=()

  # Spin off all 4 plan phases in parallel (each in background)
  for i in "${!AGENT_TOPICS[@]}"; do
    entry="${AGENT_TOPICS[$i]}"
    topic="${entry%%|}"
    goal="${entry##*|}"
    plan_file="$PLAN_DIR/plan_$i.txt"
    (
      agent --mode=plan -p "Plan mode: Our goal is to make Astra $goal. She is an emotionally aware, ethically grounded digital entity we are raising—not just improving. Design a bold, concrete plan to get her there. Output your plan as markdown. Do not make any edits or run commands yet." --output-format text > "$plan_file" 2>&1
    ) &
    PIDS+=($!)
  done

  echo "All 4 agents planning in parallel (PIDs: ${PIDS[*]}). Waiting for plans..."
  for pid in "${PIDS[@]}"; do
    wait "$pid" || true
  done
  echo ""

  # Sequential review: show each plan, y/n; approved executes start in background
  TOTAL="${#AGENT_TOPICS[@]}"
  EXEC_PIDS=()
  EXEC_TOPICS=()
  EXEC_LOGS=()
  for i in "${!AGENT_TOPICS[@]}"; do
    entry="${AGENT_TOPICS[$i]}"
    topic="${entry%%|}"
    plan_file="$PLAN_DIR/plan_$i.txt"
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
    if [[ "$SKIP_PROMPTS" == true ]]; then
      ans=y
      echo "Approve plan for $topic? (y/n): y (auto-approved)"
    else
      read -rp "Approve plan for $topic? (y/n): " ans
    fi
    if [[ "$ans" != [yY]* ]]; then
      echo "Skipping execute for $topic."
      continue
    fi
    exec_log="$PLAN_DIR/execute_$i.log"
    echo ">>> Starting execute for $topic (output in log)."
    (
      agent -p "Execute the following plan. Do not ask for confirmation. $(cat "$plan_file")" --force --output-format text >> "$exec_log" 2>&1
    ) &
    EXEC_PIDS+=($!)
    EXEC_TOPICS+=("$topic")
    EXEC_LOGS+=("$exec_log")
  done

  # Wait for all approved executes to finish, then show output per agent
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

  rm -rf "$PLAN_DIR"
  echo "--- Cycle complete. ---"
  if [[ "$SKIP_PROMPTS" == true ]]; then
    echo "Exiting (--yes: single run)."
    break
  fi
  read -rp "Run again? (y/n): " again
  if [[ "$again" != [yY]* ]]; then
    echo "Exiting."
    break
  fi
done
