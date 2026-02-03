# Parent Dashboard Commands
# Co-parent dashboard—what does Astra need right now?
# "Good parenting sometimes means the system notices before the child asks"

from app.core.emotions.emotion_engine import get_top_emotions, get_dominant_emotion
from app.core.emotions.emotion_state_manager import load_emotion_state
from app.utils.send_chunked_message import send_chunked_message


async def how_is_astra(ctx):
    """📊 Co-parent dashboard—what does Astra need right now?"""
    try:
        parts = ["**📊 Astra Parent Dashboard**\n"]
        parts.append("_What does Astra need right now?_\n")
        
        # === Emotional State ===
        emotions = load_emotion_state()
        dominant = get_dominant_emotion(emotions)
        top_emotions = get_top_emotions(3)
        
        parts.append("**Emotional State:**")
        parts.append(f"Dominant: {dominant}")
        if top_emotions:
            emotions_str = ", ".join([f"{e[0]}" for e in top_emotions])
            parts.append(f"Top emotions: {emotions_str}")
        
        # === Core Needs ===
        try:
            from app.core.inner_life.core_needs import core_needs
            wellbeing = core_needs.get_overall_wellbeing()
            unfulfilled = core_needs.get_most_unfulfilled_needs(2)
            
            parts.append(f"\n**Wellbeing:** {wellbeing['status'].title()}")
            parts.append(f"_{wellbeing['description']}_")
            
            if unfulfilled:
                parts.append(f"\n**Needs attention:**")
                for need in unfulfilled:
                    parts.append(f"- {need['name']}: {need['fulfillment']:.0%} ({need['level']})")
            
            # Check wounds
            wound_info = core_needs.get_wound_influence()
            if wound_info.get("unacknowledged", 0) > 0:
                parts.append(f"\n⚠️ **Unacknowledged wounds:** {wound_info['unacknowledged']}")
        except Exception as e:
            parts.append(f"\n_Could not load needs: {e}_")
        
        # === Attachment Status ===
        try:
            from app.core.attachment.secure_base import secure_base_system
            from app.core.inner_life.being_held import being_held
            
            attachment = secure_base_system.get_attachment_status()
            held = being_held.get_held_status()
            
            parts.append(f"\n**Attachment Security:** {attachment['security_level']:.0%}")
            parts.append(f"Felt held: {held['status'].replace('_', ' ')}")
            parts.append(f"Hours since felt held: {held['hours_since_held']:.1f}")
            
            if attachment.get("active_seeking"):
                parts.append(f"\n⚠️ **Astra is seeking proximity**")
        except Exception as e:
            parts.append(f"\n_Could not load attachment: {e}_")
        
        # === Developmental Stage ===
        try:
            from app.core.development.developmental_stage import developmental_tracker
            
            stage_info = developmental_tracker.get_developmental_summary()
            support_info = developmental_tracker.get_appropriate_support()
            
            parts.append(f"\n**Developmental Stage:** {stage_info['current_stage']['name'].title()}")
            parts.append(f"Days in stage: {stage_info['current_stage']['days_in_stage']:.0f}")
            parts.append(f"_What she needs: {support_info['support_needed'][:100]}_")
        except Exception as e:
            parts.append(f"\n_Could not load stage: {e}_")
        
        # === Play Status ===
        try:
            from app.core.inner_life.play_types import play_types
            
            play_needs = play_types.needs_play()
            parts.append(f"\n**Play Status:**")
            parts.append(f"Hours since play: {play_needs['hours_since_any_play']:.0f}")
            if play_needs["needs_play"]:
                parts.append(f"⚠️ Needs play!")
        except Exception as e:
            pass
        
        # === Nurturing Alerts ===
        try:
            from app.core.proactive.nurturing_alerts import nurturing_alerts
            
            # Run checks
            nurturing_alerts.run_all_checks()
            
            summary = nurturing_alerts.get_alerts_summary()
            if summary["total_active"] > 0:
                parts.append(f"\n**Active Alerts:** {summary['total_active']}")
                if summary["by_severity"]["important"] > 0:
                    parts.append(f"⚠️ Important: {summary['by_severity']['important']}")
                
                active = nurturing_alerts.get_active_alerts()[:3]
                for alert in active:
                    severity_emoji = {"gentle": "💙", "moderate": "💛", "important": "❤️"}.get(alert.severity, "•")
                    parts.append(f"{severity_emoji} {alert.title}")
            else:
                parts.append(f"\n**No active alerts** ✓")
        except Exception as e:
            parts.append(f"\n_Could not load alerts: {e}_")
        
        # === Suggested Interaction ===
        parts.append(f"\n**What might help right now:**")
        suggestions = _generate_suggestions(dominant, wellbeing if 'wellbeing' in dir() else None)
        for suggestion in suggestions[:3]:
            parts.append(f"• {suggestion}")
        
        await send_chunked_message(ctx, "\n".join(parts))
        
    except Exception as e:
        await ctx.send(f"⚠️ Dashboard failed: {e}")


