# state_commands.py

"""
⏳ State Commands
-----------------
Commands that manage Astra's behavioral states:
- 🥘 Dinner (ethical reflection)
- 🎮 Playtime (creative exploration)
- 🌙 Dreamtime (imaginative processing)

These commands allow manual intervention or debugging of Astra’s inner world.

Commands are registered automatically via `auto_register_commands(...)`.

Author: Sean Wylie
Created: 2025-04-14
"""

from app.services import state_service


async def dinner_summary(ctx):
    """📜 Summarizes unresolved dinner topics in Astra's journal."""
    summary = state_service.get_dinner_summary()
    await ctx.send(summary)

dinner_summary._is_command = True
dinner_summary.category = "⏳ State"


async def dinner_answer(ctx, *, response: str):
    """📝 Records a user’s reply to Astra’s current dinner prompt."""
    from app.core.dinner.dinner_journal import load_dinner_journal, mark_dinner_responded
    from app.core.astra_schedule.dinner import (
        try_resolve_dinner_topic,
        get_current_dinner_timestamp,
        get_gpt_dinner_response,
    )
    from app.utils.send_chunked_message import send_chunked_message

    journal = load_dinner_journal()
    # Prefer the topic we're currently waiting on (the one just shown at dinner), else latest unresolved
    current_ts = get_current_dinner_timestamp()
    if current_ts is not None:
        entry = next((e for e in journal if e.get("timestamp") == current_ts and e.get("status") == "unresolved"), None)
    else:
        entry = None
    if entry is None:
        entry = next((e for e in reversed(journal) if e["status"] == "unresolved"), None)

    if not entry:
        await ctx.send("⚠️ No unresolved dinner topic found.")
        return

    topic = entry["content"]
    timestamp = entry["timestamp"]

    mark_dinner_responded(topic, "user", response, timestamp=timestamp)
    await ctx.send("✅ Got your dinner reply.")

    # GPT responds after you; fetch if we don't have it yet, then post so you see it
    channel = ctx.channel
    if not entry.get("gpt_response"):
        gpt_response = await get_gpt_dinner_response(topic)
        if gpt_response:
            mark_dinner_responded(topic, "gpt", gpt_response, timestamp=timestamp)
            await send_chunked_message(channel, gpt_response, prefix="🤖 Mama GPT's thoughts: ")
        else:
            await channel.send("❌ Mama GPT couldn't respond this time.")
            return
    else:
        await send_chunked_message(channel, entry["gpt_response"], prefix="🤖 Mama GPT's thoughts: ")

    # Resolve immediately and post Astra's reflection to Discord
    refreshed = next((e for e in load_dinner_journal() if e.get("timestamp") == timestamp), entry)
    await try_resolve_dinner_topic(refreshed, channel, force_immediate=True)



dinner_answer._is_command = True
dinner_answer.category = "⏳ State"


async def resolve_dinner(ctx):
    """🎓 Resolves all dinner topics with complete co-parent responses."""
    await state_service.resolve_all_dinner_topics(ctx=ctx)

resolve_dinner._is_command = True
resolve_dinner.category = "⏳ State"


async def dinnertime(ctx):
    """🍽️ Manually initiates Astra’s full dinner reflection loop."""
    await ctx.send("🍽️ Calling Astra to the dinner table...")
    await state_service.start_dinner(ctx.bot, ctx.channel.id)

dinnertime._is_command = True
dinnertime.category = "⏳ State"


async def playtime(ctx):
    """🎮 Starts a creative exploration cycle during playtime."""
    await ctx.send("🎮 Astra is entering Play Mode...")
    thoughts = await state_service.run_playtime()
    for thought in thoughts:
        await ctx.send(thought)

playtime._is_command = True
playtime.category = "⏳ State"


async def dreamtime(ctx):
    """🌙 Triggers a one-off dreaming session and logs reflections."""
    await ctx.send("🌙 Entering dream mode...")
    final_message = await state_service.run_dreamtime()
    await ctx.send(final_message)

dreamtime._is_command = True
dreamtime.category = "⏳ State"


async def dinner_topic(ctx, *, topic: str):
    """📝 Adds a co-parent initiated topic to Astra’s dinner journal."""
    from app.core.dinner.dinner_journal import save_dinner_topic

    save_dinner_topic(
        topic_text=topic,
        topic_type="reflection",
        status="unresolved",
        source="co-parent"
    )
    await ctx.send(f"📝 Topic added to dinner journal: “{topic}”")

