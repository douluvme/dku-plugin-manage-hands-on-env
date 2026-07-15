# Security

## Credential handling

AWS credentials are **not** stored in this repository. They are supplied at
runtime through a Dataiku parameter set (`aws-credentials`), where the secret
field is typed `PASSWORD` and encrypted at rest by DSS. Runnables read them via
`preset.get("aws_access_key_id")` / `preset.get("aws_secret_access_key")` and
must never print them to logs.

Rules:

- Never hardcode an access key, secret, or token in a `.py` or `.json` file.
- Never `print()` credential values, even at debug level.
- Credentials belong in the DSS preset, not in project or plugin source.

## Incident remediation checklist (June–July 2026)

A set of AWS credentials was previously committed to this repository and printed
in debug logs. Remediation status:

- [x] Move credentials out of source into the `aws-credentials` preset.
- [x] Remove credential prints from the `3-x` runnables.
- [x] Reset git history (single squashed commit; old commits removed from branch).
- [ ] **Rotate / deactivate the exposed access key in AWS IAM.**
      A history reset does not invalidate a key that was already public — forks,
      prior clones, cached commit objects, and old logs may still hold it.
      Rotation in IAM is the only complete remediation. Do this even if the repo
      now looks clean.
- [ ] Confirm no forks exist (GitHub repo → Forks tab).
- [ ] If old commit SHAs are still reachable by direct URL, request that GitHub
      Support purge them rather than waiting for garbage collection.

## Reporting

If you find a credential or other secret committed to this repo, treat the key
as compromised: rotate it first, then remove it from source and history.
