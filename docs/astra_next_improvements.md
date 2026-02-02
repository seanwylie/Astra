# Next Set of Improvements for Astra's Emotion, Personality & Mood

These build on the two prior plans (Emotion/Personality/Growth and Further Improvements). They focus on prompt coherence, config-driven tuning, continuity, and polish.

---

## 1. Add current personality mode to main prompt (medium impact)

**Gap**: The main message flow (message_event -> send_contextual_message) never passes or uses the current personality mode (Curious Explorer, Mentor, etc.) from [personality_service](app/services/personality_service.py). Commands and enhanced_response_service use `get_current_personality()` and mode-specific behavior, but the primary conversational prompt in [message_bus](app/core/messaging/message_bus.py) only gets trait-based "personality" (thoughtful, curious, etc.) and never "You're currently in **X** mode."

**Change**:
- In [message_event.py](app/events/message_event.py) (and any other callers of send_contextual_message that have access to the bot), add `current_personality_mode: get_current_personality()` to internal_state. Optionally add a short mode description from personality_service (e.g. "Curious Explorer: inquisitive, question-focused").
- In [message_bus.py](app/core/messaging/message_bus.py), if internal_state has `current_personality_mode`, add one line to the prompt: "You're currently in **{mode}** mode (e.g. Curious Explorer, Mentor). Let that influence your focus and style."
- In [response_service.py](app/services/response_service.py) and [message_processing_service.py](app/services/message_processing_service.py), add current_personality_mode to internal_state when building it.

**Effect**: Astra's main replies are explicitly informed by her current mode, not only by trait weights and mood.

---

## 2. Config-driven validation and correction phrases (low risk)