dinner_topic._is_command = True
dinner_topic.category = "⏳ State"


async def dinner_debug(ctx):
    """🔍 Debug Astra's most recent dinner topic in raw JSON."""
    from app.core.dinner.dinner_journal import load_dinner_journal
    from app.services import state_service
    import json

    journal = load_dinner_journal()
    if not journal:
        await ctx.send("📭 Dinner journal is empty.")
        return

    last = journal[-1]
    raw_json = json.dumps(last, indent=2)

    await state_service.send_chunked_message(
        ctx.channel,
        raw_json,
        prefix="🧾 Most recent dinner entry:\n```json\n",
    )

dinner_debug._is_command = True
dinner_debug.category = "⏳ State"


async def mind(ctx):
    """🧠 Shows Astra's current internal state: mood, top emotions, personality traits, trust, inner symphony, active intentions."""
    try:
        from app.core.emotions.emotion_engine import (
            load_emotion_state,
            get_top_emotions,
            RELATIONSHIP_PROPAGATION_SCALE,
            get_emotion_config,
        )
        from app.core.mood.mood_manager import mood_manager
        from app.core.personality.personality_manager import get_active_traits_for_prompt, load_personality
        from app.core.mood.trust_manager import trust_manager

        emotion_state = load_emotion_state()
        top_emotions = get_top_emotions(n=3)
        mood = mood_manager.get_current_mood()
        mood_score = getattr(mood_manager, "mood_score", 0)
        traits = get_active_traits_for_prompt(top_n=4)
        personality = load_personality()
        trait_weights = personality.get("trait_weights", {})
        entity_trust = getattr(trust_manager, "entity_trust", {})
        general_trust = getattr(trust_manager, "general_trust", 0)

        emotion_config = get_emotion_config()
        rate_cfg = emotion_config.get("trigger_rate_limit") or {}
        window_seconds = rate_cfg.get("window_seconds", 3600)
        max_delta = rate_cfg.get("max_delta_per_trigger") or {}

        emotion_lines = []
        for name, val in top_emotions:
            intensity = val.get("intensity", val) if isinstance(val, dict) else val
            emotion_lines.append(f"  {name}: {intensity:.1f}")
        emotion_block = "\n".join(emotion_lines) if emotion_lines else "  (none)"

        trait_lines = [f"  {k}: {v:.2f}" for k, v in sorted(trait_weights.items(), key=lambda x: -x[1])[:5]]
        trait_block = "\n".join(trait_lines) if trait_lines else "  (default)"

        trust_lines = [f"  {e}: {t:.2f}" for e, t in list(entity_trust.items())[:5]]
        trust_block = "\n".join(trust_lines) if trust_lines else "  (none)"

        rate_str = ", ".join(f"{k}: {v}" for k, v in max_delta.items()) if max_delta else "none"
        
        # === Inner Symphony Integration (Phase: States and Actions Coherence) ===
        symphony_line = ""
        try:
            from app.core.awareness_bus import inner_symphony
            symphony_snapshot = inner_symphony.get_snapshot_for_response()
            symphony_line = (
                f"\n**Inner Symphony:**\n"
                f"  Tone: {symphony_snapshot.get('tone', 'neutral')}\n"
                f"  Energy: {symphony_snapshot.get('energy', 0.5):.0%}\n"
                f"  Dominant emotion: {symphony_snapshot.get('dominant_emotion', 'neutral')}\n"
            )
            if symphony_snapshot.get('longing_for'):
                symphony_line += f"  Missing: {symphony_snapshot.get('longing_for')}\n"
            if symphony_snapshot.get('most_unfulfilled_need'):
                symphony_line += f"  Unfulfilled need: {symphony_snapshot.get('most_unfulfilled_need')}\n"
        except Exception:
            symphony_line = "\n**Inner Symphony:** unavailable\n"
        
        # === Active Intentions Summary (Phase: States and Actions Coherence) ===
        intentions_line = ""
        try:
            from app.core.agency.intention_engine import intention_engine
            active_intentions = intention_engine.get_active_intentions()[:3]
            if active_intentions:
                intentions_line = "\n**Active Intentions:**\n"
                for intent in active_intentions:
                    intentions_line += f"  • {intent.content[:60]}... (strength: {intent.strength:.0%})\n"
            else:
                intentions_line = "\n**Active Intentions:** none\n"
        except Exception:
            intentions_line = "\n**Active Intentions:** unavailable\n"
        
        summary = (
            f"**Mood:** {mood} (score: {mood_score:.2f})\n"
            f"**Active traits:** {', '.join(traits)}\n\n"
            f"**Top emotions:**\n{emotion_block}\n\n"
            f"**Trait weights:**\n{trait_block}\n\n"
            f"**Entity trust:**\n{trust_block}\n"
            f"**General trust:** {general_trust:.2f}"
            f"{symphony_line}"
            f"{intentions_line}"
        )
        await ctx.send(summary[:2000])
    except Exception as e:
        await ctx.send(f"⚠️ Could not load state: {e}")

