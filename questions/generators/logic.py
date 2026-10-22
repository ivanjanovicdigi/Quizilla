"""Generator for topic logic (30 templates × 25)."""
import random
from common import Batch, fill, code_ans, pick_wrong

R = random.Random(20261023)
DATE = "2026-10-22"
BOOLS = ["`true`", "`false`", "`1`", "`0`"]
OUT_Q = ("{code}\nČo vypíše tento kód?", "{code}\nWhat does this code print?")
NOTHING = ("Nič", "Nothing")
CRASH = ("Program spadne (DivideByZeroException)", "The program crashes (DivideByZeroException)")
COMPILE = ("Chyba pri preklade", "Compile error")
OPS = ["==", "!=", "<", "<=", ">", ">="]
SK_OP = {"==": "rovné", "!=": "rôzne od", "<": "menšie ako", "<=": "menšie alebo rovné", ">": "väčšie ako", ">=": "väčšie alebo rovné"}
EN_OP = {"==": "equal to", "!=": "not equal to", "<": "less than", "<=": "less than or equal to", ">": "greater than", ">=": "greater than or equal to"}
FLIP = {"==": "!=", "!=": "==", "<": ">=", "<=": ">", ">": "<=", ">=": "<"}


def cmp(a, op, b):
    return {"==": a == b, "!=": a != b, "<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]


def bstr(v):
    return "true" if v else "false"


def bool_answers(v):
    c = f"`{bstr(v)}`"
    return [c] + [x for x in BOOLS if x != c]


def tv(v):
    return bstr(v)


def text_answers(answers):
    """answers: list of str (code) or (sk, en) tuples → (sk list, en list or None)."""
    sk = [a[0] if isinstance(a, tuple) else a for a in answers]
    en = [a[1] if isinstance(a, tuple) else a for a in answers]
    return sk, (en if en != sk else None)


def write_if(cond, then_line, else_line=None, braces=False, indent=""):
    i2 = indent + "    "
    if braces:
        s = f"{indent}if ({cond})\n{indent}{{\n{i2}{then_line}\n{indent}}}"
        if else_line:
            s += f"\n{indent}else\n{indent}{{\n{i2}{else_line}\n{indent}}}"
    else:
        s = f"{indent}if ({cond})\n{i2}{then_line}"
        if else_line:
            s += f"\n{indent}else\n{i2}{else_line}"
    return s


W = lambda letter: f'Console.Write("{letter}");'


def main():
    b = Batch(f"{DATE}_logic", "logic", DATE)

    # =================================================================== EASY
    # ---- lg-compare-result
    def compare_result():
        a = R.randint(0, 20)
        bb = a if R.random() < 0.35 else R.randint(0, 20)
        op = R.choice(OPS)
        v = cmp(a, op, bb)
        expr = f"{a} {op} {bb}"
        return b.add("lg-compare-result", 1, code=None,
                     sk_body=f"Akú hodnotu má výraz `{expr}`?", en_body=f"What is the value of the expression `{expr}`?",
                     answers=bool_answers(v),
                     sk_expl=f"Výraz `{expr}` sa pýta, či je {a} {SK_OP[op]} {bb} – {'áno' if v else 'nie'}, preto je jeho hodnota `{bstr(v)}`.",
                     en_expl=f"The expression `{expr}` asks whether {a} is {EN_OP[op]} {bb} – {'yes' if v else 'no'}, so its value is `{bstr(v)}`.",
                     verify={"type": "value", "expr": f"({expr})", "expected": bstr(v)})
    fill(b, "lg-compare-result", 25, compare_result)

    # ---- lg-op-meaning-to-symbol / lg-op-symbol-to-meaning
    MEAN = [
        ("rovná sa", "equal to", "==", ["=", "===", "!=", "<>"]),
        ("nerovná sa", "not equal to", "!=", ["<>", "=!", "==", "!=="]),
        ("menší ako", "less than", "<", ["<=", ">", "=<"]),
        ("menší alebo rovný", "less than or equal to", "<=", ["=<", "<", ">="]),
        ("väčší ako", "greater than", ">", [">=", "<", "=>"]),
        ("väčší alebo rovný", "greater than or equal to", ">=", ["=>", ">", "<="]),
        ("a zároveň (AND)", "and (AND)", "&&", ["||", "and", "!"]),
        ("alebo (OR)", "or (OR)", "||", ["&&", "or", "!="]),
        ("negácia (NOT)", "negation (NOT)", "!", ["not", "!=", "||"]),
        ("priradenie", "assignment", "=", ["==", ":=", "=>"]),
    ]
    PHR = [("Ktorý operátor znamená „{m}“?", "Which operator means “{m}”?"),
           ("Ktorým operátorom v C# zapíšeme „{m}“?", "Which operator do we use in C# for “{m}”?")]
    def meaning_to_symbol():
        sk_m, en_m, op, wrongs = R.choice(MEAN)
        ph = R.choice(PHR)
        w = R.sample(wrongs, 3)
        return b.add("lg-op-meaning-to-symbol", 1, code=None, sk_body=ph[0].format(m=sk_m), en_body=ph[1].format(m=en_m),
                     answers=[code_ans(op)] + [code_ans(x) for x in w],
                     sk_expl=f"Operátor `{op}` znamená „{sk_m}“." + (" Pozor: `=` je priradenie, `==` porovnanie." if op in ("==", "=") else ""),
                     en_expl=f"The operator `{op}` means “{en_m}”." + (" Note: `=` is assignment, `==` is comparison." if op in ("==", "=") else ""),
                     verify={"type": "none"})
    fill(b, "lg-op-meaning-to-symbol", 25, meaning_to_symbol)

    SIMILAR = {"==": ["!=", "=", "<=", ">="], "!=": ["==", "!", "=", "<"], "<": ["<=", ">", ">=", "!="], "<=": ["<", ">=", ">", "=="],
               ">": [">=", "<", "<=", "!="], ">=": [">", "<=", "<", "=="], "&&": ["||", "!", "=="], "||": ["&&", "!", "!="],
               "!": ["!=", "&&", "||"], "=": ["==", "!=", "<="]}
    by_op = {m[2]: m for m in MEAN}
    PHR2 = [("Čo znamená operátor `{o}`?", "What does the operator `{o}` mean?"),
            ("Aký význam má v C# operátor `{o}`?", "What is the meaning of the operator `{o}` in C#?")]
    def symbol_to_meaning():
        sk_m, en_m, op, _ = R.choice(MEAN)
        others = R.sample(SIMILAR[op], 3)
        ph = R.choice(PHR2)
        ans = [(sk_m, en_m)] + [(by_op[o][0], by_op[o][1]) for o in others]
        sk, en = text_answers(ans)
        return b.add("lg-op-symbol-to-meaning", 1, code=None, sk_body=ph[0].format(o=op), en_body=ph[1].format(o=op),
                     answers=sk, en_answers=en,
                     sk_expl=f"Operátor `{op}` znamená „{sk_m}“.", en_expl=f"The operator `{op}` means “{en_m}”.",
                     verify={"type": "none"})
    fill(b, "lg-op-symbol-to-meaning", 25, symbol_to_meaning)

    # ---- lg-assign-vs-compare
    def assign_vs_compare():
        n, m = R.randint(1, 20), R.randint(1, 20)
        comp = [f"if (x == {n})", f"bool rovne = x == {n};", f"while (x == {m}) {{ }}", f"bool b = x == y;", f"if (x == y + {m})"]
        asg = [f"x = {n};", f"x = x + {m};", f"x = y;", f"x = {n} * {m};", f"x = y - {n};"]
        if R.random() < 0.5:
            correct, wrong, sk_a, en_a = R.choice(comp), R.sample(asg, 3), "porovnáva", "compared"
            sk_body = "V ktorom riadku sa hodnota premennej `x` **porovnáva**?"
            en_body = "In which line is the value of `x` **compared**?"
        else:
            correct, wrong = R.choice(asg[:2] + asg[3:]), R.sample(comp, 3)
            sk_body = "V ktorom riadku sa do premennej `x` **priraďuje** hodnota?"
            en_body = "In which line is a value **assigned** to `x`?"
        return b.add("lg-assign-vs-compare", 1, code=None, sk_body=sk_body, en_body=en_body,
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl="`=` priraďuje hodnotu, `==` porovnáva dve hodnoty.",
                     en_expl="`=` assigns a value, `==` compares two values.",
                     verify={"type": "none"})
    fill(b, "lg-assign-vs-compare", 25, assign_vs_compare)

    # ---- lg-not-simple
    def not_simple():
        if R.random() < 0.2:
            inner_v = R.random() < 0.5
            expr, inner = f"!{bstr(inner_v)}", bstr(inner_v)
        else:
            a, c, op = R.randint(0, 15), R.randint(0, 15), R.choice(OPS)
            inner_v = cmp(a, op, c); inner = f"{a} {op} {c}"; expr = f"!({inner})"
        v = not inner_v
        return b.add("lg-not-simple", 1, code=None, sk_body=f"Akú hodnotu má výraz `{expr}`?", en_body=f"What is the value of the expression `{expr}`?",
                     answers=bool_answers(v),
                     sk_expl=f"`{inner}` je `{bstr(inner_v)}`, negácia `!` ho otočí na `{bstr(v)}`.",
                     en_expl=f"`{inner}` is `{bstr(inner_v)}`; the negation `!` flips it to `{bstr(v)}`.",
                     verify={"type": "value", "expr": f"({expr})", "expected": bstr(v)})
    fill(b, "lg-not-simple", 25, not_simple)

    # ---- lg-and-or-literals
    def operand():
        if R.random() < 0.4:
            v = R.random() < 0.5
            return bstr(v), v
        a, c, op = R.randint(0, 9), R.randint(0, 9), R.choice(OPS)
        return f"{a} {op} {c}", cmp(a, op, c)
    def and_or():
        (l, lv), (r, rv) = operand(), operand()
        op = R.choice(["&&", "||"])
        v = (lv and rv) if op == "&&" else (lv or rv)
        expr = f"{l} {op} {r}"
        steps_sk = f"Ľavá strana je `{bstr(lv)}`, pravá `{bstr(rv)}`."
        steps_en = f"The left side is `{bstr(lv)}`, the right side `{bstr(rv)}`."
        return b.add("lg-and-or-literals", 1, code=None, sk_body=f"Akú hodnotu má výraz `{expr}`?", en_body=f"What is the value of the expression `{expr}`?",
                     answers=bool_answers(v),
                     sk_expl=f"`&&` je `true` len vtedy, keď sú obe strany `true`; `||` je `true`, keď je aspoň jedna strana `true`. {steps_sk}",
                     en_expl=f"`&&` is `true` only when both sides are `true`; `||` is `true` when at least one side is `true`. {steps_en}",
                     verify={"type": "value", "expr": f"({expr})", "expected": bstr(v)})
    fill(b, "lg-and-or-literals", 25, and_or)

    # ---- lg-if-only
    def if_only():
        x, m, op = R.randint(0, 20), R.randint(0, 20), R.choice(OPS)
        cond = f"x {op} {m}"; v = cmp(x, op, m)
        code = f"int x = {x};\n" + write_if(cond, W("A"), braces=R.random() < 0.5) + "\n" + W("B")
        correct = "AB" if v else "B"
        wrong = [w for w in ["AB", "B", "A", "BA"] if w != correct]
        R.shuffle(wrong)
        what_sk = "vypíše `A`" if v else "riadok s `A` preskočí"
        what_en = "`A` is printed" if v else "the line with `A` is skipped"
        return b.add("lg-if-only", 1, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Podmienka `{cond}` je `{bstr(v)}`, preto sa {what_sk}. Riadok s `B` je mimo `if` a vypíše sa vždy.",
                     en_expl=f"The condition `{cond}` is `{bstr(v)}`, so {what_en}. The line with `B` is outside the `if` and always runs.",
                     verify={"type": "output"})
    fill(b, "lg-if-only", 25, if_only)

    # ---- lg-if-else
    def if_else():
        x = R.randint(0, 20); m = x if R.random() < 0.3 else R.randint(0, 20); op = R.choice(OPS)
        cond = f"x {op} {m}"; v = cmp(x, op, m)
        code = f"int x = {x};\n" + write_if(cond, W("A"), W("B"), braces=R.random() < 0.4)
        correct = "A" if v else "B"
        sk, en = text_answers([code_ans(correct), code_ans("B" if v else "A"), code_ans("AB"), NOTHING])
        return b.add("lg-if-else", 1, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"Podmienka `{cond}` je `{bstr(v)}`, preto sa vykoná vetva {'`if`' if v else '`else`'}.",
                     en_expl=f"The condition `{cond}` is `{bstr(v)}`, so the {'`if`' if v else '`else`'} branch runs.",
                     verify={"type": "output"})
    fill(b, "lg-if-else", 25, if_else)

    # ---- lg-bool-from-compare
    def bool_from_compare():
        x = R.randint(0, 30); m = x if R.random() < 0.4 else x + R.choice([-2, -1, 1, 2, 5]); op = R.choice(OPS)
        name = R.choice(["b", "vysledok", "plati", "ok"])
        v = cmp(x, op, m); expr = f"x {op} {m}"
        return b.add("lg-bool-from-compare", 1, code=f"int x = {x};\nbool {name} = {expr};",
                     sk_body=f"{{code}}\nAkú hodnotu bude mať premenná `{name}`?", en_body=f"{{code}}\nWhat value will the variable `{name}` have?",
                     answers=bool_answers(v),
                     sk_expl=f"Výraz `{expr}` sa pre `x = {x}` vyhodnotí na `{bstr(v)}` a táto hodnota sa uloží do `{name}`.",
                     en_expl=f"For `x = {x}` the expression `{expr}` evaluates to `{bstr(v)}`, and that value is stored in `{name}`.",
                     verify={"type": "value", "expr": name, "expected": bstr(v)})
    fill(b, "lg-bool-from-compare", 25, bool_from_compare)

    # ---- lg-which-true
    def cond_pool(v):
        pool = []
        for d in [-2, -1, 0, 1, 2]:
            for op in OPS:
                pool.append(f"x {op} {v + d}")
        for _ in range(12):
            a, c = sorted(R.sample(range(v - 4, v + 5), 2))
            pool += [f"x > {a} && x < {c}", f"x < {a} || x > {c}", f"x >= {a} && x <= {c}", f"x == {a} || x == {c}"]
        return pool
    def ev(cond, x):
        return eval(cond.replace("&&", " and ").replace("||", " or "), {"x": x})
    def which_true():
        v = R.randint(1, 15)
        pool = list(dict.fromkeys(cond_pool(v)))
        trues = [c for c in pool if ev(c, v)]
        falses = [c for c in pool if not ev(c, v)]
        correct = R.choice(trues)
        near = [c for c in falses if str(v) in c or str(v + 1) in c or str(v - 1) in c]
        wrong = R.sample(near if len(near) >= 3 else falses, 3)
        if R.random() < 0.4 and "&&" not in correct + "".join(wrong) and "||" not in correct + "".join(wrong):
            comp = [c for c in falses if "&&" in c or "||" in c]
            wrong[0] = R.choice(comp)
        all4 = [correct] + wrong
        return b.add("lg-which-true", 1, code=None,
                     sk_body=f"Premenná `x` má hodnotu `{v}`. Ktorá podmienka je pravdivá?",
                     en_body=f"The variable `x` has the value `{v}`. Which condition is true?",
                     answers=[code_ans(c) for c in all4],
                     sk_expl=f"Pre `x = {v}` platí iba `{correct}`.", en_expl=f"For `x = {v}`, only `{correct}` is true.",
                     verify={"type": "value", "setup": f"int x = {v};",
                             "expr": " + \"|\" + ".join(f"({c})" for c in all4),
                             "expected": "|".join(["True", "False", "False", "False"])})
    fill(b, "lg-which-true", 25, which_true)

    # =================================================================== MEDIUM
    # ---- lg-boundary
    def boundary():
        m, op = R.randint(3, 20), R.choice(["<", "<=", ">", ">="])
        values = {"<": [m - 1, m, m + 1, m + 2], "<=": [m, m + 1, m + 2, m + 3], ">": [m + 1, m, m - 1, m - 2], ">=": [m, m - 1, m - 2, m - 3]}[op]
        code = write_if(f"x {op} {m}", W("A"), W("B"), braces=R.random() < 0.3)
        return b.add("lg-boundary", 2, code=code,
                     sk_body="{code}\nPre ktorú hodnotu `x` vypíše program `A`?", en_body="{code}\nFor which value of `x` does the program print `A`?",
                     answers=[code_ans(x) for x in values],
                     sk_expl=f"Podmienka `x {op} {m}` platí z ponúknutých hodnôt iba pre `{values[0]}`. Pozor na rozdiel medzi `{op[0]}` a `{op[0]}=`.",
                     en_expl=f"Of the offered values, the condition `x {op} {m}` holds only for `{values[0]}`. Mind the difference between `{op[0]}` and `{op[0]}=`.",
                     verify={"type": "which-input", "input": "int x = {answer};", "output": "A"})
    fill(b, "lg-boundary", 25, boundary)

    # ---- lg-else-if-chain
    def else_if_chain():
        x = R.randint(5, 30)
        n = R.choice([3, 4])
        thresholds = sorted(R.sample(range(0, 30), n - 1), reverse=True)
        op = R.choice([">", ">="])
        if R.random() < 0.5:  # ascending wrong-way chain: several true
            thresholds = sorted(thresholds)
        letters = "ABCD"[:n]
        conds = [f"x {op} {t}" for t in thresholds]
        truth = [cmp(x, op, t) for t in thresholds]
        if sum(truth) < 2 and R.random() < 0.7:
            return False
        lines = [f"int x = {x};"]
        for k, c in enumerate(conds):
            lines.append(("if" if k == 0 else "else if") + f" ({c})\n    {W(letters[k])}")
        lines.append(f"else\n    {W(letters[-1])}")
        code = "\n".join(lines)
        first = next((k for k, t in enumerate(truth) if t), n - 1)
        correct = letters[first]
        trues = [letters[k] for k, t in enumerate(truth) if t]
        cands = [l for l in trues if l != correct] + ["".join(trues) if len(trues) > 1 else None, letters[-1]] + list(letters)
        wrong = pick_wrong(correct, [c for c in cands if c])
        if not wrong:
            return False
        cond = conds[first] if first < len(conds) else "else"
        return b.add("lg-else-if-chain", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=(f"Vykoná sa iba prvá vetva, ktorej podmienka platí: `{cond}`." if cond != "else" else "Žiadna podmienka neplatí, vykoná sa `else`."),
                     en_expl=(f"Only the first branch whose condition holds runs: `{cond}`." if cond != "else" else "No condition holds, so `else` runs."),
                     verify={"type": "output"})
    fill(b, "lg-else-if-chain", 25, else_if_chain)

    # ---- lg-nested-if
    def nested_if():
        x, y = R.randint(0, 20), R.randint(0, 20)
        o1, o2 = R.choice(OPS[2:]), R.choice(OPS)
        m1, m2 = R.randint(0, 20), R.randint(0, 20)
        c1, c2 = f"x {o1} {m1}", f"y {o2} {m2}"
        v1, v2 = cmp(x, o1, m1), cmp(y, o2, m2)
        code = (f"int x = {x};\nint y = {y};\nif ({c1})\n{{\n    if ({c2})\n    {{\n        {W('A')}\n    }}\n    else\n    {{\n        {W('B')}\n    }}\n}}\nelse\n{{\n    {W('C')}\n}}")
        correct = ("A" if v2 else "B") if v1 else "C"
        wrong = pick_wrong(correct, ["B" if correct == "A" else "A", "C", "AB", "BC", "A"])
        return b.add("lg-nested-if", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Najprv sa vyhodnotí vonkajšia podmienka `{c1}` (`{bstr(v1)}`)" + (f", potom vnútorná `{c2}` (`{bstr(v2)}`)." if v1 else " – vnútorná sa už nekontroluje."),
                     en_expl=f"First the outer condition `{c1}` is evaluated (`{bstr(v1)}`)" + (f", then the inner one `{c2}` (`{bstr(v2)}`)." if v1 else " – the inner one is never checked."),
                     verify={"type": "output"})
    fill(b, "lg-nested-if", 25, nested_if)

    # ---- lg-even-odd
    def even_odd():
        x = R.randint(1, 50); k = R.choice([2, 2, 2, 3, 4, 5]); neg = R.random() < 0.25
        cond = f"x % {k} {'!=' if neg else '=='} 0"
        rem = x % k; v = (rem != 0) if neg else (rem == 0)
        code = f"int x = {x};\n" + write_if(cond, W("A"), W("B"), braces=R.random() < 0.3)
        correct = "A" if v else "B"
        sk, en = text_answers([code_ans(correct), code_ans("B" if v else "A"), code_ans("AB"), NOTHING])
        return b.add("lg-even-odd", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"`{x} % {k}` je `{rem}`, preto je podmienka `{cond}` `{bstr(v)}`.",
                     en_expl=f"`{x} % {k}` is `{rem}`, so the condition `{cond}` is `{bstr(v)}`.",
                     verify={"type": "output"})
    fill(b, "lg-even-odd", 25, even_odd)

    # ---- lg-change-then-decide
    def change_then_decide():
        x = R.randint(1, 15)
        changes = R.sample([("+", R.randint(2, 9)), ("*", R.randint(2, 3)), ("-", R.randint(1, 5))], R.choice([1, 2]))
        nx = x
        for op, n in changes:
            nx = {"+": nx + n, "*": nx * n, "-": nx - n}[op]
        op = R.choice(["<", "<=", ">", ">="])
        lo, hi = min(x, nx), max(x, nx)
        if hi - lo < 1:
            return False
        m = R.randint(lo, hi)
        if cmp(x, op, m) == cmp(nx, op, m):
            return False
        v = cmp(nx, op, m)
        code = f"int x = {x};\n" + "\n".join(f"x = x {o} {n};" for o, n in changes) + "\n" + write_if(f"x {op} {m}", W("A"), W("B"))
        correct = "A" if v else "B"
        sk, en = text_answers([code_ans(correct), code_ans("B" if v else "A"), code_ans("AB"), NOTHING])
        return b.add("lg-change-then-decide", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"Pred podmienkou má `x` hodnotu `{nx}` (nie {x}), preto je `x {op} {m}` `{bstr(v)}`.",
                     en_expl=f"Before the condition `x` is `{nx}` (not {x}), so `x {op} {m}` is `{bstr(v)}`.",
                     verify={"type": "output"})
    fill(b, "lg-change-then-decide", 25, change_then_decide)

    # ---- lg-separate-ifs
    def separate_ifs():
        x = R.randint(2, 30)
        pool = [(f"x > {m}", lambda x, m=m: x > m) for m in range(0, 30, 3)] + \
               [(f"x < {m}", lambda x, m=m: x < m) for m in range(2, 30, 4)] + \
               [(f"x % {k} == 0", lambda x, k=k: x % k == 0) for k in (2, 3, 5)] + \
               [(f"x != {x}", lambda x, v=x: x != v), (f"x == {x}", lambda x, v=x: x == v)]
        conds = R.sample(pool, 3)
        truth = [f(x) for _, f in conds]
        if sum(truth) < 2:
            return False
        letters = "ABC"
        code = f"int x = {x};\n" + "\n".join(f"if ({c}) {W(l)}" for (c, _), l in zip(conds, letters))
        correct = "".join(l for l, t in zip(letters, truth) if t)
        first = correct[0]
        wrong = pick_wrong(correct, [first, "ABC", correct[-1], correct[::-1], "AB", "BC", "AC"])
        return b.add("lg-separate-ifs", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl="Každý `if` sa vyhodnocuje samostatne (nie je to `else if`), preto sa vypíše každé písmeno, ktorého podmienka platí.",
                     en_expl="Each `if` is evaluated separately (it's not `else if`), so every letter whose condition holds is printed.",
                     verify={"type": "output"})
    fill(b, "lg-separate-ifs", 25, separate_ifs)

    # ---- lg-negated-compare
    ALMOST = {"<": ">", "<=": ">=", ">": "<", ">=": "<=", "==": "<", "!=": "<"}
    def negated_compare():
        op = R.choice(OPS)
        l, r = R.choice([("a", "b"), ("x", "y"), ("x", "10"), ("a", "0"), ("vek", "18"), ("body", "50")])
        expr = f"!({l} {op} {r})"
        correct = f"{l} {FLIP[op]} {r}"
        cands = [f"{l} {ALMOST[op]} {r}", f"{l} {op} {r}"] + ([] if op in ("==", "!=") else [f"{r} {FLIP[op]} {l}"]) + [ f"{l} {FLIP[FLIP[op]] if op not in ('==','!=') else '<='} {r}", f"!{l} {op} {r}"]
        wrong = pick_wrong(correct, cands)
        if not wrong:
            return False
        return b.add("lg-negated-compare", 2, code=None,
                     sk_body=f"Ktorá podmienka znamená to isté ako `{expr}`?", en_body=f"Which condition means the same as `{expr}`?",
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Opak `{l} {op} {r}` je `{correct}` – nezabudni na prípad, keď sú hodnoty rovnaké.",
                     en_expl=f"The opposite of `{l} {op} {r}` is `{correct}` – don't forget the case when the values are equal.",
                     verify={"type": "none"})
    fill(b, "lg-negated-compare", 25, negated_compare)

    # ---- lg-range-and
    def range_and():
        a = R.randint(0, 20); c = a + R.randint(3, 15)
        if R.random() < 0.5:
            correct = f"x >= {a} && x <= {c}"
            wrong = [f"x >= {a} || x <= {c}", f"x > {a} && x < {c}", f"{a} <= x <= {c}"]
            return b.add("lg-range-and", 2, code=None,
                         sk_body=f"Ktorá podmienka platí práve vtedy, keď je `x` od {a} do {c} (vrátane)?",
                         en_body=f"Which condition is true exactly when `x` is from {a} to {c} (inclusive)?",
                         answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                         sk_expl=f"`&&` vyžaduje, aby platili obe podmienky naraz – `x` musí byť zároveň aspoň {a} a najviac {c}. Zápis `{a} <= x <= {c}` v C# nefunguje.",
                         en_expl=f"`&&` requires both conditions to hold at once – `x` must be at least {a} and at most {c}. `{a} <= x <= {c}` doesn't work in C#.",
                         verify={"type": "none"})
        x = R.choice([a - 1, a, R.randint(a, c), c, c + 1])
        lo, hi = R.choice([(">=", "<="), (">", "<"), (">=", "<")])
        cond = f"x {lo} {a} && x {hi} {c}"
        v = cmp(x, lo, a) and cmp(x, hi, c)
        code = f"int x = {x};\n" + write_if(cond, W("A"), W("B"))
        correct = "A" if v else "B"
        sk, en = text_answers([code_ans(correct), code_ans("B" if v else "A"), code_ans("AB"), NOTHING])
        return b.add("lg-range-and", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"`&&` vyžaduje, aby platili obe časti: `x {lo} {a}` je `{bstr(cmp(x, lo, a))}`, `x {hi} {c}` je `{bstr(cmp(x, hi, c))}`.",
                     en_expl=f"`&&` requires both parts to hold: `x {lo} {a}` is `{bstr(cmp(x, lo, a))}`, `x {hi} {c}` is `{bstr(cmp(x, hi, c))}`.",
                     verify={"type": "output"})
    fill(b, "lg-range-and", 25, range_and)

    # ---- lg-either-or
    def either_or():
        a = R.randint(0, 20); c = a + R.randint(5, 50)
        if R.random() < 0.7:
            cond = f"x < {a} || x > {c}"; f = lambda x: x < a or x > c
            x = R.choice([a - 1, a, R.randint(a, c), c, c + 1, a - 5, c + 7])
        else:
            cond = f"x == {a} || x == {c}"; f = lambda x: x == a or x == c
            x = R.choice([a, c, a + 1, c - 1])
        v = f(x)
        code = f"int x = {x};\n" + write_if(cond, W("A"), W("B"))
        correct = "A" if v else "B"
        sk, en = text_answers([code_ans(correct), code_ans("B" if v else "A"), code_ans("AB"), NOTHING])
        l, r = cond.split(" || ")
        return b.add("lg-either-or", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"`||` je `true`, keď platí aspoň jedna strana. Pre `x = {x}`: `{l}` je `{bstr(ev(l, x))}`, `{r}` je `{bstr(ev(r, x))}`.",
                     en_expl=f"`||` is `true` when at least one side holds. For `x = {x}`: `{l}` is `{bstr(ev(l, x))}`, `{r}` is `{bstr(ev(r, x))}`.",
                     verify={"type": "output"})
    fill(b, "lg-either-or", 25, either_or)

    # ---- lg-reverse
    def reverse():
        k = R.choice([2, 3, 5]); a = R.randint(0, 10); c = a + R.randint(4, 15)
        forms = [
            (f"x > {a} && x % {k} == 0", lambda x: x > a and x % k == 0),
            (f"x >= {a} && x <= {c}", lambda x: a <= x <= c),
            (f"x < {a} || x > {c}", lambda x: x < a or x > c),
            (f"x % {k} == 0 || x == {c}", lambda x: x % k == 0 or x == c),
            (f"!(x > {a}) && x != 0", lambda x: not x > a and x != 0),
            (f"x != {a} && x < {c}", lambda x: x != a and x < c),
        ]
        cond, f = R.choice(forms)
        cands = list(range(a - 6, c + 7))
        R.shuffle(cands)
        yes = [x for x in cands if f(x)]
        no = [x for x in cands if not f(x)]
        if not yes or len(no) < 3:
            return False
        correct = yes[0]
        near = sorted(no, key=lambda x: min(abs(x - a), abs(x - c), abs(x - correct)))[:6]
        wrong = R.sample(near, 3)
        code = write_if(cond, W("A"), W("B"))
        return b.add("lg-reverse", 2, code=code,
                     sk_body="{code}\nPre ktorú hodnotu `x` vypíše program `A`?", en_body="{code}\nFor which value of `x` does the program print `A`?",
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Pre `{correct}` platí `{cond}`; ostatné hodnoty podmienku nesplnia.",
                     en_expl=f"For `{correct}` the condition `{cond}` holds; the other values don't satisfy it.",
                     verify={"type": "which-input", "input": "int x = {answer};", "output": "A"})
    fill(b, "lg-reverse", 25, reverse)

    # =================================================================== HARD
    # ---- lg-no-braces
    def no_braces():
        x, m, op = R.randint(0, 20), R.randint(0, 20), R.choice(OPS)
        if cmp(x, op, m):
            return False
        third = R.random() < 0.5
        code = f"int x = {x};\nif (x {op} {m})\n    {W('A')}\n    {W('B')}" + (f"\n{W('C')}" if third else "")
        correct = "BC" if third else "B"
        cands = [(NOTHING if not third else "C"), "AB" + ("C" if third else ""), "A", "ABC" if not third else "AC"]
        sk, en = text_answers([code_ans(correct)] + [c if isinstance(c, tuple) else code_ans(c) for c in cands[:3]])
        return b.add("lg-no-braces", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"Bez zložených zátvoriek patrí k `if` iba prvý príkaz (`A`). Odsadenie na tom nič nemení – riadok s `B` sa vykoná vždy.",
                     en_expl=f"Without braces only the first statement (`A`) belongs to the `if`. Indentation doesn't change that – the line with `B` always runs.",
                     verify={"type": "output"})
    fill(b, "lg-no-braces", 25, no_braces)

    # ---- lg-dangling-else
    def dangling_else():
        x = R.randint(0, 30); m1, m2 = R.randint(0, 30), R.randint(0, 30)
        o1, o2 = R.choice(OPS[2:]), R.choice(OPS[2:])
        v1, v2 = cmp(x, o1, m1), cmp(x, o2, m2)
        code = f"int x = {x};\nif (x {o1} {m1})\n    if (x {o2} {m2})\n        {W('A')}\nelse\n    {W('B')}"
        real = ("A" if v2 else "B") if v1 else ""
        looks = ("A" if v2 else "") if v1 else "B"
        if real == looks:
            return False
        correct = real if real else NOTHING
        cands = [looks if looks else NOTHING, "AB", "A", "B", NOTHING]
        ans = [correct if isinstance(correct, tuple) else code_ans(correct)]
        for c in cands:
            item = c if isinstance(c, tuple) else code_ans(c)
            if item not in ans:
                ans.append(item)
            if len(ans) == 4:
                break
        sk, en = text_answers(ans)
        return b.add("lg-dangling-else", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"`else` patrí k najbližšiemu `if` – teda k `if (x {o2} {m2})`, aj keď je odsadený inak. `x {o1} {m1}` je `{bstr(v1)}`" + (f", `x {o2} {m2}` je `{bstr(v2)}`." if v1 else ", takže sa celý vnútorný `if` aj s `else` preskočí."),
                     en_expl=f"`else` belongs to the nearest `if` – `if (x {o2} {m2})` – even though it's indented differently. `x {o1} {m1}` is `{bstr(v1)}`" + (f", `x {o2} {m2}` is `{bstr(v2)}`." if v1 else ", so the whole inner `if` including the `else` is skipped."),
                     verify={"type": "output", **({"expected": ""} if not real else {})})
    fill(b, "lg-dangling-else", 25, dangling_else)

    # ---- lg-semicolon-if
    def semicolon_if():
        x, m, op = R.randint(0, 20), R.randint(0, 20), R.choice(OPS)
        if cmp(x, op, m) and R.random() < 0.7:
            return False
        block = R.random() < 0.5
        body = f"{{\n    {W('A')}\n}}" if block else f"    {W('A')}"
        code = f"int x = {x};\nif (x {op} {m});\n{body}\n{W('B')}"
        sk, en = text_answers([code_ans("AB"), code_ans("B"), NOTHING, code_ans("A")])
        return b.add("lg-semicolon-if", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl="Bodkočiarka za `if (…)` ukončí príkaz – `if` má prázdne telo a nasledujúci riadok sa vykoná vždy, bez ohľadu na podmienku.",
                     en_expl="The semicolon after `if (…)` ends the statement – the `if` has an empty body and the next line always runs, whatever the condition.",
                     verify={"type": "output"})
    fill(b, "lg-semicolon-if", 25, semicolon_if)

    # ---- lg-compile-error
    INVALID = [("if (x = 5)", "`=` je priradenie – do `int` sa priradí 5 a výsledok nie je `bool`", "`=` is assignment – the result is an `int`, not a `bool`"),
               ("if (x)", "`x` je `int`, podmienka musí byť `bool`", "`x` is an `int`; a condition must be a `bool`"),
               ("if (1 <= x <= 10)", "`1 <= x` je `bool` a ten sa nedá porovnať s číslom 10", "`1 <= x` is a `bool`, which can't be compared with the number 10"),
               ("if (!x > 3)", "`!` sa nedá použiť na `int`", "`!` can't be applied to an `int`"),
               ("if (x > 3 && 10)", "pravá strana `&&` musí byť `bool`, nie číslo", "the right side of `&&` must be a `bool`, not a number"),
               ("if (x == 1 || 2)", "pravá strana `||` musí byť `bool`, nie číslo", "the right side of `||` must be a `bool`, not a number"),
               ("if (b == 1)", "`bool` sa nedá porovnať s číslom", "a `bool` can't be compared with a number")]
    VALID_TRICKY = ["if (b = true)", "if (!b)", "if (b == false)", "if (!(x > 3))"]
    VALID = ["if (b)", "if (x != 5 || b)", "if (x % 2 == 1)", "if (x >= 1 && x <= 10)", "if (x == 5 && !b)"]
    def compile_error():
        bad, rsk, ren = R.choice(INVALID)
        valid = R.sample(VALID_TRICKY, R.choice([1, 2]))
        valid += R.sample(VALID, 3 - len(valid))
        R.shuffle(valid)
        extra_sk = " Pozor: `if (b = true)` sa preloží – `b` je `bool`, takže priradenie dá `bool` (kompilátor iba upozorní)." if "if (b = true)" in valid else ""
        extra_en = " Note: `if (b = true)` compiles – `b` is a `bool`, so the assignment gives a `bool` (only a warning)." if "if (b = true)" in valid else ""
        return b.add("lg-compile-error", 3, code="int x = 5;\nbool b = false;",
                     sk_body="{code}\nKtorý riadok spôsobí chybu pri preklade?", en_body="{code}\nWhich line causes a compile error?",
                     answers=[code_ans(bad)] + [code_ans(v) for v in valid],
                     sk_expl=f"`{bad}` sa nedá preložiť: {rsk}.{extra_sk}", en_expl=f"`{bad}` does not compile: {ren}.{extra_en}",
                     verify={"type": "which-line", "expect": "compile-error", "wrap": "{line} { }"})
    fill(b, "lg-compile-error", 25, compile_error)

    # ---- lg-else-if-order
    def else_if_order():
        name = R.choice(["body", "skore", "x"])
        t = sorted(R.sample(range(10, 95, 5), 2))  # low, high
        v = R.randint(t[1] + 1, 100)
        letters = R.choice([("C", "A", "F"), ("B", "A", "X"), ("2", "1", "5")])
        code = (f"int {name} = {v};\nif ({name} > {t[0]})\n    {W(letters[0])}\nelse if ({name} > {t[1]})\n    {W(letters[1])}\nelse\n    {W(letters[2])}")
        correct = letters[0]
        wrong = [letters[1], letters[0] + letters[1], letters[2]]
        return b.add("lg-else-if-order", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Vetvy sa skúšajú zhora: `{name} > {t[0]}` platí už pre `{v}`, takže vetva `{name} > {t[1]}` sa nikdy nevyskúša – podmienky sú v zlom poradí.",
                     en_expl=f"Branches are tried from the top: `{name} > {t[0]}` already holds for `{v}`, so the branch `{name} > {t[1]}` is never tried – the conditions are in the wrong order.",
                     verify={"type": "output"})
    fill(b, "lg-else-if-order", 25, else_if_order)

    # ---- lg-short-circuit
    def short_circuit():
        k = R.choice([10, 12, 20, 30, 100]); t = R.randint(0, 5)
        form = R.choice(["and0", "or0", "and_ok", "or_ok"])
        if form == "and0":
            a = 0; cond = f"a != 0 && {k} / a > {t}"; v = False
        elif form == "or0":
            a = 0; cond = f"a == 0 || {k} / a > {t}"; v = True
        elif form == "and_ok":
            a = R.choice([2, 3, 4, 5]); cond = f"a != 0 && {k} / a > {t}"; v = k // a > t
        else:
            a = R.choice([2, 3, 4, 5]); cond = f"a == 0 || {k} / a > {t}"; v = k // a > t
        code = f"int a = {a};\n" + write_if(cond, W("A"), W("B"))
        correct = "A" if v else "B"
        sk, en = text_answers([code_ans(correct), code_ans("B" if v else "A"), CRASH, COMPILE])
        if a == 0:
            esk = "`&&` a `||` sú skrátené: ľavá strana už rozhodne o výsledku, takže pravá sa vôbec nevyhodnotí – k deleniu nulou nedôjde."
            een = "`&&` and `||` short-circuit: the left side already decides the result, so the right side is never evaluated – no division by zero happens."
        else:
            esk = f"`a` je `{a}`, takže sa vyhodnotí aj pravá strana: `{k} / {a}` = {k // a}, `{k // a} > {t}` je `{bstr(k // a > t)}`."
            een = f"`a` is `{a}`, so the right side is evaluated too: `{k} / {a}` = {k // a}, `{k // a} > {t}` is `{bstr(k // a > t)}`."
        return b.add("lg-short-circuit", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=esk, en_expl=een, verify={"type": "output"})
    fill(b, "lg-short-circuit", 25, short_circuit)

    # ---- lg-and-or-precedence
    def and_or_prec():
        def opnd():
            if R.random() < 0.5:
                v = R.random() < 0.5
                return bstr(v), v
            x, op, m = R.randint(0, 9), R.choice(OPS), R.randint(0, 9)
            return f"{x} {op} {m}", cmp(x, op, m)
        (p, pv), (q, qv), (r, rv) = opnd(), opnd(), opnd()
        if R.random() < 0.5:
            expr = f"{p} || {q} && {r}"; real = pv or (qv and rv); ltr = (pv or qv) and rv
            grouped = f"{p} || ({q} && {r})"
        else:
            expr = f"{p} && {q} || {r}"; real = (pv and qv) or rv; ltr = (pv and qv) or rv
            grouped = f"({p} && {q}) || {r}"
            if R.random() < 0.7:
                return False  # this form gives the same result left-to-right; keep a few
        if real == ltr and "|| (" in grouped:
            return False
        return b.add("lg-and-or-precedence", 3, code=None,
                     sk_body=f"Akú hodnotu má výraz `{expr}`?", en_body=f"What is the value of the expression `{expr}`?",
                     answers=bool_answers(real),
                     sk_expl=f"`&&` má prednosť pred `||`, výraz sa vyhodnotí ako `{grouped}` = `{bstr(real)}`.",
                     en_expl=f"`&&` has higher precedence than `||`, so the expression is evaluated as `{grouped}` = `{bstr(real)}`.",
                     verify={"type": "value", "expr": f"({expr})", "expected": bstr(real)})
    fill(b, "lg-and-or-precedence", 25, and_or_prec)

    # ---- lg-precedence
    def precedence():
        x = R.randint(1, 12)
        forms = [
            (lambda: (f"x + {(k := R.randint(1, 5))} > {(m := R.randint(2, 4))} * {(n := R.randint(1, 5))}", x + k > m * n, f"{x} + {k} = {x + k}, {m} * {n} = {m * n}, {x + k} > {m * n}")),
            (lambda: (f"!(x % {(k := R.randint(2, 4))} == 0)", not (x % k == 0), f"{x} % {k} = {x % k}, `{x % k} == 0` je `{bstr(x % k == 0)}`, `!` to otočí")),
            (lambda: (f"x * 2 == x + {(k := R.randint(1, 12))}", x * 2 == x + k, f"{x} * 2 = {x * 2}, {x} + {k} = {x + k}")),
            (lambda: (f"x - {(k := R.randint(1, 5))} * 2 >= {(m := R.randint(0, 8))}", x - k * 2 >= m, f"{k} * 2 = {k * 2}, {x} - {k * 2} = {x - k * 2}, {x - k * 2} >= {m}")),
            (lambda: (f"x / {(k := R.randint(2, 4))} * {k} == x", x // k * k == x, f"{x} / {k} = {x // k} (celočíselne), {x // k} * {k} = {x // k * k}, {x // k * k} == {x}")),
        ]
        expr, v, steps = R.choice(forms)()
        steps_en = steps.replace("celočíselne", "integer division").replace(" je ", " is ").replace("to otočí", "flips it")
        name = R.choice(["b", "vysledok", "plati"])
        return b.add("lg-precedence", 3, code=f"int x = {x};\nbool {name} = {expr};",
                     sk_body=f"{{code}}\nAkú hodnotu bude mať premenná `{name}`?", en_body=f"{{code}}\nWhat value will the variable `{name}` have?",
                     answers=bool_answers(v),
                     sk_expl=f"Najprv sa vypočíta aritmetika (`*`, `/`, `%` pred `+`, `-`), potom porovnanie: {steps}.",
                     en_expl=f"Arithmetic is done first (`*`, `/`, `%` before `+`, `-`), then the comparison: {steps_en}.",
                     verify={"type": "value", "expr": name, "expected": bstr(v)})
    fill(b, "lg-precedence", 25, precedence)

    # ---- lg-de-morgan
    def de_morgan():
        (l1, o1, r1), (l2, o2, r2) = (("x", R.choice(OPS[2:]), R.randint(0, 9)), ("y", R.choice(OPS[2:]), R.randint(0, 9)))
        op = R.choice(["&&", "||"]); other = "||" if op == "&&" else "&&"
        expr = f"!({l1} {o1} {r1} {op} {l2} {o2} {r2})"
        correct = f"{l1} {FLIP[o1]} {r1} {other} {l2} {FLIP[o2]} {r2}"
        wrong = [f"{l1} {FLIP[o1]} {r1} {op} {l2} {FLIP[o2]} {r2}",
                 f"{l1} {ALMOST[o1]} {r1} {other} {l2} {ALMOST[o2]} {r2}",
                 f"!{l1} {o1} {r1} {other} !{l2} {o2} {r2}"]
        if len(set([correct] + wrong)) < 4:
            return False
        return b.add("lg-de-morgan", 3, code=None,
                     sk_body=f"Ktorá podmienka znamená to isté ako `{expr}`?", en_body=f"Which condition means the same as `{expr}`?",
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Negácia `{op}` je `{other}` a každá podmienka sa otočí: `{correct}`.",
                     en_expl=f"The negation of `{op}` is `{other}`, and each condition is flipped: `{correct}`.",
                     verify={"type": "none"})
    fill(b, "lg-de-morgan", 25, de_morgan)

    # ---- lg-trace-branches
    def trace_branches():
        x = R.randint(1, 20)
        k = R.choice([2, 3])
        a1 = R.choice([("x = x / 2;", lambda v: v // 2), ("x = x + 10;", lambda v: v + 10), ("x = x - 3;", lambda v: v - 3)])
        a2 = R.choice([("x = x * 3;", lambda v: v * 3), ("x = x + 1;", lambda v: v + 1), ("x = x * 2;", lambda v: v * 2)])
        c1 = f"x % {k} == 0"
        t1, t2 = R.randint(5, 25), R.randint(0, 6)
        c2 = R.choice([f"x > {t1} || x < {t2}", f"x > {t2} && x < {t1}", f"x % 2 == 1 || x > {t1}"])
        a3 = R.choice([("x = x - 10;", lambda v: v - 10), ("x = x + 5;", lambda v: v + 5), ("x = x * 2;", lambda v: v * 2)])
        def evc(c, v):
            return eval(c.replace("&&", " and ").replace("||", " or ").replace("%", "%"), {"x": v})
        def run(flip1=False, flip2=False, skip2=False):
            v = x
            b1 = (v % k == 0) != flip1
            v = a1[1](v) if b1 else a2[1](v)
            if skip2:
                return v
            b2 = evc(c2, v) != flip2
            if b2:
                v = a3[1](v)
            return v
        if x < 0:
            return False
        correct = run()
        mid = run(skip2=True)
        if mid < 0:
            return False
        wrong = pick_wrong(correct, [run(flip1=True), run(flip2=True), mid, run(flip1=True, flip2=True)], fallback=[correct + 1, correct - 1])
        if not wrong:
            return False
        code = (f"int x = {x};\nif ({c1})\n{{\n    {a1[0]}\n}}\nelse\n{{\n    {a2[0]}\n}}\nif ({c2})\n{{\n    {a3[0]}\n}}")
        b1 = x % k == 0
        b2 = evc(c2, mid)
        steps_sk = f"`{c1}` je `{bstr(b1)}` → x = {mid}; `{c2}` je `{bstr(b2)}`" + (f" → x = {correct}" if b2 else " → x sa nemení")
        steps_en = f"`{c1}` is `{bstr(b1)}` → x = {mid}; `{c2}` is `{bstr(b2)}`" + (f" → x = {correct}" if b2 else " → x doesn't change")
        return b.add("lg-trace-branches", 3, code=code,
                     sk_body="{code}\nAkú hodnotu bude mať premenná `x` na konci?", en_body="{code}\nWhat value will the variable `x` have at the end?",
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Postupne: {steps_sk}. Na konci má `x` hodnotu `{correct}`.",
                     en_expl=f"Step by step: {steps_en}. At the end `x` is `{correct}`.",
                     verify={"type": "value", "expr": "x"})
    fill(b, "lg-trace-branches", 25, trace_branches)
    return b


if __name__ == "__main__":
    main().write()
