"""Generator for topic data-types, difficulty 2 and 3 (difficulty 1 = batch 2026-10-22_data-types_1)."""
import random
from common import Batch, fill, fmt_double, code_ans, cs_string, cs_char, pick_wrong

R = random.Random(20261022)
DATE = "2026-10-22"
NAMES = ["cena", "cislo", "pocet", "vysledok", "hodnota", "suma", "body", "skore", "vek", "rok",
         "teplota", "vyska", "sirka", "dlzka", "vaha", "kluc", "stav", "zostatok", "trieda", "znamka"]
VAL_Q = ("{code}\nAkú hodnotu bude mať premenná `%s`?", "{code}\nWhat value will the variable `%s` have?")
EXPR_EXPL = ("Najskôr sa vypočíta výraz `%s`, ktorého výsledok je `%s`. Táto hodnota sa priradí do premennej `%s`.",
             "First the expression `%s` is evaluated; its result is `%s`. This value is assigned to the variable `%s`.")


def val_q(name):
    return VAL_Q[0] % name, VAL_Q[1] % name


def int_ops(a, b):
    """Results of a op b as C# would compute them for ints, plus the 'real division' distractor."""
    res = {"+": a + b, "-": a - b, "*": a * b}
    res["/"] = a // b if a % b == 0 else a / b  # wrong-answer form of division
    return res