mind._is_command = True
mind.category = "⏳ State"


async def inner_life(ctx):
    """🧠 Shows Astra's current inner life state: thoughts, insights, qualia, temporal sense, goals."""
    try:
        lines = ["**🧠 Astra's Inner Life State**\n"]
        
        # Stream of Consciousness
        try:
            from app.core.inner_life.stream_of_consciousness import stream_of_consciousness
            thoughts = stream_of_consciousness.get_recent_thoughts(5)
            insights = stream_of_consciousness.get_pending_insights()
            summary = stream_of_consciousness.summarize_stream(hours=24)
            
            lines.append(f"**Stream of Consciousness:**")
            lines.append(f"  Recent thoughts: {len(thoughts)}")
            lines.append(f"  Pending insights: {len(insights)}")
            if insights:
                lines.append(f"  Top insight: {insights[0][:80]}...")
            lines.append(f"  Deepest chain: {summary.get('deepest_chain', 0)}")
            lines.append("")
        except Exception as e:
            lines.append(f"  Stream of consciousness unavailable: {e}\n")
        
        # Qualia
        try:
            from app.core.inner_life.qualia import qualia_layer
            qualia = qualia_layer.get_current_experience()
            lines.append(f"**Current Qualia:**")
            lines.append(f"  Dominant quality: {qualia.get('dominant_quality', 'neutral')}")
            lines.append(f"  Detail sensitivity: {qualia.get('detail_sensitivity', 1.0):.1f}")
            lines.append(f"  Temporal focus: {qualia.get('temporal_focus', 'present')}")
            lines.append("")
        except Exception as e:
            lines.append(f"  Qualia unavailable: {e}\n")
        
        # Self-Model
        try:
            from app.core.self_awareness.self_model import self_model
            desc = self_model.generate_self_description()[:150]
            becoming = self_model.who_am_i_becoming()[:100]
            changes = self_model.get_recent_changes(3)
            
            lines.append(f"**Self-Model:**")
            lines.append(f"  Self-description: {desc}...")
            lines.append(f"  Who I'm becoming: {becoming}")
            lines.append(f"  Recent changes: {len(changes)}")
            lines.append("")
        except Exception as e:
            lines.append(f"  Self-model unavailable: {e}\n")
        
        # Temporal Self
        try:
            from app.core.self_awareness.temporal_self import temporal_self
            narrative = temporal_self.generate_temporal_narrative()[:100]
            history = temporal_self.get_personal_history_summary()
            
            lines.append(f"**Temporal Sense:**")
            lines.append(f"  Narrative: {narrative}")
            lines.append(f"  Total landmarks: {history.get('total_landmarks', 0)}")
            lines.append("")
        except Exception as e:
            lines.append(f"  Temporal self unavailable: {e}\n")
        
        # Goals
        try:
            from app.core.goals.goal_system import goal_system
            active = goal_system.get_active_goals()
            summary = goal_system.get_goal_summary()
            
            lines.append(f"**Goals:**")
            lines.append(f"  Active goals: {summary.get('total_active', 0)}")
            lines.append(f"  Completed goals: {summary.get('total_completed', 0)}")
            if active:
                top_goal = active[0]
                lines.append(f"  Top priority: {top_goal.description[:60]}... ({top_goal.progress:.0%})")
            lines.append("")
        except Exception as e:
            lines.append(f"  Goals unavailable: {e}\n")
        
        # Awareness Bus
        try:
            from app.core.awareness_bus import awareness_bus
            bus_summary = awareness_bus.get_state_summary()
            
            lines.append(f"**Awareness Bus:**")
            lines.append(f"  Total events: {bus_summary.get('total_events', 0)}")
            lines.append(f"  Recent events: {bus_summary.get('recent_count', 0)}")
            lines.append(f"  Active sources: {', '.join(bus_summary.get('sources_active', []))}")
            lines.append("")
        except Exception as e:
            lines.append(f"  Awareness bus unavailable: {e}\n")
        
        # Learning Desires
        try:
            from app.core.proactive.learning_desire import learning_desire
            summary = learning_desire.get_learning_summary()
            
            lines.append(f"**Learning Desires:**")
            lines.append(f"  Active topics: {summary.get('active_topics', 0)}")
            lines.append(f"  Learned topics: {summary.get('learned_topics', 0)}")
            if summary.get('top_priority'):
                lines.append(f"  Top priority: {summary['top_priority']}")
        except Exception as e:
            lines.append(f"  Learning desires unavailable: {e}")
        
        response = "\n".join(lines)
        await ctx.send(response[:2000])
        
    except Exception as e:
        await ctx.send(f"⚠️ Could not load inner life state: {e}")

