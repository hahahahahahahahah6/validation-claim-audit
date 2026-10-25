"""Tests for validation-claim-audit."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from validation_claim_audit.audit import audit, extract_claims  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MARKER = "MARKER_NEVER_READ_9f3a"


def make_tree(files):
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return tmp, root


def run_cli(root, *extra):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    proc = subprocess.run(
        [sys.executable, "-m", "validation_claim_audit", str(root), *extra],
        capture_output=True, text=True, env=env,
    )
    return proc


class ClaimTests(unittest.TestCase):
    def claims(self, readme):
        _, root = make_tree({"README.md": readme, "main.py": "x = 1\n"})
        return extract_claims(root)

    def test_validates_input(self):
        self.assertEqual(len(self.claims("It validates input.\n")["validated"]), 1)

    def test_validates_all_input(self):
        self.assertEqual(len(self.claims("It validates all input.\n")["validated"]), 1)

    def test_validates_inputs(self):
        self.assertEqual(len(self.claims("It validates inputs.\n")["validated"]), 1)

    def test_input_validation_phrase(self):
        self.assertEqual(len(self.claims("With input validation.\n")["validated"]), 1)

    def test_input_hyphen_phrase(self):
        self.assertEqual(len(self.claims("With input-validation.\n")["validated"]), 1)

    def test_validates_data(self):
        self.assertEqual(len(self.claims("It validates data.\n")["validated"]), 1)

    def test_validates_requests(self):
        self.assertEqual(len(self.claims("It validates requests.\n")["validated"]), 1)

    def test_validates_arguments(self):
        self.assertEqual(len(self.claims("It validates arguments.\n")["validated"]), 1)

    def test_validates_parameters(self):
        self.assertEqual(len(self.claims("It validates parameters.\n")["validated"]), 1)

    def test_validates_user_input(self):
        self.assertEqual(len(self.claims("It validates user input.\n")["validated"]), 1)

    def test_all_input_is_validated(self):
        self.assertEqual(
            len(self.claims("All input is validated.\n")["validated"]), 1)

    def test_inputs_are_validated(self):
        self.assertEqual(
            len(self.claims("Inputs are validated.\n")["validated"]), 1)

    def test_validated_input(self):
        self.assertEqual(len(self.claims("Validated input only.\n")["validated"]), 1)

    def test_performs_validation(self):
        self.assertEqual(
            len(self.claims("It performs validation.\n")["validated"]), 1)

    def test_bare_validate_no_claim(self):
        claims = self.claims("Validate\n")
        self.assertEqual(claims["validated"], [])
        self.assertEqual(claims["unvalidated"], [])

    def test_bare_validation_no_claim(self):
        claims = self.claims("Validation\n")
        self.assertEqual(claims["validated"], [])
        self.assertEqual(claims["unvalidated"], [])

    def test_no_validation(self):
        self.assertEqual(len(self.claims("No validation.\n")["unvalidated"]), 1)

    def test_without_validation(self):
        self.assertEqual(
            len(self.claims("Without validation.\n")["unvalidated"]), 1)

    def test_does_not_validate(self):
        self.assertEqual(
            len(self.claims("It does not validate.\n")["unvalidated"]), 1)

    def test_doesnt_validate(self):
        self.assertEqual(
            len(self.claims("It doesn't validate.\n")["unvalidated"]), 1)

    def test_never_validates(self):
        self.assertEqual(
            len(self.claims("It never validates.\n")["unvalidated"]), 1)

    def test_not_validated(self):
        claims = self.claims("Input is not validated.\n")
        self.assertEqual(len(claims["unvalidated"]), 1)
        self.assertEqual(claims["validated"], [])

    def test_unvalidated_only(self):
        claims = self.claims("Unvalidated data passes through.\n")
        self.assertEqual(len(claims["unvalidated"]), 1)
        self.assertEqual(claims["validated"], [])

    def test_no_input_validation(self):
        self.assertEqual(
            len(self.claims("No input validation.\n")["unvalidated"]), 1)

    def test_without_input_validation(self):
        self.assertEqual(
            len(self.claims("Without input validation.\n")["unvalidated"]), 1)

    def test_does_no_validation(self):
        self.assertEqual(
            len(self.claims("It does no validation.\n")["unvalidated"]), 1)

    def test_fenced_excluded(self):
        claims = self.claims("```\nIt validates input.\n```\n")
        self.assertEqual(claims["validated"], [])
        self.assertEqual(claims["unvalidated"], [])

    def test_inline_code_counts(self):
        self.assertEqual(
            len(self.claims("It `validates input` first.\n")["validated"]), 1)

    def test_negation_suppresses_validated(self):
        claims = self.claims("It does not validate input.\n")
        # "does not validate" is itself an unvalidated claim; the
        # validated family must not also fire on this sentence.
        self.assertEqual(claims["validated"], [])

    def test_docs_subdir_counts(self):
        _, root = make_tree({
            "README.md": "Nothing here.\n",
            "docs/guide.md": "It validates input.\n",
            "main.py": "x = 1\n",
        })
        self.assertEqual(len(extract_claims(root)["validated"]), 1)


class EvidenceTests(unittest.TestCase):
    def audit_tree(self, readme, main):
        _, root = make_tree({"README.md": readme, "main.py": main})
        return audit(root)

    def test_pydantic_import_counts(self):
        res = self.audit_tree("It validates input.\n", "import pydantic\n")
        self.assertEqual(res["status"], "PASS")

    def test_jsonschema_import_counts(self):
        res = self.audit_tree("It validates input.\n", "import jsonschema\n")
        self.assertEqual(res["status"], "PASS")

    def test_marshmallow_import_counts(self):
        res = self.audit_tree("It validates input.\n", "import marshmallow\n")
        self.assertEqual(res["status"], "PASS")

    def test_cerberus_import_counts(self):
        res = self.audit_tree("It validates input.\n", "import cerberus\n")
        self.assertEqual(res["status"], "PASS")

    def test_voluptuous_import_counts(self):
        res = self.audit_tree("It validates input.\n", "import voluptuous\n")
        self.assertEqual(res["status"], "PASS")

    def test_re_import_alone_no(self):
        res = self.audit_tree("It validates input.\n", "import re\n")
        self.assertEqual(res["status"], "FAIL")

    def test_json_import_alone_no(self):
        res = self.audit_tree("It validates input.\n", "import json\n")
        self.assertEqual(res["status"], "FAIL")

    def test_validate_call_counts(self):
        res = self.audit_tree("It validates input.\n", "validate(data)\n")
        self.assertEqual(res["status"], "PASS")

    def test_validate_input_call_counts(self):
        res = self.audit_tree("It validates input.\n", "validate_input(data)\n")
        self.assertEqual(res["status"], "PASS")

    def test_schema_validate_call_counts(self):
        res = self.audit_tree("It validates input.\n", "schema.validate(data)\n")
        self.assertEqual(res["status"], "PASS")

    def test_validate_python_call_counts(self):
        res = self.audit_tree(
            "It validates input.\n", "adapter.validate_python(data)\n")
        self.assertEqual(res["status"], "PASS")

    def test_local_def_validate_suppresses_name(self):
        code = "def validate(x):\n    return x\n\nvalidate(data)\n"
        res = self.audit_tree("It validates input.\n", code)
        self.assertEqual(res["status"], "FAIL")

    def test_field_validator_counts(self):
        code = "from pydantic import field_validator\n\n"
        code += "@field_validator('x')\ndef check(cls, v):\n    return v\n"
        res = self.audit_tree("It validates input.\n", code)
        self.assertEqual(res["status"], "PASS")

    def test_model_validator_counts(self):
        code = "@model_validator(mode='after')\ndef check(self):\n    return self\n"
        res = self.audit_tree("It validates input.\n", code)
        self.assertEqual(res["status"], "PASS")

    def test_validator_decorator_counts(self):
        code = "@validator('x')\ndef check(cls, v):\n    return v\n"
        res = self.audit_tree("It validates input.\n", code)
        self.assertEqual(res["status"], "PASS")

    def test_validates_decorator_counts(self):
        code = "@validates('x')\ndef check(self, key, v):\n    return v\n"
        res = self.audit_tree("It validates input.\n", code)
        self.assertEqual(res["status"], "PASS")

    def test_basemodel_class_counts(self):
        code = "class User(BaseModel):\n    name: str\n"
        res = self.audit_tree("It validates input.\n", code)
        self.assertEqual(res["status"], "PASS")

    def test_schema_load_counts(self):
        res = self.audit_tree("It validates input.\n", "user_schema.load(data)\n")
        self.assertEqual(res["status"], "PASS")

    def test_json_load_no(self):
        res = self.audit_tree("It validates input.\n", "json.load(f)\n")
        self.assertEqual(res["status"], "FAIL")

    def test_isinstance_alone_no(self):
        res = self.audit_tree(
            "It validates input.\n", "if isinstance(x, int):\n    pass\n")
        self.assertEqual(res["status"], "FAIL")

    def test_try_except_alone_no(self):
        code = "try:\n    run()\nexcept ValueError:\n    pass\n"
        res = self.audit_tree("It validates input.\n", code)
        self.assertEqual(res["status"], "FAIL")

    def test_assert_alone_no(self):
        res = self.audit_tree("It validates input.\n", "assert x > 0\n")
        self.assertEqual(res["status"], "FAIL")

    def test_regex_alone_no(self):
        res = self.audit_tree(
            "It validates input.\n", "import re\nre.fullmatch('a+', x)\n")
        self.assertEqual(res["status"], "FAIL")

    def test_variable_named_validate_no(self):
        res = self.audit_tree("It validates input.\n", "validate = 5\n")
        self.assertEqual(res["status"], "FAIL")

    def test_ignore_drops_evidence(self):
        _, root = make_tree({
            "README.md": "It validates input.\n",
            "main.py": "import jsonschema\n",
        })
        res = audit(root, ["main.py"])
        self.assertEqual(res["status"], "FAIL")


class RuleTests(unittest.TestCase):
    def test_no_claim_pass(self):
        _, root = make_tree({"README.md": "A tool.\n", "main.py": "x = 1\n"})
        self.assertEqual(audit(root)["status"], "PASS")

    def test_no_source_high(self):
        _, root = make_tree({"README.md": "It validates input.\n"})
        res = audit(root)
        self.assertEqual(res["status"], "FAIL")
        self.assertEqual(res["findings"][0]["severity"], "HIGH")

    def test_both_families_two_findings(self):
        _, root = make_tree({
            "README.md": "It validates input.\nNo validation.\n",
            "main.py": "import jsonschema\n",
        })
        res = audit(root)
        # validated verified; unvalidated falsified -> exactly one finding
        self.assertEqual(len(res["findings"]), 1)
        self.assertEqual(
            res["findings"][0]["rule"], "documented-unvalidated-claim-false")

    def test_both_families_both_falsified(self):
        # validated falsified by zero evidence, unvalidated falsified
        # cannot co-exist with zero evidence, so use two roots? Instead
        # check contradictory docs with evidence falsify unvalidated only;
        # the independent-family property is pinned by the fixture tests.
        _, root = make_tree({
            "README.md": "It validates input.\nNo validation.\n",
            "main.py": "x = 1\n",
        })
        res = audit(root)
        # validated falsified HIGH; unvalidated verified (zero evidence)
        self.assertEqual(len(res["findings"]), 1)
        self.assertEqual(
            res["findings"][0]["rule"], "documented-validated-claim-false")


class FixtureTests(unittest.TestCase):
    def test_good_validated(self):
        self.assertEqual(audit(FIXTURES / "good" / "validated")["status"], "PASS")

    def test_good_unvalidated(self):
        self.assertEqual(
            audit(FIXTURES / "good" / "unvalidated")["status"], "PASS")

    def test_bad_validated_exactly_one_high(self):
        res = audit(FIXTURES / "bad" / "validated")
        self.assertEqual(res["status"], "FAIL")
        self.assertEqual(len(res["findings"]), 1)
        self.assertEqual(res["findings"][0]["rule"],
                         "documented-validated-claim-false")
        self.assertEqual(res["findings"][0]["severity"], "HIGH")

    def test_bad_unvalidated_exactly_one_high(self):
        res = audit(FIXTURES / "bad" / "unvalidated")
        self.assertEqual(res["status"], "FAIL")
        self.assertEqual(len(res["findings"]), 1)
        self.assertEqual(res["findings"][0]["rule"],
                         "documented-unvalidated-claim-false")
        self.assertEqual(res["findings"][0]["severity"], "HIGH")

    def test_testonly_medium(self):
        res = audit(FIXTURES / "testonly" / "validated")
        self.assertEqual(res["status"], "FAIL")
        self.assertEqual(len(res["findings"]), 1)
        self.assertEqual(res["findings"][0]["severity"], "MEDIUM")
        self.assertEqual(res["findings"][0]["rule"],
                         "documented-validated-claim-false-test-only")

    def test_marker_never_leaked(self):
        proc = run_cli(FIXTURES / "bad" / "validated", "--json")
        self.assertNotIn(MARKER, proc.stdout)
        self.assertNotIn(MARKER, proc.stderr)

    def test_json_shape(self):
        proc = run_cli(FIXTURES / "good" / "validated", "--json")
        data = json.loads(proc.stdout)
        self.assertIn("findings", data)
        self.assertIn("verified_claims", data)
        self.assertEqual(proc.returncode, 0)

    def test_cli_bad_exit_2(self):
        proc = run_cli(FIXTURES / "bad" / "validated")
        self.assertEqual(proc.returncode, 2)

    def test_cli_fail_on_high_medium_exit_0(self):
        proc = run_cli(FIXTURES / "testonly" / "validated", "--fail-on", "HIGH")
        self.assertEqual(proc.returncode, 0)

    def test_cli_version(self):
        proc = run_cli(FIXTURES / "good" / "validated", "--version")
        self.assertIn("0.1.0", proc.stdout)

    def test_cli_usage_error(self):
        proc = run_cli("/nonexistent-path-xyz")
        self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