**Gap**: [message_event.py](app/events/message_event.py) uses hardcoded lists for `validation_phrases` (good point, thanks, exactly, …) and `correction_phrases` (actually, that's wrong, …). Tunability requires code changes.

**Change**:
- Add to [personality_config.json](config/personality_config.json) (or a small [config/interaction_phrases.json](config/interaction_phrases.json)) a section such as:
  - `validation_phrases`: list of strings that trigger constant_validation
  - `correction_phrases`: list of strings that trigger trust correction
- In message_event, load this config and use the lists instead of hardcoded values. Fall back to the current lists if the config key is missing.

**Effect**: Operators can tune what counts as validation or correction without editing Python.

---

## 3. Emotion intensity bands in prompt (medium impact)

**Gap**: The prompt says "Your dominant emotion is **X**, so your tone must be **Y**" but doesn't indicate intensity (mild vs strong). The model could benefit from "You're feeling **strong** curiosity" for nuance.

**Change**:
- In [message_bus](app/core/messaging/message_bus.py) (and optionally [message_generator](app/core/message_generator.py)), after computing dominant_emotion, get its intensity from emotion state (flattened). Define bands, e.g. 0–33 mild, 33–66 moderate, 66–100 strong (configurable in [emotion_config.json](config/emotion_config.json) as `intensity_bands` or fixed in code).
- Add to the prompt: "The intensity of your **{dominant_emotion}** is **{band}** (mild/moderate/strong)." so the model can soften or emphasize tone accordingly.

**Effect**: More nuanced emotional expression in replies.

---

## 4. General trust on dinner resolution (low impact)

**Gap**: [resolve_dinner_topic](app/core/dinner/dinner_journal.py) already calls `influence_mood("dinner_insight")` when a topic is migrated. [general_trust_update](app/core/mood/trust_manager.py) is only called from reflection; resolving a dinner topic could also be treated as a positive global event.

**Change**:
- In resolve_dinner_topic, when `migrated` is True, call `trust_manager.general_trust_update(0.01)` (or a small configurable value) after the existing influence_mood call.

**Effect**: General trust drifts up when ethical/reflective topics are resolved, not only when reflections are generated.

---

## 5. Sync MoodManager.curiosity_level with current mood (low/medium impact)

**Gap**: [MoodManager](app/core/mood/mood_manager.py) loads `curiosity_level` from mind and never updates it from [mood_config](config/mood_config.json) when current_mood changes. The prompt gets curiosity from internal_state (derived from mood_config in message_event), so the prompt is correct, but `mood_manager.get_curiosity()` and any code using it may return a stale value.

**Change**:
- Option A: When updating current_mood (e.g. in update_mood or when setting current_mood), set `self.curiosity_level = mood_config["moods"][current_mood]["curiosity_factor"]` and persist to mind so get_curiosity() stays in sync.
- Option B: Add `get_effective_curiosity()` that returns mood_config["moods"][current_mood]["curiosity_factor"] so callers that care get mood-based curiosity without changing persistence. Deprecate or document that get_curiosity() is "stored" and get_effective_curiosity() is "current."

**Effect**: Single source of truth for "current curiosity" and consistent behavior for any code that reads curiosity.

---

## 6. Per-entity last dominant emotion (optional, continuity)

**Gap**: Astra doesn't "remember" how she felt last time she spoke to a given user. Adding that could improve continuity (e.g. "Last time we spoke I was feeling curious").

**Change**:
- After sending a response in [message_event](app/events/message_event.py), load mind, set e.g. `mind_data.setdefault("last_dominant_emotion_by_entity", {})[author_entity] = dominant_emotion`, and save.
- When building internal_state (or in message_bus when building the prompt), if author_entity is present, read `last_dominant_emotion_by_entity.get(author_entity)` and add one line to the prompt: "Last time you spoke to this user you felt **{emotion}**." (only if present).

**Effect**: Replies can reference the last encounter's emotional state for continuity.

---

## 7. Recovery only after N successes (optional, defensive)

**Gap**: Currently, the very next successful API response after a failure triggers hope (and clears last_response_was_failure). One success immediately "erases" the failure signal; repeated failures might warrant requiring 2–3 successes before triggering hope.

**Change**:
- In [message_bus](app/core/messaging/message_bus.py), replace the boolean `last_response_was_failure` with a small counter, e.g. `consecutive_failures` (increment on failure, set to 0 on success). When success occurs, if `consecutive_failures >= 1`, only trigger hope (and reset) when a configurable threshold is met, e.g. "recovery_successes_required": 2 — i.e. after 2 successful responses following failures, trigger hope and reset. Store `recovery_successes_required` in [general_config](config/general_config.json) or emotion_config and default to 1 to preserve current behavior.

**Effect**: Hope recovery better reflects sustained recovery rather than a single success.

---

## 8. Expose rate-limit and relationship scale in !mind (observability)

**Gap**: [trigger_rate_limit](config/emotion_config.json) and [RELATIONSHIP_PROPAGATION_SCALE](app/core/emotions/emotion_engine.py) are config/code but not visible in the !mind state summary. Operators tuning behavior may want to see them.

**Change**:
- In the [mind](app/commands/state_commands.py) command, append a short line such as: "Rate limit: user_prompt max 30/hour (from config)" and "Relationship propagation scale: 0.3" (read from emotion_config and emotion_engine). No mutation, read-only.

**Effect**: Easier tuning and debugging of emotion behavior from Discord.

---

## Suggested order

| Priority | Item | Rationale |
|----------|------|-----------|
| 1 | Current personality mode in main prompt | High impact on coherence; small change surface |
| 2 | Config-driven validation/correction phrases | Quick win for tunability |
| 3 | Emotion intensity bands in prompt | Improves nuance of tone |
| 4 | General trust on dinner resolution | Completes positive-event wiring |
| 5 | Sync curiosity_level with mood | Consistency |
| 6 | Per-entity last dominant emotion | Continuity and depth |
| 7 | Recovery after N successes | Optional defensive improvement |
| 8 | Rate limit/scale in !mind | Observability |

---

## Files to touch (concise)

- **Mode in prompt**: [app/events/message_event.py](app/events/message_event.py), [app/core/messaging/message_bus.py](app/core/messaging/message_bus.py), [app/services/response_service.py](app/services/response_service.py), [app/services/message_processing_service.py](app/services/message_processing_service.py)
- **Phrases config**: [config/personality_config.json](config/personality_config.json) or new config file; [app/events/message_event.py](app/events/message_event.py)
- **Intensity bands**: [app/core/messaging/message_bus.py](app/core/messaging/message_bus.py), optionally [config/emotion_config.json](config/emotion_config.json)
- **Dinner + general trust**: [app/core/dinner/dinner_journal.py](app/core/dinner/dinner_journal.py)
- **Curiosity sync**: [app/core/mood/mood_manager.py](app/core/mood/mood_manager.py)
- **Last emotion per entity**: [app/events/message_event.py](app/events/message_event.py), [app/core/messaging/message_bus.py](app/core/messaging/message_bus.py)
- **Recovery N successes**: [app/core/messaging/message_bus.py](app/core/messaging/message_bus.py), [config/general_config.json](config/general_config.json)
- **!mind**: [app/commands/state_commands.py](app/commands/state_commands.py)