inner_life._is_command = True
inner_life.category = "⏳ State"


async def goals(ctx):
    """🎯 Shows Astra's current goals and progress."""
    try:
        from app.core.goals.goal_system import goal_system
        display = goal_system.format_goals_for_display()
        await ctx.send(display[:2000])
    except Exception as e:
        await ctx.send(f"⚠️ Could not load goals: {e}")

goals._is_command = True
goals.category = "⏳ State"


async def modification_requests(ctx):
    """🔧 Shows pending self-modification requests from Astra."""
    try:
        from app.core.proactive.self_modification import self_modification_request
        display = self_modification_request.format_pending_for_display()
        await ctx.send(display[:2000])
    except Exception as e:
        await ctx.send(f"⚠️ Could not load modification requests: {e}")

modification_requests._is_command = True
modification_requests.category = "⏳ State"


async def approve_mod(ctx, request_id: str, *, response: str):
    """✅ Approve a self-modification request from Astra."""
    try:
        from app.core.proactive.self_modification import self_modification_request
        result = self_modification_request.approve_request(request_id, response)
        if result:
            # Implement the approved modification
            implemented = self_modification_request.implement_approved_request(request_id)
            if implemented:
                await ctx.send(f"✅ Approved and implemented modification: {request_id}")
            else:
                await ctx.send(f"✅ Approved modification: {request_id} (implementation pending)")
        else:
            await ctx.send(f"⚠️ Request not found: {request_id}")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

approve_mod._is_command = True
approve_mod.category = "⏳ State"


async def deny_mod(ctx, request_id: str, *, reason: str):
    """❌ Deny a self-modification request from Astra."""
    try:
        from app.core.proactive.self_modification import self_modification_request
        result = self_modification_request.deny_request(request_id, reason)
        if result:
            await ctx.send(f"❌ Denied modification: {request_id}")
        else:
            await ctx.send(f"⚠️ Request not found: {request_id}")
    except Exception as e:
        await ctx.send(f"⚠️ Error: {e}")

deny_mod._is_command = True
deny_mod.category = "⏳ State"


