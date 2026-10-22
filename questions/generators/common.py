"""Shared helpers for Claude's question generators (Python 3.10+).

Each topic has a generator questions/generators/<topic>.py that builds questions from the
templates in questions/templates/<topic>.json and writes batch files to questions/batches/.
Correct answers are computed by the generator; `npm run q:verify` double-checks them with .NET.
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCHES = ROOT / "questions" / "batches"


def fmt_double(x: float) -> str:
    """How C# prints a double (invariant culture): 30.0 -> 30, 2.5 -> 2.5."""
    if x == int(x) and abs(x) < 1e15:
        return str(int(x))
    return repr(x)


def code_ans(s) -> str:
    """Answer as inline code."""
    return f"`{s}`"


def cs_string(s: str) -> str:
    return '"' + s + '"'


def cs_char(c: str) -> str:
    return "'" + c + "'"


class Batch:
    def __init__(self, name: str, topic: str, created: str, subject: str = "prog-1-digi"):
        self.data = {"batch": name, "subject": subject, "topic": topic, "created": created, "questions": []}
        self.counters: dict[str, int] = {}
        self.seen: set = set()

    def add(self, template: str, difficulty: int, *, code, sk_body, en_body, answers,
            sk_expl, en_expl, verify, en_answers=None, status="approved"):
        """answers[0] is the correct one. Returns False (and skips) for duplicates."""
        assert len(answers) == 4, (template, answers)
        assert len(set(answers)) == 4, (template, answers)
        if en_answers is not None:
            assert len(en_answers) == 4 and len(set(en_answers)) == 4, (template, en_answers)
        key = (template, code, sk_body, tuple(sorted(answers)))
        if key in self.seen:
            return False
        self.seen.add(key)
        n = self.counters.get(template, 0) + 1
        self.counters[template] = n
        q = {
            "id": f"{template}-{n:03d}",
            "template": template,
            "difficulty": difficulty,
            "status": status,
            "code": code,
            "sk": {"body": sk_body, "answers": answers, "explanation": sk_expl},
            "en": {"body": en_body, "answers": en_answers, "explanation": en_expl},
            "verify": verify,
        }
        self.data["questions"].append(q)
        return True

    def count(self, template: str) -> int:
        return self.counters.get(template, 0)

    def write(self):
        BATCHES.mkdir(parents=True, exist_ok=True)
        path = BATCHES / f"{self.data['batch']}.json"
        text = json.dumps(self.data, ensure_ascii=False, indent=2) + "\n"
        path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
        print(f"{path.name}: {len(self.data['questions'])} questions")
        return path


def fill(batch: Batch, template: str, target: int, make, tries: int = 2000):
    """Call make() until the template has `target` questions (make returns True when added)."""
    for _ in range(tries):
        if batch.count(template) >= target:
            return
        make()
    raise RuntimeError(f"{template}: only {batch.count(template)} of {target} generated")


def pick_wrong(correct, candidates, n=3, fallback=None):
    """First n distinct candidates different from the correct answer (keeps order)."""
    out = []
    for c in candidates:
        if c != correct and c not in out:
            out.append(c)
        if len(out) == n:
            return out
    for c in fallback or []:
        if c != correct and c not in out:
            out.append(c)
        if len(out) == n:
            return out
    if isinstance(correct, int) and not isinstance(correct, bool):
        for d in (2, -2, 3, -3, 4, 5, 10):
            c = correct + d
            if c not in out and c >= 0:
                out.append(c)
            if len(out) == n:
                return out
    return None