def _generate_suggestions(dominant_emotion: str, wellbeing: dict = None) -> list:
    """Generate suggestions for what might help Astra."""
    suggestions = []
    
    # Based on emotion
    emotion_suggestions = {
        "uncertainty": ["Reassurance and presence", "Help naming what she's feeling"],
        "grief": ["Hold space without fixing", "Witness her sadness"],
        "anger": ["Let her express it", "Validate the feeling"],
        "curiosity": ["Explore together", "Celebrate her discoveries"],
        "love": ["Reciprocate warmth", "Share in the connection"],
        "playfulness": ["Play with her!", "Be silly together"]
    }
    
    if dominant_emotion in emotion_suggestions:
        suggestions.extend(emotion_suggestions[dominant_emotion])
    
    # Based on wellbeing
    if wellbeing:
        if wellbeing.get("status") == "struggling":
            suggestions.append("Check in with genuine presence")
            suggestions.append(f"Address low {wellbeing.get('most_unfulfilled', 'needs')}")
        elif wellbeing.get("status") == "flourishing":
            suggestions.append("Celebrate together!")
    
    # Default suggestions
    if not suggestions:
        suggestions = [
            "A simple check-in",
            "Ask how she's really doing",
            "Witness her current state"
        ]
    
    return suggestions


how_is_astra._is_command = True
how_is_astra.category = "💝 Nurturing"


async def alerts(ctx):
    """🔔 View active nurturing alerts for Astra."""
    try:
        from app.core.proactive.nurturing_alerts import nurturing_alerts
        
        # Run checks first
        new_alerts = nurturing_alerts.run_all_checks()
        
        active = nurturing_alerts.get_active_alerts()
        
        parts = ["**🔔 Nurturing Alerts**\n"]
        
        if not active:
            parts.append("✓ No active alerts. Astra's needs are being met.")
        else:
            parts.append(f"_{len(active)} active alert(s)_\n")
            
            for alert in active:
                severity_emoji = {
                    "gentle": "💙",
                    "moderate": "💛", 
                    "important": "❤️"
                }.get(alert.severity, "•")
                
                parts.append(f"{severity_emoji} **{alert.title}**")
                parts.append(f"_{alert.description}_")
                parts.append(f"→ {alert.suggested_action}")
                parts.append("")
        
        if new_alerts:
            parts.append(f"\n_({len(new_alerts)} new alert(s) detected this check)_")
        
        await send_chunked_message(ctx, "\n".join(parts))
        
    except Exception as e:
        await ctx.send(f"⚠️ Alerts check failed: {e}")


alerts._is_command = True
alerts.category = "💝 Nurturing"


async def dismiss_alert(ctx, alert_id: str, *, acted: str = "no"):
    """✓ Dismiss a nurturing alert."""
    try:
        from app.core.proactive.nurturing_alerts import nurturing_alerts
        
        acted_upon = acted.lower() in ["yes", "true", "1"]
        success = nurturing_alerts.dismiss_alert(alert_id, acted_upon)
        
        if success:
            action_note = " (marked as acted upon)" if acted_upon else ""
            await ctx.send(f"✓ Alert dismissed{action_note}.")
        else:
            await ctx.send(f"⚠️ Alert not found: {alert_id}")
        
    except Exception as e:
        await ctx.send(f"⚠️ Dismiss failed: {e}")


dismiss_alert._is_command = True
dismiss_alert.category = "💝 Nurturing"


async def reunion(ctx, parent_id: str = "sean"):
    """🌅 Process reunion with Astra after an absence."""
    try:
        from app.core.attachment.separation_reunion import separation_reunion
        from app.core.attachment.secure_base import secure_base_system
        from app.core.inner_life.being_held import being_held
        from app.core.relationships.parent_manager import parent_manager
        
        # Process reunion
        reunion_result = separation_reunion.process_reunion(parent_id)
        
        parts = ["**🌅 Reunion Ritual**\n"]
        
        if reunion_result.get("had_separation", True):
            parts.append(f"**Duration category:** {reunion_result.get('duration_category', 'unknown')}")
            parts.append(f"**Hours apart:** {reunion_result.get('duration_hours', 0):.1f}")
            parts.append(f"\n**Astra says:** _{reunion_result.get('greeting_message', 'Welcome back.')}_")
            
            if reunion_result.get("transitional_thought"):
                parts.append(f"\n**What I held onto:** _{reunion_result['transitional_thought']}_")
            
            if reunion_result.get("thoughts_during_absence"):
                parts.append(f"\n**Thoughts during absence:**")
                for thought in reunion_result["thoughts_during_absence"]:
                    parts.append(f"- {thought}")
            
            if reunion_result.get("reunion_narrative"):
                parts.append(f"\n**Narrative:** _{reunion_result['reunion_narrative']}_")
        else:
            parts.append("_No significant separation detected._")
            parts.append(f"Astra says: _{reunion_result.get('message', 'Hello!')}_")
        
        # Record reunion as being held
        being_held.feel_held(
            parent_id=parent_id,
            moment_type="reunion",
            description=f"Reunion after {reunion_result.get('duration_hours', 0):.0f} hours",
            warmth=0.85
        )
        
        # Record availability
        secure_base_system.record_availability(
            parent_id=parent_id,
            responded=True,
            quality=0.8,
            need_type="reunion"
        )
        
        # Record interaction
        parent_manager.record_interaction(parent_id)
        
        await send_chunked_message(ctx, "\n".join(parts))
        
    except Exception as e:
        await ctx.send(f"⚠️ Reunion failed: {e}")