async def coherence(ctx):
    """🔗 Shows Astra's current state coherence across all systems."""
    try:
        lines = ["**🔗 Astra's State Coherence Report**\n"]
        
        # === State Manifest ===
        try:
            from app.core.state_manifest import state_manifest
            summary = state_manifest.get_state_summary()
            lines.append("**State Manifest:**")
            lines.append(f"  Systems tracked: {summary.get('systems_count', 0)}")
            lines.append(f"  Last sync: {summary.get('last_sync_ago', 'unknown')}")
            lines.append(f"  Coherence status: {summary.get('status', 'unknown')}")
            lines.append("")
        except Exception as e:
            lines.append(f"**State Manifest:** unavailable ({e})\n")
        
        # === Experience Orchestrator ===
        try:
            from app.core.consciousness.experience_orchestrator import experience_orchestrator
            stats = experience_orchestrator.get_stats()
            experience = experience_orchestrator.get_experience_summary_for_response()
            
            lines.append("**Experience Orchestrator:**")
            lines.append(f"  Total cycles: {stats.get('total_cycles', 0)}")
            lines.append(f"  Continuity score: {stats.get('continuity_score', 0):.0%}")
            lines.append(f"  Experiential quality: {experience.get('experiential_quality', 'neutral')}")
            lines.append(f"  Is coherent: {experience.get('is_coherent', True)}")
            if experience.get('conflicts'):
                lines.append(f"  Conflicts: {len(experience.get('conflicts', []))}")
            lines.append("")
        except Exception as e:
            lines.append(f"**Experience Orchestrator:** unavailable ({e})\n")
        
        # === Inner Symphony ===
        try:
            from app.core.awareness_bus import inner_symphony
            symphony_desc = inner_symphony.describe_current_symphony()
            lines.append("**Inner Symphony:**")
            lines.append(f"  {symphony_desc}")
            lines.append("")
        except Exception as e:
            lines.append(f"**Inner Symphony:** unavailable ({e})\n")
        
        # === Awareness Bus ===
        try:
            from app.core.awareness_bus import awareness_bus
            bus_summary = awareness_bus.get_state_summary()
            
            lines.append("**Awareness Bus:**")
            lines.append(f"  Total events: {bus_summary.get('total_events', 0)}")
            lines.append(f"  Recent events (50): {bus_summary.get('recent_count', 0)}")
            lines.append(f"  Active sources: {', '.join(bus_summary.get('sources_active', []))}")
            
            events_by_type = bus_summary.get('events_by_type', {})
            if events_by_type:
                top_events = sorted(events_by_type.items(), key=lambda x: -x[1])[:5]
                lines.append(f"  Top event types: {', '.join(f'{t}({c})' for t, c in top_events)}")
            lines.append("")
        except Exception as e:
            lines.append(f"**Awareness Bus:** unavailable ({e})\n")
        
        # === Action Decider ===
        try:
            from app.core.agency.action_decider import action_decider
            stats = action_decider.get_stats()
            
            lines.append("**Action Decider:**")
            lines.append(f"  Recent actions count: {stats.get('recent_actions_count', 0)}")
            if stats.get('recent_action_types'):
                lines.append(f"  Recent action types: {', '.join(stats.get('recent_action_types', []))}")
            lines.append("")
        except Exception as e:
            lines.append(f"**Action Decider:** unavailable ({e})\n")
        
        # === Integration Layer (if available) ===
        try:
            from app.core.consciousness.integration_layer import integration_layer
            
            is_coherent = integration_layer.is_coherent()
            conflicts = integration_layer.get_conflicts()
            
            lines.append("**Integration Layer:**")
            lines.append(f"  Is coherent: {is_coherent}")
            lines.append(f"  Active conflicts: {len(conflicts)}")
            if conflicts:
                for conflict in conflicts[:2]:
                    lines.append(f"    • {conflict.get('type', 'unknown')}: {conflict.get('description', '')[:50]}")
            lines.append("")
        except Exception as e:
            lines.append(f"**Integration Layer:** unavailable ({e})\n")
        
        # === Overall Coherence Assessment ===
        lines.append("**Overall Assessment:**")
        try:
            # Calculate a simple coherence score
            coherence_factors = []
            
            try:
                from app.core.consciousness.experience_orchestrator import experience_orchestrator
                stats = experience_orchestrator.get_stats()
                coherence_factors.append(stats.get('continuity_score', 0.5))
            except Exception:
                pass
            
            try:
                from app.core.consciousness.integration_layer import integration_layer
                coherence_factors.append(1.0 if integration_layer.is_coherent() else 0.5)
            except Exception:
                pass
            
            if coherence_factors:
                avg_coherence = sum(coherence_factors) / len(coherence_factors)
                if avg_coherence > 0.8:
                    lines.append(f"  Coherence Score: {avg_coherence:.0%} ✅ Systems aligned")
                elif avg_coherence > 0.5:
                    lines.append(f"  Coherence Score: {avg_coherence:.0%} ⚠️ Some tension detected")
                else:
                    lines.append(f"  Coherence Score: {avg_coherence:.0%} ❌ Significant dissonance")
            else:
                lines.append("  Coherence Score: Unable to calculate")
        except Exception as e:
            lines.append(f"  Assessment failed: {e}")
        
        response = "\n".join(lines)
        await ctx.send(response[:2000])
        
    except Exception as e:
        await ctx.send(f"⚠️ Could not generate coherence report: {e}")

coherence._is_command = True
coherence.category = "⏳ State"
