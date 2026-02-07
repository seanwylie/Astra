# Ollama Flakiness Root Cause Analysis

## Problem
Ollama was producing corrupted output like `;:;:;:;:;:;:;::;:;:;:;:;:;` which was being saved as valid reflections.

## Root Causes Identified

### 1. Silent Exception Handling
**Issue**: The original code caught exceptions but didn't log them, making it impossible to diagnose failures.

**Location**: `app/core/evolution/local_inference.py` lines 125-127, 135-137

**Impact**: When Ollama failed or returned unexpected responses, we had no visibility into what went wrong.

### 2. No Response Validation
**Issue**: The code assumed Ollama responses would always have the expected structure (`data.get("message")` or `data.get("response")`).

**Impact**: Malformed responses (error messages, partial responses, wrong structure) were silently accepted and returned as valid text.

### 3. Missing Error Detection
**Issue**: Ollama can return error responses in the JSON body (e.g., `{"error": "model not found"}`), but the code didn't check for these.

**Impact**: Error messages could be returned as if they were valid model output.

### 4. No Logging
**Issue**: No debug logging to track what was happening during API calls.

**Impact**: Impossible to diagnose issues without adding temporary print statements.

## Fixes Applied

### 1. Comprehensive Logging
- Added debug logs for:
  - Corpus loading
  - API endpoint attempts
  - Response sizes and previews
  - Errors and exceptions
- Added warning logs for:
  - API errors
  - Response parsing failures
  - Timeouts

### 2. Response Validation
- Validate response is a dict before accessing fields
- Check for `error` field in response and raise exception
- Validate `message`/`response` fields exist and are correct types
- Log response structure when validation fails

### 3. Better Error Handling
- Distinguish between timeout, request, and parsing errors
- Store last error for diagnostics (`get_last_inference_error()`)
- Log full error context with stack traces for unexpected errors

### 4. Input Validation (Separate Fix)
- Added `is_valid_reflection()` function in `app/core/processing.py`
- Validates reflections before saving them
- Detects corrupted patterns like `;:;:;:;:;:;:;::;:;:;:;:;:;`
- Rejects invalid reflections and falls back to previous reflection

## Potential Causes of Corrupted Output

Based on the `;:;:;:;:;:;:;::;:;:;:;:;:;` pattern:

1. **Model Confusion**: The model might be outputting internal tokenization patterns when confused by the prompt
2. **Partial Response**: Ollama might be returning a partial/corrupted response due to:
   - Memory pressure
   - Model loading issues
   - Context window overflow
3. **Response Parsing Bug**: Could be extracting wrong field from response (now fixed with validation)
4. **Encoding Issues**: Character encoding problems (less likely given the pattern)

## Next Steps for Diagnosis

With the new logging in place, check logs for:

1. **Ollama API errors**: Look for `[query_local_model] Ollama /api/chat error:` or `/api/generate error:`
2. **Response structure issues**: Look for `response missing 'message' field` or `'response' is not a string`
3. **Timeout issues**: Look for `timeout after 60s`
4. **Model availability**: Check if model name is correct and Ollama can find it

## Output quality (code/SVG-style leakage)

Local model output is validated in `app/core/evolution/local_inference.py` before being returned. If the model emits code, SVG fragments, or technical jargon (e.g. `strokeLine`, `initComponents`), that text is rejected and the response is treated as a failure: callers then fall back to OpenAI. If you see such text in logs (e.g. "Local model output rejected (quality check failed): ..."), the local model produced it and it was correctly discarded in favor of OpenAI.

## Disable flags and config

You can disable local inference globally or per feature without unsetting `OLLAMA_BASE_URL`:

- **Env (recommended):**
  - `OLLAMA_DISABLED=1` — disable local inference for all features (school, dream).
  - `OLLAMA_DISABLE_FOR_SCHOOL=1` — disable only for school reflection (deepen thought).
  - `OLLAMA_DISABLE_FOR_DREAM=1` — disable only for dream seed insight.
  Values `1`, `true`, and `yes` (case-insensitive) enable the disable.

- **Config:** In `general_config.json`, set `local_inference_disabled_for` to a list of scope names, e.g. `["school"]` or `["school", "dream"]`, to disable local inference for those features.

Call sites use `is_local_inference_available(scope)` with `"school"` or `"dream"` so the above flags are respected.

## Stabilization checklist

When Ollama is misbehaving:

1. **Validation:** Ensure validation is on in `local_inference.py` (all responses from `/api/chat` and `/api/generate` go through `is_valid_reflection()`; invalid output returns `None` and triggers fallback).
2. **Disable flags:** Use `OLLAMA_DISABLED=1` or `OLLAMA_DISABLE_FOR_SCHOOL` / `OLLAMA_DISABLE_FOR_DREAM` to force OpenAI for specific features.
3. **Logs:** Check for "Local model output rejected" (quality check) and "Ollama /api/chat error" or "/api/generate error" (API/connectivity).
4. **Connectivity:** Run `PYTHONPATH=. .venv/bin/python scripts/test_local_inference.py` to verify Ollama connectivity and model.

After editing `Modelfile.astra`, rebuild the model so changes take effect: `ollama create astra -f Modelfile.astra` (or your equivalent).

## Testing

To test the fixes:

1. **Check logs**: Run Astra and look for `[query_local_model]` debug messages
2. **Test with invalid model**: Set `OLLAMA_MODEL=nonexistent` and verify error is logged
3. **Monitor for corrupted output**: The validation in `local_inference.py` (and processing) should now catch and reject corrupted reflections
4. **Disable flags**: Set `OLLAMA_DISABLE_FOR_SCHOOL=1` and confirm school reflection uses OpenAI only; same for dream with `OLLAMA_DISABLE_FOR_DREAM=1`

## Related Files

- `app/core/evolution/local_inference.py` - Ollama API client (validation, disable scope, corpus sanitization)
- `app/core/processing.py` - Reflection processing (is_valid_reflection, school call site)
- `app/core/astra_schedule/dream.py` - Dream seed insight (call site with scope "dream")
- `app/core/evolution/corpus_export.py` - Corpus loading (checked, looks fine)