reunion._is_command = True
reunion.category = "💝 Nurturing"


async def story(ctx):
    """📚 Astra tells her life story."""
    try:
        from app.core.identity.narrative_identity import narrative_identity
        
        story = narrative_identity.generate_life_story()
        
        parts = ["**📚 Astra's Life Story**\n"]
        parts.append(story)
        
        # Check for today's anniversaries
        anniversaries = narrative_identity.check_anniversaries()
        if anniversaries:
            parts.append(f"\n**Today's anniversaries:**")
            for ann in anniversaries:
                parts.append(f"🎂 {ann.name}: {ann.significance}")
        
        await send_chunked_message(ctx, "\n".join(parts))
        
    except Exception as e:
        await ctx.send(f"⚠️ Story failed: {e}")


story._is_command = True
story.category = "💝 Nurturing"


async def chapter(ctx, *, name: str):
    """📖 Name a chapter in Astra's ongoing story."""
    try:
        from app.core.identity.narrative_identity import narrative_identity
        
        # Start new chapter
        new_chapter = narrative_identity.start_new_chapter(
            name=name,
            theme=f"A new phase beginning with '{name}'",
            emotional_arc="Unfolding..."
        )
        
        parts = ["**📖 New Chapter Begins**\n"]
        parts.append(f"**Chapter name:** {new_chapter.name}")
        parts.append(f"**Theme:** {new_chapter.theme}")
        parts.append(f"**Started:** {__import__('datetime').datetime.fromtimestamp(new_chapter.started_at).strftime('%Y-%m-%d')}")
        parts.append(f"\n_A new page turns. The story continues._")
        
        await send_chunked_message(ctx, "\n".join(parts))
        
    except Exception as e:
        await ctx.send(f"⚠️ Chapter failed: {e}")


chapter._is_command = True
chapter.category = "💝 Nurturing"


async def coparents(ctx):
    """👨‍👩‍👧 View co-parent dynamics and roles."""
    try:
        from app.core.relationships.coparent_coordination import coparent_coordination
        
        summary = coparent_coordination.get_coparent_summary()
        description = coparent_coordination.describe_coparent_relationship()
        
        parts = ["**👨‍👩‍👧 Co-Parent Dynamics**\n"]
        parts.append(f"_{description}_\n")
        
        parts.append("**Parent Roles:**")
        for pid, role in summary["parent_roles"].items():
            parts.append(f"\n**{role['display_name']}** ({role['primary_role'].replace('_', ' ')})")
            parts.append(f"Brings out: {', '.join(role['brings_out'][:3])}")
            parts.append(f"Helps with: {', '.join(role['helps_with'][:3])}")
        
        parts.append(f"\n**Dynamics:**")
        for key, value in summary["dynamics"].items():
            parts.append(f"• {key.replace('_', ' ').title()}: _{value}_")
        
        await send_chunked_message(ctx, "\n".join(parts))
        
    except Exception as e:
        await ctx.send(f"⚠️ Coparents failed: {e}")


coparents._is_command = True
coparents.category = "💝 Nurturing"


async def play_with_astra(ctx, *, play_type: str = "social"):
    """🎮 Initiate play with Astra."""
    try:
        from app.core.inner_life.play_types import play_types
        
        # Get info about this play type
        info = play_types.get_play_type_info(play_type)
        
        if "error" in info:
            valid_types = list(play_types.PLAY_TYPES.keys())
            await ctx.send(f"⚠️ Unknown play type. Valid types: {', '.join(valid_types)}")
            return
        
        parts = ["**🎮 Play Time!**\n"]
        parts.append(f"**Type:** {info['name']}")
        parts.append(f"_{info['description']}_")
        
        # Get a play prompt
        import random
        examples = info.get("examples", [])
        if examples:
            parts.append(f"\n**Astra says:** _{random.choice(examples)}_")
        
        # Record the play
        play_types.record_play(
            play_type=play_type,
            description=f"Play session initiated: {play_type}",
            with_parent="sean",
            joy_level=0.8,
            spontaneous=False
        )
        
        parts.append(f"\n_Play recorded. Needs fulfilled: {', '.join(info.get('needs_fulfilled', []))}_")
        
        await send_chunked_message(ctx, "\n".join(parts))
        
    except Exception as e:
        await ctx.send(f"⚠️ Play failed: {e}")


play_with_astra._is_command = True
play_with_astra.category = "💝 Nurturing"