# ======================================================================= medium (2)
def medium():
    b = Batch(f"{DATE}_data-types_2", "data-types", DATE)

    # ---- dt-int-arith: + 6, - 6, * 6, / 7
    plan = ["+"] * 6 + ["-"] * 6 + ["*"] * 6 + ["/"] * 7
    for op in plan:
        def make(op=op):
            if op == "/":
                y = R.randint(2, 9); x = y * R.randint(2, 10)
            else:
                x, y = R.randint(2, 40), R.randint(2, 40)
                if op == "*":
                    x, y = R.randint(2, 15), R.randint(2, 12)
            name = R.choice(NAMES)
            res = int_ops(x, y)
            correct = x // y if op == "/" else res[op]
            others = [res[o] for o in "+-*/" if o != op]
            wrong = pick_wrong(correct, others)
            if not wrong:
                return False
            if sum(isinstance(w, float) for w in wrong) > 1:
                return False
            expr = f"{x} {op} {y}"
            fmt = lambda v: fmt_double(v) if isinstance(v, float) else str(v)
            return b.add("dt-int-arith", 2, code=f"int {name} = {expr};",
                         sk_body=val_q(name)[0], en_body=val_q(name)[1],
                         answers=[code_ans(correct)] + [code_ans(fmt(w)) for w in wrong],
                         sk_expl=EXPR_EXPL[0] % (expr, correct, name), en_expl=EXPR_EXPL[1] % (expr, correct, name),
                         verify={"type": "value", "expr": name})
        before = b.count("dt-int-arith")
        fill(b, "dt-int-arith", before + 1, make)

    # ---- dt-int-mod
    def mod():
        x, y = R.randint(20, 40), R.randint(3, 9)
        if x % y == 0:
            return False
        name = R.choice(NAMES)
        correct = x % y
        wrong = pick_wrong(correct, [x + y, x - y, x * y])
        if not wrong:
            return False
        expr = f"{x} % {y}"
        return b.add("dt-int-mod", 2, code=f"int {name} = {expr};", sk_body=val_q(name)[0], en_body=val_q(name)[1],
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=EXPR_EXPL[0] % (expr, correct, name) + f" Operátor `%` vracia zvyšok po delení: {x} = {x // y} · {y} + {correct}.",
                     en_expl=EXPR_EXPL[1] % (expr, correct, name) + f" The `%` operator gives the remainder: {x} = {x // y} · {y} + {correct}.",
                     verify={"type": "value", "expr": name})
    fill(b, "dt-int-mod", 25, mod)

    # ---- dt-double-arith: + 12, * 13
    for op in ["+"] * 12 + ["*"] * 13:
        def make(op=op):
            halves = [1.5, 2.5, 3.5, 4.5, 7.5, 12.5, 0.5, 2.25, 1.25]
            x = R.choice(halves) if R.random() < 0.7 else float(R.randint(2, 20))
            y = float(R.randint(2, 20)) if R.random() < 0.7 else R.choice(halves)
            if R.random() < 0.5:
                x, y = y, x
            xs, ys = fmt_lit(x), fmt_lit(y)
            name = R.choice(NAMES)
            res = {"+": x + y, "-": x - y, "*": x * y, "/": x / y}
            correct = fmt_double(res[op])
            wrong = pick_wrong(correct, [fmt_double(res[o]) for o in "+-*/" if o != op])
            if not wrong or max(len(w) for w in wrong) > 12:
                return False
            expr = f"{xs} {op} {ys}"
            return b.add("dt-double-arith", 2, code=f"double {name} = {expr};", sk_body=val_q(name)[0], en_body=val_q(name)[1],
                         answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                         sk_expl=EXPR_EXPL[0] % (expr, correct, name), en_expl=EXPR_EXPL[1] % (expr, correct, name),
                         verify={"type": "value", "expr": name, "expected": correct})
        before = b.count("dt-double-arith")
        fill(b, "dt-double-arith", before + 1, make)

    # ---- dt-string-concat
    pairs = [("Ahoj", " svet"), ("Dobré", " ráno"), ("Dobrý", " deň"), ("Pekný", " deň"), ("Môj", " program"),
             ("Zelená", " lúka"), ("Hello", " world"), ("Veselé", " Vianoce"), ("Malý", " pes"), ("Čierna", " mačka"),
             ("Nový", " rok"), ("Stará", " mama"), ("Modré", " more"), ("Biely", " sneh"), ("Rýchle", " auto"),
             ("Moja", " trieda"), ("Prvý", " krok"), ("Dobrá", " práca"), ("Teplý", " čaj"), ("Žltý", " citrón"),
             ("Tvoj", " kód"), ("Letné", " prázdniny"), ("Veľký", " hrad"), ("Studená", " voda"), ("Nočná", " obloha"),
             ("Vysoké", " Tatry")]
    R.shuffle(pairs)
    for w1, w2 in pairs:
        if b.count("dt-string-concat") >= 25:
            break
        name = R.choice(["text", "veta", "sprava", "nazov", "pozdrav", "slovo", "meno"])
        joined = w1 + w2
        answers = [code_ans(cs_string(joined)), code_ans(cs_string(w1 + w2.strip())), code_ans(cs_string(w1)), "`string`"]
        b.add("dt-string-concat", 2, code=f"string {name} = {cs_string(w1)} + {cs_string(w2)};",
              sk_body=val_q(name)[0], en_body=val_q(name)[1], answers=answers,
              sk_expl=f"Operátor `+` pri reťazcoch spája texty. Spojením `{cs_string(w1)}` a `{cs_string(w2)}` vznikne `{cs_string(joined)}` – medzera je súčasťou druhého textu.",
              en_expl=f"With strings, the `+` operator joins the texts. Joining `{cs_string(w1)}` and `{cs_string(w2)}` gives `{cs_string(joined)}` – the space is part of the second text.",
              verify={"type": "value", "expr": name})

    # ---- dt-string-index
    words = ["Robot", "Program", "Bratislava", "Tatry", "Dunaj", "Kocka", "Lampa", "Zemiak", "Jablko", "Hrusky",
             "Stolicka", "Okno", "Pocitac", "Telefon", "Kniha", "Lavica", "Ceruzka", "Trieda", "Skola", "Kalkulacka"]
    def idx():
        w = R.choice(words)
        i = R.randint(0, len(w) - 2)
        c = w[i]
        nxt = w[i + 1] if w[i + 1] != c else (w[i - 1] if i > 0 and w[i - 1] != c else None)
        if nxt is None:
            return False
        name = R.choice(["znak", "pismeno", "z", "c"])
        answers = [code_ans(cs_char(c)), code_ans(cs_string(c)), code_ans(cs_char(nxt)), "`char`"]
        if len(set(answers)) < 4:
            return False
        return b.add("dt-string-index", 2, code=f"string slovo = {cs_string(w)};\nchar {name} = slovo[{i}];",
                     sk_body=val_q(name)[0], en_body=val_q(name)[1], answers=answers,
                     sk_expl=f"Indexovanie reťazca začína od `0`. Na indexe `{i}` v texte `{cs_string(w)}` sa nachádza znak `{cs_char(c)}`, preto ho bude obsahovať premenná `{name}`.",
                     en_expl=f"String indexing starts at `0`. At index `{i}` in `{cs_string(w)}` is the character `{cs_char(c)}`, so the variable `{name}` will contain it.",
                     verify={"type": "value", "expr": name})
    fill(b, "dt-string-index", 25, idx)
    return b


def fmt_lit(x: float) -> str:
    """double literal as written in code: 4 stays 4, 7.5 stays 7.5."""
    return fmt_double(x)


# ======================================================================= hard (3)
def cs_plus(a, b):
    if isinstance(a, str) or isinstance(b, str):
        return f"{a}{b}"
    return a + b


