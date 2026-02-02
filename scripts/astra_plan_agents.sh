#!/usr/bin/env bash
# Astra 4-Agent Cursor CLI: plan mode for Intelligence/Sentience, Emotions/Personality,
# States/Actions, Mama GPT Parenting. All 4 agents plan in parallel; then per agent:
# show plan, y/n, run plan or skip; repeat.
set -euo pipefail

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
    wait "$pid"
  done
  echo ""

  # Sequential review: show each plan, y/n, then execute or skip
  for i in "${!AGENT_TOPICS[@]}"; do
    entry="${AGENT_TOPICS[$i]}"
    topic="${entry%%|}"
    plan_file="$PLAN_DIR/plan_$i.txt"
    if [[ ! -f "$plan_file" ]]; then
      echo "No plan file for $topic, skipping."
      continue
    fi
    echo "========== Plan: $topic =========="
    cat "$plan_file"
    echo ""
    read -rp "Approve plan for $topic? (y/n): " ans
    if [[ "$ans" != [yY]* ]]; then
      echo "Skipping execute for $topic."
      continue
    fi
    agent -p "Execute the following plan. Do not ask for confirmation. $(cat "$plan_file")" --output-format text
  done

  rm -rf "$PLAN_DIR"
  echo "--- Cycle complete. Starting again (Ctrl+C to exit). ---"
done
