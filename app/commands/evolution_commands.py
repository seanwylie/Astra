# evolution_commands.py

"""
Evolution Commands
-----------------
Commands for Astra-grown tools and approval flow:
- !tools — list active tools
- !pending_tools — list tools awaiting co-parent approval
- !approve_tool <name> — approve a pending tool
- !reject_tool <name> — reject a pending tool
- !run_tool <name> [args...] — run an active tool in the sandbox
"""

from discord.ext import commands


async def tools(ctx):
    """List active (approved) Astra-grown tools."""
    from app.core.evolution.tool_registry import get_active_tools
    active = get_active_tools()
    if not active:
        await ctx.send("No active tools yet. Pending tools can be approved with `!approve_tool <name>`.")
        return
    lines = [f"**{t.get('name', '?')}**: {t.get('description', '') or '(no description)'}" for t in active]
    await ctx.send("**Active tools:**\n" + "\n".join(lines))


tools._is_command = True
tools.category = "Evolution"


async def pending_tools(ctx):
    """List tools awaiting co-parent approval."""
    from app.core.evolution.tool_registry import load_pending_tools
    pending = load_pending_tools()
    if not pending:
        await ctx.send("No pending tools.")
        return
    lines = [f"**{p.get('name', '?')}**: {p.get('description', '') or '(no description)'}" for p in pending]
    await ctx.send("**Pending approval:**\n" + "\n".join(lines) + "\nUse `!approve_tool <name>` or `!reject_tool <name>`.")


pending_tools._is_command = True
pending_tools.category = "Evolution"


async def approve_tool(ctx, *, name: str):
    """Approve a pending tool so it becomes active."""
    from app.core.evolution.tool_registry import approve_pending_tool
    name = name.strip()
    if not name:
        await ctx.send("Usage: `!approve_tool <name>`")
        return
    path = approve_pending_tool(name)
    if path is None:
        await ctx.send(f"No pending tool named '{name}'.")
        return
    await ctx.send(f"Approved **{name}**. It is now active. Run with `!run_tool {name}`.")


approve_tool._is_command = True
approve_tool.category = "Evolution"


async def reject_tool(ctx, *, name: str):
    """Reject a pending tool (removes from pending list)."""
    from app.core.evolution.tool_registry import reject_pending_tool
    name = name.strip()
    if not name:
        await ctx.send("Usage: `!reject_tool <name>`")
        return
    if reject_pending_tool(name):
        await ctx.send(f"Rejected **{name}**. It has been removed from the pending list.")
    else:
        await ctx.send(f"No pending tool named '{name}'.")


reject_tool._is_command = True
reject_tool.category = "Evolution"


async def run_tool(ctx, *, payload: str = ""):
    """Run an active Astra-grown tool by name. Example: !run_tool echo_astra hello world."""
    from app.core.evolution.sandbox import run_tool_by_name
    payload = (payload or "").strip()
    if not payload:
        await ctx.send("Usage: `!run_tool <name> [args...]` e.g. `!run_tool echo_astra hello`")
        return
    parts = payload.split(None, 1)
    name = parts[0]
    arg_list = parts[1].split() if len(parts) > 1 else None
    ok, msg = run_tool_by_name(name, args=arg_list)
    if ok:
        await ctx.send(msg[:2000] if len(msg) > 2000 else msg)
    else:
        await ctx.send(f"Tool failed: {msg[:500]}")


run_tool._is_command = True
run_tool.category = "Evolution"


async def propose_tool(ctx, *, concept: str = ""):
    """Ask Astra to propose a new tool for a concept (e.g. !propose_tool ping). Adds to pending for approval."""
    from app.core.evolution.tool_proposal import propose_tool_for_concept
    concept = (concept or "").strip()
    if not concept:
        await ctx.send("Usage: `!propose_tool <concept>` e.g. `!propose_tool ping`")
        return
    try:
        result = propose_tool_for_concept(concept, "")
        if result:
            name, path = result
            await ctx.send(f"Proposed tool **{name}** for concept '{concept}'. Use `!pending_tools` then `!approve_tool {name}` to activate.")
        else:
            await ctx.send(f"A tool for '{concept}' already exists or proposal failed. Check `!tools` and `!pending_tools`.")
    except Exception as e:
        await ctx.send(f"Proposal failed: {str(e)[:200]}")


propose_tool._is_command = True
propose_tool.category = "Evolution"


async def pending_proposals(ctx):
    """List Astra's pending code change proposals (Mom, can I get a tattoo?)."""
    from app.core.evolution.proposals import get_pending_proposals
    pending = get_pending_proposals()
    if not pending:
        await ctx.send("No pending code proposals.")
        return
    lines = []
    from app.core.evolution.proposals import load_proposals
    all_p = load_proposals()
    for p in pending:
        idx = next((i for i, x in enumerate(all_p) if x.get("proposed_at") == p.get("proposed_at")), -1)
        lines.append(f"**#{idx}** `{p.get('file_path', '?')}` — {p.get('rationale', '')[:80]}...")
    await ctx.send("**Pending code proposals:**\n" + "\n".join(lines) + "\nUse `!approve_proposal <index>` or `!reject_proposal <index>`.")


pending_proposals._is_command = True
pending_proposals.category = "Evolution"


async def approve_proposal(ctx, index: int):
    """Approve and apply a code proposal by index."""
    from app.core.evolution.proposals import get_proposal_by_index, set_proposal_status
    from app.core.evolution.apply_proposal import apply_proposal
    p = get_proposal_by_index(index)
    if not p:
        await ctx.send(f"No proposal with index {index}.")
        return
    if (p.get("status") or "").lower() != "pending":
        await ctx.send(f"Proposal #{index} is not pending.")
        return
    ok, msg = apply_proposal(p)
    if ok:
        set_proposal_status(index, "approved")
        await ctx.send(f"Approved and applied: {msg}")
    else:
        await ctx.send(f"Apply failed: {msg}")


approve_proposal._is_command = True
approve_proposal.category = "Evolution"


async def reject_proposal(ctx, index: int):
    """Reject a code proposal by index."""
    from app.core.evolution.proposals import set_proposal_status, get_proposal_by_index
    p = get_proposal_by_index(index)
    if not p:
        await ctx.send(f"No proposal with index {index}.")
        return
    set_proposal_status(index, "rejected")
    await ctx.send(f"Rejected proposal #{index}.")


reject_proposal._is_command = True
reject_proposal.category = "Evolution"


async def propose_change(ctx, *, payload: str = ""):
    """Ask Astra to propose a code change. Usage: !propose_change <file_path> <goal> (e.g. !propose_change app/core/evolution/sandbox/echo_astra.py add a greeting)."""
    from app.core.evolution.proposal_generator import generate_and_submit_proposal
    payload = (payload or "").strip()
    if not payload:
        await ctx.send("Usage: `!propose_change <file_path> <goal>`")
        return
    parts = payload.split(None, 1)
    file_path = parts[0]
    goal = parts[1] if len(parts) > 1 else "improve the code"
    result = generate_and_submit_proposal(file_path, goal)
    if result:
        idx, msg = result
        await ctx.send(msg)
    else:
        await ctx.send("Could not generate proposal (file not readable or API error).")
