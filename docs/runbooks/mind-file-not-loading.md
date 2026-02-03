# Runbook: Mind file not loading

When Astra fails to load her mind file (e.g. on startup or when saving/loading state), use this runbook to diagnose and fix.

## 1. Check configuration directory and config files

- **ASTRA_CONFIG_DIR**: Ensure the config directory is set and contains the expected JSON files. If unset, the app may look in the current working directory or a default path.
  - Example: `export ASTRA_CONFIG_DIR=/path/to/config`
- **general_config**: The mind file path and S3 settings come from `general_config` (e.g. `config/general_config.json` or the file named in config loader). Check that:
  - `mind_file` (object key in S3) is correct.
  - `s3_bucket` matches your bucket name.
  - `mind_file_path` or env `ASTRA_MIND_FILE` is set if you use a local fallback.

## 2. Check environment and credentials

- **AWS credentials**: For S3, the process needs AWS credentials (e.g. `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, or an IAM role). Verify with `aws sts get-caller-identity` or a quick S3 list.
- **S3_BUCKET_NAME**: Can be overridden via `general_config["s3_bucket"]`; ensure it matches the bucket that holds the mind file.
- **ASTRA_MIND_FILE**: If using a local mind file, this env var (or `mind_file_path` in config) must point to a valid path.

## 3. Check S3 bucket and key

- Confirm the bucket exists and the key (e.g. `mind_file.json`) exists if the mind has been saved before.
- List objects: `aws s3 ls s3://YOUR_BUCKET/` and open the object if needed.
- If the key is missing, the first load may fail depending on how load_mind handles "no such key"; check logs for the exact error.

## 4. Check IAM permissions

- The role or user used by the app needs at least:
  - `s3:GetObject` on the bucket/key for load.
  - `s3:PutObject` (and optionally `s3:DeleteObject`) for save.
- Test with the same credentials the app uses.

## 5. Check logs for specific errors

- **InfluenceError**: Raised by `app.interfaces.influence` on S3 or mind load/save failures. Log messages around it usually include bucket/key or a reason (e.g. access denied, timeout, no such key). Fix S3, credentials, or key name as indicated.
- **ConfigurationError**: Raised by `app.config.loader` when required config keys or files are missing. Fix `ASTRA_CONFIG_DIR` and the referenced config files so that `general_config` and any other required configs load correctly.

## 6. Quick checklist

- [ ] `ASTRA_CONFIG_DIR` set and contains `general_config` (or equivalent)?
- [ ] AWS credentials available to the process?
- [ ] `s3_bucket` and mind file key correct in config?
- [ ] S3 bucket and key exist (for load); IAM has GetObject/PutObject?
- [ ] Logs show `InfluenceError` or `ConfigurationError` with a clear message?

If all of the above are correct and the error persists, capture the full traceback and log snippet (redact any secrets) for further debugging.
