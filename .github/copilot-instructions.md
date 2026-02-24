# GitHub Copilot Instructions — HALO-ELI Project

## What This Project Is

HALO (Honest AI Ledger Operations) is a cryptographic audit layer for AI conversations.
It turns volatile AI interactions into immutable forensic artifacts using:
- **Ed25519 digital signatures** on every receipt
- **Hash chaining** to link conversation turns in tamper-evident sequence
- **ELI (Evidence-Led Inference) schema** to categorize AI claims as FACT, INFERENCE, or OPINION

This is not a chatbot project. It is a compliance and forensic integrity system.
Treat every function that touches signing, hashing, or chain linking as **safety-critical code**.

---

## Project Structure

```
app/
  escrow/
    signing.py        # sign_receipt(), verify_receipt_signature() — do not refactor without review
    chaining.py       # build_chain(), verify_chain() — hash linking logic lives here
    eli.py            # ELI schema enforcement and claim categorization
dist/
  <slug>/
    chain.json        # prev_hash, current_hash for one conversation turn
    receipt.json      # signed artifact for one turn
  master_receipt.json # signed aggregate of all turns in a session
```

---

## Conventions Copilot Must Follow

### Signing
- Always use `sign_receipt()` from `app.escrow.signing` — never roll a custom signing function.
- Always call `verify_receipt_signature()` after writing any receipt to disk. If verification fails, raise immediately — do not silently continue.
- The signing key is loaded from the environment variable `RECEIPT_SIGNING_KEY`. Never hardcode a key. Never log a key. Never pass a key as a function argument directly — always read from env inside the signing module.

### Chaining
- `prev_hash` for turn 1 is always `null`. This is intentional. Do not add a default value.
- `current_hash` is always a SHA-256 hash of the canonical JSON of the unsigned receipt body.
- Chain verification must be done in order. Never verify a subset of turns in isolation and report `chain_valid: true`.
- If any link fails, set `chain_valid: false` and report which turn index broke and why.

### ELI Schema
- Every AI response processed by this system must be tagged before it is signed.
- Valid claim types: `FACT`, `INFERENCE`, `OPINION`.
- A `FACT` must include a `source_hash` field — the SHA-256 of the source document it references. If there is no source, it cannot be tagged FACT. Downgrade it to INFERENCE.
- Never allow an untagged claim to pass through to a signed receipt.

### Receipt Structure
Every receipt must contain these fields before signing:
```json
{
  "type": "...",
  "slug": "...",
  "turn": 0,
  "timestamp_utc": "ISO-8601",
  "content_hash": "sha256-of-content",
  "eli_claims": [],
  "prev_hash": null,
  "current_hash": "..."
}
```
Do not add fields that aren't in this schema without updating the schema documentation first.

### File I/O
- Always write receipts as UTF-8 with `ensure_ascii=False`.
- Always read receipts with `encoding='utf-8'`.
- Never write a receipt file and exit without verifying the written file by re-reading and re-verifying the signature.

---

## What Copilot Must Never Do

- **Never suggest storing plaintext conversation content in a receipt in content_hash_only mode.** In that mode, store only the SHA-256 hash of the content. The plaintext stays in the customer environment.
- **Never suggest hardcoding signing keys**, even as placeholders in tests. Use `os.environ.get('RECEIPT_SIGNING_KEY')` and raise a clear error if it is missing.
- **Never suggest skipping signature verification** for performance or convenience. Verification is not optional.
- **Never suggest mutating a receipt after it has been signed.** If a field needs to change, generate a new receipt with a new timestamp and new signature.
- **Never suggest deleting or overwriting `chain.json` or `receipt.json` files.** These are forensic artifacts. Append or archive — never overwrite.
- **Never suggest logging receipt content to stdout in production paths.** Use structured logging to a separate audit log only.

---

## Testing Standards

- Every function in `app/escrow/` must have a corresponding test that covers the happy path and the tamper-detected path.
- The tamper-detected test must actually mutate a field in a signed receipt and assert that `verify_receipt_signature()` returns `False`.
- Chain tests must cover: single turn (genesis), three-turn valid chain, and a chain with one corrupted link in the middle.
- Use `pytest`. Do not use `unittest` unless an existing test file already uses it.
- Test signing keys must be loaded from environment or a `.env.test` file. Never committed to the repo.

---

## Language and Style

- Python 3.10+
- Type hints on all function signatures in `app/escrow/`
- Docstrings on every public function using this format:
```python
def sign_receipt(payload: dict) -> dict:
    """
    Signs a receipt payload using Ed25519.

    Args:
        payload: Unsigned receipt dict conforming to the HALO receipt schema.

    Returns:
        A new dict with a 'signature' field appended.

    Raises:
        EnvironmentError: If RECEIPT_SIGNING_KEY is not set.
        ValueError: If payload is missing required fields.
    """
```
- No abbreviations in variable names inside `app/escrow/`. `prev_hash` is acceptable (established convention). `ph` is not.

---

## Architecture Decisions — Do Not Suggest Reversing These

| Decision | Reason |
|---|---|
| Ed25519 over RSA | Smaller signatures, faster verification, modern standard |
| SHA-256 for content hashing | Collision resistance, universal support in audit tooling |
| JSON receipts over binary formats | Human-readable for forensic review without tooling |
| UTC timestamps only | No timezone ambiguity in cross-jurisdiction legal contexts |
| Hash-only mode for regulated industries | PHI and privileged content never leaves customer environment |

---

## Glossary

| Term | Meaning |
|---|---|
| Receipt | A signed JSON artifact representing one AI conversation turn |
| Master Receipt | A signed aggregate artifact covering an entire session |
| Chain | The hash-linked sequence of receipts across turns |
| Slug | A unique identifier for one conversation turn, used as the folder name in `dist/` |
| ELI | Evidence-Led Inference — the claim categorization schema |
| Tamper-detected | State where chain verification fails due to hash mismatch |
| Genesis turn | Turn 1, where `prev_hash` is null by design |
