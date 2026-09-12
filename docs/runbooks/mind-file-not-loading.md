# Runbook: Mind file not loading

When Astra fails to load a mind file on startup or on save/load, use this runbook.

The default path is **local**. S3 is opt-in. An empty `s3_bucket` and
`s3_sync_enabled: false` (the shipped defaults) mean Astra does not talk to AWS.

## 1. Check the local mind path

- **ASTRA_MIND_FILE**: Overrides the mind file path. The shipped default is
  `fixtures/example_mind.json`.
- Confirm the file exists and is readable JSON.
- Do not point this at a live operator mind if you are only trying to start
  the engine.

## 2. Check configuration directory

- **ASTRA_CONFIG_DIR**: Must point at the directory with the JSON configs. If
  unset, the app uses `config/` under the repo.
- **general_config**: `mind_file_path` / `ASTRA_MIND_FILE` is the local path.
  `s3_bucket` and `s3_sync_enabled` apply only if you turned S3 on.

## 3. Only if S3 sync is enabled

Skip this section unless `s3_sync_enabled` is true and a bucket name is set.

- AWS credentials must be available to the process.
- `S3_BUCKET_NAME` or `general_config["s3_bucket"]` must match that bucket.
- The object key (for example `mind_file.json`) must exist if you expect a load.
- IAM needs `s3:GetObject` to load and `s3:PutObject` to save.

## 4. Check logs

- **InfluenceError**: S3 or mind load/save failed. The log usually names the
  path, bucket/key, or reason.
- **ConfigurationError**: Required config keys or files are missing. Fix
  `ASTRA_CONFIG_DIR` and the referenced JSON files.

## 5. Quick checklist

- [ ] `ASTRA_MIND_FILE` (or the default fixture) exists and is valid JSON?
- [ ] `ASTRA_CONFIG_DIR` points at the config directory?
- [ ] S3 still off unless you meant to enable it?
- [ ] If S3 is on: credentials, bucket, key, and IAM match?
- [ ] Logs show `InfluenceError` or `ConfigurationError` with a clear message?

If the error persists, capture the traceback (redact secrets) before going further.
