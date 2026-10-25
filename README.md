# validation-claim-audit

Offline, stdlib-only auditor for documented input-checking promises in
Python projects. It reads a project's docs and its Python source, and
reports when a documented checking promise does not match the code.
It executes nothing, uses no network, and never reads `.env` contents.

## Why

Docs that promise input is checked before use, while the code passes
user data straight through, fail only on the first hostile or malformed
input — the author's own fixtures are always well-formed. The reverse is
just as silent: docs that promise unchecked handling, while the code
rejects malformed input, surprise the first user who relied on
pass-through behaviour. A successful run looks identical either way, so
no test fails on the broken promise.

## Usage

```sh
pip install validation-claim-audit
validation-claim-audit /path/to/project
validation-claim-audit /path/to/project --json
validation-claim-audit /path/to/project --fail-on HIGH
validation-claim-audit /path/to/project --ignore "vendor/*"
```

Exit codes: `0` PASS, `2` FAIL, `1` usage error. `--fail-on HIGH` makes
a MEDIUM-only run exit `0` while still printing the MEDIUM findings.

## How it works

Claim sources are the root `README.md` plus `docs/**/*.md`. Fenced code
blocks are excluded from claims; inline code spans count as prose.
Production Python source excludes `tests/`, `fixtures/`, `docs/`,
`examples/`, `test_*.py`, `*_test.py`, and symlinked files. Checking
evidence found only under tests or fixtures yields MEDIUM findings.

Checking evidence is: imports of a checking library, a checking call, a
checking decorator, a model class built on a checking base, or a
schema-object load call. Hand-rolled guards with no checking name do not
count — see Limitations.

## Rules

The exact claim phrases and rule names are listed only in the fenced
block below, so that auditing this tool's own tree passes with no
claims. Prose in this README deliberately paraphrases them.

```
Claim families: checked-promise family, unchecked-promise family.
Rules:
  documented-validated-claim-false (HIGH)
  documented-validated-claim-false-test-only (MEDIUM)
  documented-unvalidated-claim-false (HIGH)
  documented-unvalidated-claim-false-test-only (MEDIUM)
Claim phrases (checked family):
  "validates input", "validates all input", "validates inputs",
  "validates user input", "validates data", "validates requests",
  "validates arguments", "validates parameters", "input validation",
  "all input is validated", "inputs are validated", "validated input",
  "validated inputs", "with input validation", "performs validation"
Claim phrases (unchecked family):
  "no validation", "without validation", "does not validate",
  "never validates", "not validated", "unvalidated",
  "no input validation", "without input validation", "does no validation"
Evidence kinds:
  import:pydantic, import:jsonschema, import:marshmallow,
  import:cerberus, import:voluptuous, call:validate*,
  decorator:field_validator, decorator:model_validator,
  decorator:validator, decorator:validates, model:BaseModel,
  call:schema.load
```

One finding per family. A checked-promise claim with production checking
evidence is verified; an unchecked-promise claim with zero checking
evidence anywhere is verified. No claim means PASS, even with checking
calls everywhere. A claim with no production Python source at all yields
one HIGH finding per family.

## Differentiation

- error-claim-audit: which failures the code produces, never whether
  input is checked before use.
- schema-claim-audit: documented field names vs read/write keys, never
  whether values are checked.
- security-claim-audit: eval, shell, and pickle execution of data,
  never checking of data.
- auth-claim-audit: credential requirements, never input checking.
- bandit/ruff: code issues, never docs promises.
- pydantic, jsonschema, and marshmallow documentation: libraries that
  provide checking, never docs-vs-code truth.

## Honest limitations

- Claims are exact phrases, not semantic judgement: a paraphrased
  promise the phrase list does not contain is missed.
- Matching is word-boundary matching on normalised text (lowercased,
  `n't` expanded, hyphens turned into spaces).
- Negation is asymmetric: a negated sentence suppresses checked-family
  claims but not unchecked-family claims, because the unchecked family
  is itself phrased negatively.
- Bare words are not claims: a lone "validate" or "validation" heading
  promises nothing specific.
- Dead code counts: a checking call in uncalled code is still evidence.
- Imports count even when unused; receiver types are not inferred, so
  a checking-named attribute call on any receiver counts.
- A file-local function named the same as a checking call suppresses
  bare-name evidence in that file; attribute evidence is unaffected.
- A schema-object load counts only when the receiver name contains
  "schema"; other load calls do not count.
- No strength check: this tool checks checking-use existence, not
  whether a check is strict, complete, or correct. A hand-rolled
  if/raise guard with no checking name does not count.
- Dynamic imports, aliased library names beyond the tracked list, and
  checking provided by a framework outside the evidence table are missed.

## Development

```sh
python3 -m build
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## License

MIT