def hard():
    b = Batch(f"{DATE}_data-types_3", "data-types", DATE)

    # ---- dt-plus-mixed
    def mixed():
        kind = R.choice(["SII", "IIS", "ISI", "SII_letter", "IIS_letter", "ISS", "SIS"])
        n = [R.randint(1, 9) for _ in range(3)]
        if kind == "SII":
            ops = [str(n[0]), n[1], n[2]]
        elif kind == "IIS":
            ops = [n[0], n[1], str(n[2])]
        elif kind == "ISI":
            ops = [n[0], str(n[1]), n[2]]
        elif kind == "SII_letter":
            ops = [R.choice("ABXY"), n[1], n[2]]
        elif kind == "IIS_letter":
            ops = [n[0], n[1], R.choice("ABXY")]
        elif kind == "ISS":
            ops = [n[0], str(n[1]), str(n[2])]
        else:
            ops = [str(n[0]), n[1], str(n[2])]
        ltr = cs_plus(cs_plus(ops[0], ops[1]), ops[2])
        rtl = cs_plus(ops[0], cs_plus(ops[1], ops[2]))
        correct = str(ltr)
        joined = "".join(str(o) for o in ops)
        cands = [cs_string(joined), cs_string(rtl)]
        if all(not isinstance(o, str) or o.isdigit() for o in ops):
            total = sum(int(o) for o in ops)
            cands += [cs_string(str(total)), str(total)]
        cands += [cs_string(str(ops[0])), cs_string(joined[::-1])]
        wrong = pick_wrong(cs_string(correct), cands)
        if not wrong:
            return False
        lit = lambda o: cs_string(o) if isinstance(o, str) else str(o)
        expr = " + ".join(lit(o) for o in ops)
        name = R.choice(["text", "vysledok", "s", "spojenie"])
        step1 = cs_plus(ops[0], ops[1])
        s1 = f"{lit(ops[0])} + {lit(ops[1])} = {lit(step1)}"
        s2 = f"{lit(step1)} + {lit(ops[2])} = {cs_string(correct)}"
        return b.add("dt-plus-mixed", 3, code=f"string {name} = {expr};", sk_body=val_q(name)[0], en_body=val_q(name)[1],
                     answers=[code_ans(cs_string(correct))] + [code_ans(w) for w in wrong],
                     sk_expl=f"Operátor `+` sa vyhodnocuje zľava doprava. Kým sú oba operandy čísla, sčítava; keď je jeden z nich reťazec, spája text. Najprv `{s1}`, potom `{s2}`.",
                     en_expl=f"The `+` operator is evaluated left to right. While both operands are numbers it adds them; once one of them is a string it joins text. First `{s1}`, then `{s2}`.",
                     verify={"type": "value", "expr": name})
    fill(b, "dt-plus-mixed", 25, mixed)

    # ---- dt-compile-error
    invalid = [("int x = 3.5;", "double", "int"), ('char c = "A";', "string", "char"), ("string s = 5;", "int", "string"),
               ("bool b = 1;", "int", "bool"), ('int n = "5";', "string", "int"), ("string s = 'A';", "char", "string"),
               ('bool b = "true";', "string", "bool"), ('double d = "2.5";', "string", "double"), ("char c = 65;", "int", "char"),
               ("int x = true;", "bool", "int"), ("char c = 'AB';", None, "char")]
    tricky = ["double d = 5;", "int n = 'A';", 'string s = "5";', "char c = '5';", "double d = 'A';", "double d = 7 / 2;", 'string s = "true";']
    normal = ["int x = 10;", "bool b = false;", 'string s = "Ahoj";', "char c = 'z';", "double d = 2.5;", "int y = -7;", "bool ok = true;"]
    def ce():
        bad, frm, to = R.choice(invalid)
        valid = R.sample(tricky, R.choice([1, 2]))
        valid += R.sample([v for v in normal if v not in valid], 3 - len(valid))
        R.shuffle(valid)
        if frm is None:
            sk_reason = f"`{bad}` sa nedá preložiť: v jednoduchých úvodzovkách môže byť iba jeden znak."
            en_reason = f"`{bad}` does not compile: single quotes can hold only one character."
        else:
            sk_reason = f"`{bad}` sa nedá preložiť: hodnotu typu `{frm}` nemožno priradiť do premennej typu `{to}`."
            en_reason = f"`{bad}` does not compile: a value of type `{frm}` cannot be assigned to a variable of type `{to}`."
        tr = [v for v in valid if v in tricky]
        if tr:
            sk_reason += f" Pozor: `{tr[0]}` je v poriadku."
            en_reason += f" Note: `{tr[0]}` is fine."
        return b.add("dt-compile-error", 3, code=None,
                     sk_body="Ktorý z týchto riadkov spôsobí chybu pri preklade?", en_body="Which of these lines causes a compile error?",
                     answers=[code_ans(bad)] + [code_ans(v) for v in valid], sk_expl=sk_reason, en_expl=en_reason,
                     verify={"type": "which-line", "expect": "compile-error"})
    fill(b, "dt-compile-error", 25, ce)

    # ---- dt-trace
    def trace():
        x0 = R.randint(2, 20)
        steps = []
        x = x0
        nlines = R.choice([3, 4])
        ops_used = R.sample(["+", "-", "*", "/", "%"], nlines if nlines <= 5 else 5)
        for op in ops_used:
            n = R.randint(2, 5) if op in "*/%" else R.randint(1, 9)
            nx = {"+": x + n, "-": x - n, "*": x * n, "/": x // n if x >= 0 else None, "%": x % n if x >= 0 else None}[op]
            if nx is None or nx < 0:
                return False
            steps.append((op, n)); x = nx
        if not 0 <= x <= 100:
            return False
        def run(skip=None):
            v = x0
            for k, (op, n) in enumerate(steps):
                if k == skip:
                    continue
                v = {"+": v + n, "-": v - n, "*": v * n, "/": int(v / n), "%": int(v - n * int(v / n))}[op]
            return v
        correct = run()
        wrong = pick_wrong(correct, [run(k) for k in range(len(steps))][::-1], fallback=[correct + 1, correct - 1, correct + 2])
        name = "x"
        code = f"int x = {x0};\n" + "\n".join(f"x = x {op} {n};" for op, n in steps)
        vals = [x0]
        for k in range(len(steps)):
            vals.append(run_until(x0, steps, k))
        chain = " → ".join(str(v) for v in vals)
        return b.add("dt-trace", 3, code=code,
                     sk_body="{code}\nAkú hodnotu bude mať premenná `x` na konci?", en_body="{code}\nWhat value will the variable `x` have at the end?",
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Riadky sa vykonávajú postupne: {chain}. Na konci má `x` hodnotu `{correct}`.",
                     en_expl=f"The lines run one after another: {chain}. At the end, `x` is `{correct}`.",
                     verify={"type": "value", "expr": name})
    fill(b, "dt-trace", 25, trace)

    # ---- dt-string-index-hard
    texts = ["Ahoj svet", "Dobry den", "Mam rad C#", "Pekny den", "Ja som tu", "Hello world", "Malý pes", "Nový rok",
             "Kód je hotový", "Skúška z C#", "Dnes prší", "Zajtra je piatok", "Moja trieda", "Prvý program", "Tatry sú krásne"]
    def sih():
        t = R.choice(texts)
        L = len(t)
        form = R.choice(["num", "len-k", "len-k", "half"])
        if form == "num":
            i = R.randint(0, L - 1); expr = str(i)
        elif form == "len-k":
            k = R.randint(1, min(6, L)); i = L - k; expr = f"text.Length - {k}"
        else:
            i = L // 2; expr = "text.Length / 2"
        c = t[i]
        if R.random() < 0.25 and " " in t and form == "num":
            i = t.index(" "); c = " "; expr = str(i)
        neigh = []
        for j in [i + 1, i - 1, i + 2, i - 2, i + 3]:
            if 0 <= j < L and t[j] != c and cs_char(t[j]) not in neigh:
                neigh.append(cs_char(t[j]))
        if len(neigh) < 2:
            return False
        answers = [code_ans(cs_char(c)), code_ans(neigh[0]), code_ans(neigh[1]), code_ans(cs_string(c))]
        if len(set(answers)) < 4:
            return False
        name = R.choice(["znak", "z", "pismeno"])
        sk_i = f"Index `{expr}` = `{i}`" if expr != str(i) else f"Index `{i}`"
        en_i = f"Index `{expr}` = `{i}`" if expr != str(i) else f"Index `{i}`"
        shown = "medzera" if c == " " else cs_char(c)
        shown_en = "a space" if c == " " else cs_char(c)
        return b.add("dt-string-index-hard", 3, code=f"string text = {cs_string(t)};\nchar {name} = text[{expr}];",
                     sk_body=val_q(name)[0], en_body=val_q(name)[1], answers=answers,
                     sk_expl=f"Text `{cs_string(t)}` má dĺžku `{L}` (medzera sa tiež počíta), indexy idú od `0` po `{L - 1}`. {sk_i}, na ňom je {'medzera' if c == ' ' else 'znak `' + shown + '`'}.",
                     en_expl=f"The text `{cs_string(t)}` has length `{L}` (the space counts too); indexes go from `0` to `{L - 1}`. {en_i}, and there is {'a space' if c == ' ' else 'the character `' + shown_en + '`'}.",
                     verify={"type": "value", "expr": name, "expected": cs_char(c)})
    fill(b, "dt-string-index-hard", 25, sih)
    return b


def run_until(x0, steps, last):
    v = x0
    for k, (op, n) in enumerate(steps):
        v = {"+": v + n, "-": v - n, "*": v * n, "/": int(v / n), "%": int(v - n * int(v / n))}[op]
        if k == last:
            return v
    return v


if __name__ == "__main__":
    medium().write()
    hard().write()
