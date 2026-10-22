"""Generator for topic cycles (36 templates × 25)."""
import random
from common import Batch, fill, code_ans, pick_wrong

R = random.Random(20261024)
DATE = "2026-10-22"
OUT_Q = ("{code}\nČo vypíše tento kód?", "{code}\nWhat does this code print?")
TIMES_A = ("{code}\nKoľkokrát sa vypíše `A`?", "{code}\nHow many times is `A` printed?")
NOTHING = ("Nič", "Nothing")
INF = ("Nekonečný cyklus", "Infinite loop")
COMPILE = ("Chyba pri preklade", "Compile error")
W = lambda s: f'Console.Write("{s}");'


def val_q(name, end=True):
    e = " na konci" if end else ""
    e2 = " at the end" if end else ""
    return f"{{code}}\nAkú hodnotu bude mať premenná `{name}`{e}?", f"{{code}}\nWhat value will the variable `{name}` have{e2}?"


def text_answers(answers):
    sk = [a[0] if isinstance(a, tuple) else a for a in answers]
    en = [a[1] if isinstance(a, tuple) else a for a in answers]
    return sk, (en if en != sk else None)


def ca(x):
    return x if isinstance(x, tuple) else code_ans(x)


def lst(vals):
    return ", ".join(str(v) for v in vals) if vals else "–"


def cmpf(op):
    return {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b,
            "!=": lambda a, b: a != b}[op]


def for_values(start, op, end, step):
    vals, i = [], start
    while cmpf(op)(i, end) and len(vals) < 1000:
        vals.append(i); i += step
    return vals, i


def main():
    b = Batch(f"{DATE}_cycles", "cycles", DATE)

    # =================================================================== EASY
    def for_count():
        n = R.randint(2, 8)
        start, op = R.choice([(0, "<"), (1, "<=")])
        vals, _ = for_values(start, op, n, 1)
        cnt = len(vals)
        ch, v = R.choice(["A", "B", "X", "*", "#"]), R.choice(["i", "k", "j"])
        code = f"for (int {v} = {start}; {v} {op} {n}; {v}++)\n    {W(ch)}"
        wrong = pick_wrong(cnt, [cnt - 1, cnt + 1, 0, n + 1])
        return b.add("cy-for-count", 1, code=code, sk_body=TIMES_A[0].replace("`A`", f"`{ch}`"), en_body=TIMES_A[1].replace("`A`", f"`{ch}`"),
                     answers=[code_ans(cnt)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Premenná `{v}` nadobudne hodnoty {lst(vals)}, teda telo sa vykoná {cnt}-krát.",
                     en_expl=f"The variable `{v}` takes the values {lst(vals)}, so the body runs {cnt} times.",
                     verify={"type": "output", "expected": ch * cnt})
    fill(b, "cy-for-count", 25, for_count)

    def for_print():
        a = R.choice([0, 1, 2]); op = R.choice(["<", "<="]); e = R.randint(a + 2, 8)
        vals, _ = for_values(a, op, e, 1)
        out = "".join(map(str, vals))
        more = out + str(vals[-1] + 1)
        less = out[:-1]
        shift = "".join(str(v) for v in range(a - 1 if a > 0 else a + 1, vals[-1] + 1)) if a > 0 else out[1:] + str(vals[-1] + 1)
        wrong = pick_wrong(out, [less, more, shift, out[1:]])
        code = f"for (int i = {a}; i {op} {e}; i++)\n    Console.Write(i);"
        cond = f"i {op} {e}"
        return b.add("cy-for-print", 1, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Cyklus vypíše hodnoty `i` od {a}, kým platí `{cond}`: {lst(vals)}.",
                     en_expl=f"The loop prints `i` from {a} while `{cond}` holds: {lst(vals)}.",
                     verify={"type": "output"})
    fill(b, "cy-for-print", 25, for_print)

    def for_down():
        a = R.randint(3, 9); op = R.choice([">", ">="]); e = R.randint(0, a - 2)
        vals, _ = for_values(a, op, e, -1)
        out = "".join(map(str, vals))
        wrong = pick_wrong(out, [out[::-1], out + str(vals[-1] - 1) if vals[-1] > 0 else out[1:], out[:-1], out[1:]])
        code = f"for (int i = {a}; i {op} {e}; i--)\n    Console.Write(i);"
        return b.add("cy-for-down", 1, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`i--` zmenšuje `i` o 1; cyklus beží, kým platí `i {op} {e}`: {lst(vals)}.",
                     en_expl=f"`i--` decreases `i` by 1; the loop runs while `i {op} {e}` holds: {lst(vals)}.",
                     verify={"type": "output"})
    fill(b, "cy-for-down", 25, for_down)

    def for_step():
        k = R.choice([2, 3, 5]); a = R.choice([0, 1, k]); e = a + k * R.randint(3, 5) + R.choice([0, 1])
        vals, stop = for_values(a, "<", e, k)
        out = " ".join(map(str, vals))
        incl = " ".join(map(str, vals + [stop])) if stop == e else " ".join(map(str, vals + [stop]))
        step1 = " ".join(str(v) for v in range(a, a + len(vals)))
        fromk = " ".join(map(str, vals[1:]))
        wrong = pick_wrong(out, [incl, step1, fromk])
        if not wrong:
            return False
        code = f"for (int i = {a}; i < {e}; i = i + {k})\n    Console.Write(i + \" \");"
        return b.add("cy-for-step", 1, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Krok `i = i + {k}` zväčší `i` o {k}: {lst(vals)}. Hodnota {stop} už podmienku `i < {e}` nesplní.",
                     en_expl=f"The step `i = i + {k}` increases `i` by {k}: {lst(vals)}. The value {stop} no longer satisfies `i < {e}`.",
                     verify={"type": "output"})
    fill(b, "cy-for-step", 25, for_step)

    PARTS = [("inicializácia", "initialisation", 0), ("podmienka", "condition", 1), ("krok", "step", 2)]
    def for_parts():
        var = R.choice(["i", "k", "j", "n"])
        if R.random() < 0.5:
            s, e = R.randint(0, 2), R.randint(5, 20)
            parts = [f"int {var} = {s}", f"{var} {R.choice(['<', '<='])} {e}", R.choice([f"{var}++", f"{var} = {var} + 2"])]
        else:
            s, e = R.randint(8, 20), R.randint(0, 2)
            parts = [f"int {var} = {s}", f"{var} {R.choice(['>', '>='])} {e}", R.choice([f"{var}--", f"{var} = {var} - 2"])]
        psk, pen, idx = R.choice(PARTS)
        correct = parts[idx]
        wrong = [p for k, p in enumerate(parts) if k != idx] + ["for"]
        header = "; ".join(parts)
        return b.add("cy-for-parts", 1, code=None,
                     sk_body=f"V cykle `for ({header})` čo je **{psk}**?", en_body=f"In the loop `for ({header})`, what is the **{pen}**?",
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl="Hlavička `for` má tri časti oddelené bodkočiarkou: inicializácia, podmienka, krok.",
                     en_expl="A `for` header has three parts separated by semicolons: initialisation, condition, step.",
                     verify={"type": "none"})
    fill(b, "cy-for-parts", 25, for_parts)

    def while_simple():
        if R.random() < 0.75:
            a = R.randint(0, 3); op = R.choice(["<", "<="]); e = R.randint(a + 2, 8); step = 1
        else:
            a = R.randint(4, 9); op = R.choice([">", ">="]); e = R.randint(0, a - 2); step = -1
        vals, _ = for_values(a, op, e, step)
        out = "".join(map(str, vals))
        incstr = "i++;" if step == 1 else "i--;"
        code = f"int i = {a};\nwhile (i {op} {e})\n{{\n    Console.Write(i);\n    {incstr}\n}}"
        after = "".join(str(v + step) for v in vals)
        wrong = pick_wrong(out, [out[:-1], out + str(vals[-1] + step), after])
        if not wrong:
            return False
        return b.add("cy-while-simple", 1, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Telo sa opakuje, kým platí `i {op} {e}`: {lst(vals)}.",
                     en_expl=f"The body repeats while `i {op} {e}` holds: {lst(vals)}.",
                     verify={"type": "output"})
    fill(b, "cy-while-simple", 25, while_simple)

    def while_never():
        a = R.randint(5, 20)
        op, e = R.choice([("<", R.randint(0, a)), ("<=", R.randint(0, a - 1)), (">", R.randint(a, a + 10)), ("==", a + R.randint(1, 5))])
        inc = "i++;" if op in ("<", "<=") else "i--;"
        code = f"int i = {a};\nwhile (i {op} {e})\n{{\n    Console.Write(i);\n    {inc}\n}}\n{W('K')}"
        sk, en = text_answers([code_ans("K"), code_ans(f"{a}K"), INF, NOTHING])
        return b.add("cy-while-never", 1, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"Podmienka `i {op} {e}` neplatí hneď na začiatku (`i` je {a}), telo sa nevykoná ani raz. Vypíše sa iba riadok za cyklom.",
                     en_expl=f"The condition `i {op} {e}` is false right at the start (`i` is {a}), so the body never runs. Only the line after the loop prints.",
                     verify={"type": "output"})
    fill(b, "cy-while-never", 25, while_never)

    def while_count():
        k = R.choice([1, 1, 2, 3]); a = R.randint(0, 5); op = R.choice(["<", "<="]); e = a + R.randint(2, 8 * k)
        vals, stop = for_values(a, op, e, k)
        if not 2 <= len(vals) <= 8:
            return False
        cnt = len(vals)
        code = f"int pocet = 0;\nint i = {a};\nwhile (i {op} {e})\n{{\n    pocet = pocet + 1;\n    i = i + {k};\n}}"
        wrong = pick_wrong(cnt, [cnt - 1, cnt + 1, e - a, e])
        return b.add("cy-while-count", 1, code=code,
                     sk_body="{code}\nKoľkokrát sa vykoná telo cyklu (akú hodnotu bude mať `pocet`)?",
                     en_body="{code}\nHow many times does the loop body run (what value will `pocet` have)?",
                     answers=[code_ans(cnt)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`i` postupne nadobúda {lst(vals)}; pri hodnote {stop} podmienka neplatí. Telo sa vykoná {cnt}-krát.",
                     en_expl=f"`i` takes the values {lst(vals)}; at {stop} the condition fails. The body runs {cnt} times.",
                     verify={"type": "value", "expr": "pocet"})
    fill(b, "cy-while-count", 25, while_count)

    KW = {
        "while": [("opakuje telo, kým platí podmienka", "repeats the body while a condition holds"),
                  ("opakuje príkazy dovtedy, kým je podmienka pravdivá", "repeats statements as long as the condition is true")],
        "for": [("opakuje telo s počítadlom (inicializácia, podmienka a krok v jednom riadku)", "repeats the body with a counter (initialisation, condition and step in one line)"),
                ("cyklus, ktorý má inicializáciu, podmienku a krok v hlavičke", "a loop with the initialisation, condition and step in its header")],
        "break": [("okamžite ukončí celý cyklus", "ends the whole loop immediately"),
                  ("vyskočí z cyklu, aj keď podmienka ešte platí", "jumps out of the loop even if the condition still holds")],
        "continue": [("preskočí zvyšok tela a pokračuje ďalšou iteráciou", "skips the rest of the body and goes to the next iteration"),
                     ("skočí na ďalšie opakovanie cyklu bez dokončenia tela", "jumps to the next repetition without finishing the body")],
    }
    FAKES = [("ukončí celý program", "ends the whole program"), ("zopakuje aktuálnu iteráciu ešte raz", "repeats the current iteration once more"),
             ("pozastaví program na jednu sekundu", "pauses the program for one second")]
    QFORM = [("Na čo slúži `{k}`?", "What is `{k}` used for?"), ("Čo robí príkaz `{k}` v cykle?", "What does `{k}` do in a loop?")]
    def keyword_purpose():
        k = R.choice(list(KW)); qf = R.choice(QFORM)
        correct = R.choice(KW[k])
        others = [R.choice(KW[o]) for o in KW if o != k]
        R.shuffle(others)
        wrong = others[:2] + [R.choice(FAKES)] if R.random() < 0.6 else others[:3]
        sk, en = text_answers([correct] + wrong)
        return b.add("cy-keyword-purpose", 1, code=None, sk_body=qf[0].format(k=k), en_body=qf[1].format(k=k), answers=sk, en_answers=en,
                     sk_expl=f"`{k}`: {KW[k][0][0]}.", en_expl=f"`{k}`: {KW[k][0][1]}.", verify={"type": "none"})
    fill(b, "cy-keyword-purpose", 25, keyword_purpose)

    PURP = {
        "break": [("ukončí cyklus a program pokračuje riadkom za cyklom", "ends the loop, and the program continues after it"), ("okamžite ukončí celý cyklus", "ends the whole loop immediately"), ("vyskočí z cyklu skôr, než prestane platiť podmienka", "leaves the loop before its condition stops holding")],
        "continue": [("ukončí iba aktuálnu iteráciu, cyklus beží ďalej", "ends only the current iteration; the loop keeps running"), ("preskočí zvyšok tela cyklu a pokračuje ďalšou iteráciou", "skips the rest of the loop body and goes to the next iteration"), ("vynechá zvyšok aktuálneho opakovania", "skips the rest of the current repetition")],
        "while": [("opakuje kód, pokiaľ platí podmienka kontrolovaná pred každým opakovaním", "repeats code as long as the condition, checked before every repetition, holds"), ("opakuje telo, kým platí podmienka (bez počítadla v hlavičke)", "repeats the body while a condition holds (no counter in the header)"), ("je cyklus, ktorý má v hlavičke iba podmienku", "is a loop with only a condition in its header")],
        "for": [("sa najčastejšie používa na prechádzanie čísel od–do s počítadlom", "is most often used to go through numbers from–to with a counter"), ("má inicializáciu, podmienku a krok v jednom riadku", "has the initialisation, condition and step in one line"), ("je najvhodnejší, keď vopred vieme počet opakovaní", "is the best fit when we know the number of repetitions in advance")],
    }
    QP = [("Ako sa volá príkaz, ktorý {p}?", "What is the name of the statement that {p}?"), ("Ktorý príkaz {p}?", "Which statement {p}?"), ("Ktoré kľúčové slovo {p}?", "Which keyword {p}?")]
    def purpose_keyword():
        k = R.choice(list(PURP)); p = R.choice(PURP[k]); qf = R.choice(QP)
        wrong = [o for o in PURP if o != k]
        R.shuffle(wrong)
        return b.add("cy-purpose-keyword", 1, code=None, sk_body=qf[0].format(p=p[0]), en_body=qf[1].format(p=p[1]),
                     answers=[code_ans(k)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`{k}` {p[0]}.", en_expl=f"`{k}` {p[1]}.", verify={"type": "none"})
    fill(b, "cy-purpose-keyword", 25, purpose_keyword)

    def sum_():
        n = R.randint(3, 6); form = R.choice(["i", "i", "i * 2", "2", "i + 1", "i * i"]); s0 = R.choice([0, 1, 1, 2])
        terms = [eval(form, {"i": i}) for i in range(s0, n + 1)]
        s = sum(terms)
        steps, acc = [], 0
        for t in terms:
            acc += t; steps.append(str(acc))
        code = f"int sucet = 0;\nfor (int i = {s0}; i <= {n}; i++)\n    sucet = sucet + {form};"
        wrong = pick_wrong(s, [s - terms[-1], s + eval(form, {"i": n + 1}), n, s - terms[0]])
        return b.add("cy-sum", 1, code=code, sk_body=val_q("sucet")[0], en_body=val_q("sucet")[1],
                     answers=[code_ans(s)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`sucet` postupne: {', '.join(steps)}.", en_expl=f"`sucet` step by step: {', '.join(steps)}.",
                     verify={"type": "value", "expr": "sucet"})
    fill(b, "cy-sum", 25, sum_)

    def for_to_while():
        a = R.randint(0, 2); op = R.choice(["<", "<="]); e = R.randint(a + 2, 8)
        code = f"for (int i = {a}; i {op} {e}; i++)\n    Console.Write(i);"
        good = f"int i = {a}; while (i {op} {e}) {{ Console.Write(i); i++; }}"
        bad_start = f"int i = {a + 1}; while (i {op} {e}) {{ Console.Write(i); i++; }}"
        other = "<=" if op == "<" else "<"
        bad_cond = f"int i = {a}; while (i {other} {e}) {{ Console.Write(i); i++; }}"
        bad_order = f"int i = {a}; while (i {op} {e}) {{ i++; Console.Write(i); }}"
        return b.add("cy-for-to-while", 1, code=code,
                     sk_body="{code}\nKtorý cyklus `while` robí to isté?", en_body="{code}\nWhich `while` loop does the same?",
                     answers=[code_ans(good), code_ans(bad_start), code_ans(bad_cond), code_ans(bad_order)],
                     sk_expl="Inicializácia ide pred `while`, podmienka do zátvorky a krok na koniec tela.",
                     en_expl="The initialisation goes before `while`, the condition into the brackets, and the step at the end of the body.",
                     verify={"type": "which-input", "input": "{answer}", "useCode": False,
                             "output": "".join(map(str, for_values(a, op, e, 1)[0]))})
    fill(b, "cy-for-to-while", 25, for_to_while)

    # =================================================================== MEDIUM
    def lt_vs_le():
        n = R.randint(3, 9)
        start, op = R.choice([(1, "<"), (0, "<="), (2, "<="), (2, "<")])
        if R.random() < 0.25:
            code = f"for (int i = {n}; i >= 0; i--)\n    {W('A')}"; vals = list(range(n, -1, -1))
        else:
            code = f"for (int i = {start}; i {op} {n}; i++)\n    {W('A')}"; vals, _ = for_values(start, op, n, 1)
        cnt = len(vals)
        if cnt == 0:
            return False
        wrong = pick_wrong(cnt, [n, n - 1, n + 1, cnt + 1, cnt - 1])
        return b.add("cy-lt-vs-le", 2, code=code, sk_body=TIMES_A[0], en_body=TIMES_A[1],
                     answers=[code_ans(cnt)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`i` nadobúda {lst(vals)}, to je {cnt} hodnôt.", en_expl=f"`i` takes the values {lst(vals)}, that's {cnt} values.",
                     verify={"type": "output", "expected": "A" * cnt})
    fill(b, "cy-lt-vs-le", 25, lt_vs_le)

    def i_after():
        a = R.randint(0, 3); e = R.randint(a + 2, 10); k = R.choice([1, 1, 2, 3]); op = R.choice(["<", "<="])
        vals, stop = for_values(a, op, e, k)
        step = "i++" if k == 1 else f"i = i + {k}"
        if R.random() < 0.7:
            code = f"int i;\nfor (i = {a}; i {op} {e}; {step})\n{{\n}}"
        else:
            code = f"int i = {a};\nwhile (i {op} {e})\n{{\n    {step};\n}}"
        wrong = pick_wrong(stop, [vals[-1], stop + k, a, e])
        return b.add("cy-i-after-loop", 2, code=code, sk_body=val_q("i", False)[0].replace("?", " po skončení cyklu?"),
                     en_body=val_q("i", False)[1].replace("?", " after the loop?"),
                     answers=[code_ans(stop)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Cyklus skončí, keď podmienka `i {op} {e}` prvýkrát neplatí – vtedy má `i` hodnotu `{stop}` (posledná hodnota v tele bola {vals[-1]}).",
                     en_expl=f"The loop ends when `i {op} {e}` first fails – at that moment `i` is `{stop}` (the last value inside the body was {vals[-1]}).",
                     verify={"type": "value", "expr": "i"})
    fill(b, "cy-i-after-loop", 25, i_after)

    CONDS = [("i % 2 == 0", lambda i: i % 2 == 0, "párne", "even"), ("i % 2 == 1", lambda i: i % 2 == 1, "nepárne", "odd"),
             ("i % 3 == 0", lambda i: i % 3 == 0, "deliteľné 3", "divisible by 3")]
    def if_in_loop():
        a = R.randint(0, 2); e = R.randint(6, 9)
        if R.random() < 0.7:
            c, f, _, _ = R.choice(CONDS)
        else:
            m = R.randint(a + 1, e - 1); c, f = f"i > {m}", (lambda i, m=m: i > m)
        vals = [i for i in range(a, e + 1) if f(i)]
        compl = [i for i in range(a, e + 1) if not f(i)]
        if len(vals) < 2:
            return False
        out = "".join(map(str, vals))
        wrong = pick_wrong(out, ["".join(map(str, compl)), "".join(str(i) for i in range(a, e + 1)), out[:-1], out[1:]])
        if not wrong:
            return False
        code = f"for (int i = {a}; i <= {e}; i++)\n{{\n    if ({c})\n        Console.Write(i);\n}}"
        return b.add("cy-if-in-loop", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Vypíšu sa iba hodnoty `i`, pre ktoré platí `{c}`: {lst(vals)}.",
                     en_expl=f"Only values of `i` for which `{c}` holds are printed: {lst(vals)}.",
                     verify={"type": "output"})
    fill(b, "cy-if-in-loop", 25, if_in_loop)

    def count_matches():
        n = R.randint(10, 30)
        forms = [(f"i % {k} == 0", lambda i, k=k: i % k == 0) for k in (3, 4, 5, 7)] + \
                [(f"i > {m}", lambda i, m=m: i > m) for m in (n - 4, n - 7)] + \
                [(f"i % 10 == {d}", lambda i, d=d: i % 10 == d) for d in (3, 7)] + [("i % 2 == 1", lambda i: i % 2 == 1)]
        c, f = R.choice(forms)
        vals = [i for i in range(1, n + 1) if f(i)]
        cnt = len(vals)
        if cnt < 2:
            return False
        code = f"int pocet = 0;\nfor (int i = 1; i <= {n}; i++)\n{{\n    if ({c})\n        pocet = pocet + 1;\n}}"
        wrong = pick_wrong(cnt, [cnt + 1, cnt - 1, sum(vals), n])
        return b.add("cy-count-matches", 2, code=code, sk_body=val_q("pocet")[0], en_body=val_q("pocet")[1],
                     answers=[code_ans(cnt)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Podmienku `{c}` spĺňajú čísla {lst(vals)}, to je {cnt}.",
                     en_expl=f"The numbers {lst(vals)} satisfy `{c}`, that's {cnt}.",
                     verify={"type": "value", "expr": "pocet"})
    fill(b, "cy-count-matches", 25, count_matches)

    def product():
        form = R.choice(["fact", "pow", "pow", "odd"])
        if form == "fact":
            s0, n = R.choice([1, 2]), R.randint(3, 6)
            code = f"int f = 1;\nfor (int i = {s0}; i <= {n}; i++)\n    f = f * i;"
            factors = list(range(s0, n + 1))
        elif form == "pow":
            k, n = R.choice([2, 3, 4, 5]), R.randint(2, 5)
            if k ** n > 1000:
                return False
            code = f"int f = 1;\nfor (int i = 0; i < {n}; i++)\n    f = f * {k};"
            factors = [k] * n
        else:
            n = R.choice([5, 7, 9])
            code = f"int f = 1;\nfor (int i = 1; i <= {n}; i = i + 2)\n    f = f * i;"
            factors = list(range(1, n + 1, 2))
        res, steps = 1, []
        for x in factors:
            res *= x; steps.append(str(res))
        less = res // factors[-1]
        more = res * (factors[-1] + (2 if form == "odd" else 1)) if form != "pow" else res * factors[-1]
        wrong = pick_wrong(res, [less, more, sum(factors), 0])
        return b.add("cy-product", 2, code=code, sk_body=val_q("f")[0], en_body=val_q("f")[1],
                     answers=[code_ans(res)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`f` postupne: {', '.join(steps)}.", en_expl=f"`f` step by step: {', '.join(steps)}.",
                     verify={"type": "value", "expr": "f"})
    fill(b, "cy-product", 25, product)

    def doubling():
        x0 = R.randint(1, 7); op, k = R.choice([("*", 2), ("*", 2), ("*", 3), ("+", R.randint(4, 9))]); lim = R.choice([50, 100, 60, 40, 30])
        vals, x, cnt = [x0], x0, 0
        while x < lim:
            x = x * k if op == "*" else x + k; vals.append(x); cnt += 1
        if not 2 <= cnt <= 8:
            return False
        ask_count = R.random() < 0.5
        upd = f"x = x {op} {k};"
        if ask_count:
            code = f"int x = {x0};\nint pocet = 0;\nwhile (x < {lim})\n{{\n    {upd}\n    pocet = pocet + 1;\n}}"
            corr = cnt; wrong = pick_wrong(cnt, [cnt - 1, cnt + 1, x, lim // x0 if x0 else 0])
            name = "pocet"
        else:
            code = f"int x = {x0};\nwhile (x < {lim})\n    {upd}"
            corr = x; wrong = pick_wrong(x, [vals[-2], lim, x * k if op == "*" else x + k])
            name = "x"
        if not wrong:
            return False
        chain = " → ".join(map(str, vals))
        return b.add("cy-doubling", 2, code=code, sk_body=val_q(name)[0], en_body=val_q(name)[1],
                     answers=[code_ans(corr)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`x` postupne: {chain}; pri {x} podmienka `x < {lim}` neplatí" + (f" – telo sa vykonalo {cnt}-krát." if ask_count else "."),
                     en_expl=f"`x` step by step: {chain}; at {x} the condition `x < {lim}` fails" + (f" – the body ran {cnt} times." if ask_count else "."),
                     verify={"type": "value", "expr": name})
    fill(b, "cy-doubling", 25, doubling)

    def cond_and_or():
        lim_i, lim_s = R.randint(6, 12), R.randint(10, 30)
        i, s, steps = 1, 0, []
        while i < lim_i and s < lim_s:
            s += i; i += 1; steps.append(str(s))
        stopped_by = "sucet" if s >= lim_s else "i"
        only_i = sum(range(1, lim_i))
        i2, s2 = 1, 0
        while s2 < lim_s:
            s2 += i2; i2 += 1
        ask = R.choice(["sucet", "i"])
        corr = s if ask == "sucet" else i
        if ask == "sucet":
            wrong = pick_wrong(corr, [only_i, s2, s - (i - 1), s + i])
        else:
            wrong = pick_wrong(corr, [lim_i, i - 1, i + 1, i2])
        if not wrong:
            return False
        code = f"int i = 1;\nint sucet = 0;\nwhile (i < {lim_i} && sucet < {lim_s})\n{{\n    sucet = sucet + i;\n    i++;\n}}"
        part = f"sucet < {lim_s}" if stopped_by == "sucet" else f"i < {lim_i}"
        return b.add("cy-cond-and-or", 2, code=code, sk_body=val_q(ask)[0], en_body=val_q(ask)[1],
                     answers=[code_ans(corr)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Cyklus skončí, keď prestane platiť jedna časť `&&` – tu `{part}`. `sucet` postupne: {', '.join(steps)}; na konci `i` = {i}.",
                     en_expl=f"The loop ends when one side of `&&` stops holding – here `{part}`. `sucet` step by step: {', '.join(steps)}; at the end `i` = {i}.",
                     verify={"type": "value", "expr": ask})
    fill(b, "cy-cond-and-or", 25, cond_and_or)

    def build_string():
        a = R.randint(0, 3); e = R.randint(a + 2, 6); prepend = R.random() < 0.5
        vals = list(range(a, e + 1))
        s = "".join(map(str, vals[::-1] if prepend else vals))
        rev = s[::-1]
        code = f"string s = \"\";\nfor (int i = {a}; i <= {e}; i++)\n    s = " + ("i + s;" if prepend else "s + i;")
        wrong = pick_wrong(f'"{s}"', [f'"{rev}"', str(sum(vals)), f'"{s[1:]}"', f'"{s[:-1]}"'])
        how = ("Každá nová hodnota sa pridá na začiatok", "Each new value is added to the front") if prepend else ("Každá nová hodnota sa pridá na koniec", "Each new value is added to the end")
        steps = []
        acc = ""
        for v in vals:
            acc = str(v) + acc if prepend else acc + str(v); steps.append(f'"{acc}"')
        return b.add("cy-build-string", 2, code=code, sk_body=val_q("s")[0], en_body=val_q("s")[1],
                     answers=[code_ans(f'"{s}"')] + [code_ans(w) for w in wrong],
                     sk_expl=f"{how[0]}: {' → '.join(steps)}.", en_expl=f"{how[1]}: {' → '.join(steps)}.",
                     verify={"type": "value", "expr": "s"})
    fill(b, "cy-build-string", 25, build_string)

    WORDS = ["Robot", "Tatry", "Dunaj", "Lampa", "Kniha", "Okno", "Skola", "Pocitac", "Telefon", "Trieda", "Jablko", "Stromy"]
    def string_walk():
        w = R.choice(WORDS); L = len(w)
        form = R.choice(["back", "back", "even", "odd", "from1"])
        if form == "back":
            idx = list(range(L - 1, -1, -1)); loop = "for (int i = s.Length - 1; i >= 0; i--)"
            wrong_c = [w, w[::-1][:-1], w[::-1][1:]]
        elif form == "even":
            idx = list(range(0, L, 2)); loop = "for (int i = 0; i < s.Length; i = i + 2)"
            wrong_c = ["".join(w[i] for i in range(1, L, 2)), w, w[0::3]]
        elif form == "odd":
            idx = list(range(1, L, 2)); loop = "for (int i = 1; i < s.Length; i = i + 2)"
            wrong_c = ["".join(w[i] for i in range(0, L, 2)), w[1:], w]
        else:
            idx = list(range(1, L)); loop = "for (int i = 1; i < s.Length; i++)"
            wrong_c = [w, w[2:], w[:-1]]
        out = "".join(w[i] for i in idx)
        wrong = pick_wrong(out, wrong_c + [out[:-1], out[1:]])
        if not wrong:
            return False
        code = f"string s = \"{w}\";\n{loop}\n    Console.Write(s[i]);"
        return b.add("cy-string-walk", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(x) for x in wrong],
                     sk_expl=f"Indexy idú {lst(idx)}, teda sa vypíšu znaky {', '.join(w[i] for i in idx)}.",
                     en_expl=f"The indexes go {lst(idx)}, so the characters {', '.join(w[i] for i in idx)} are printed.",
                     verify={"type": "output"})
    fill(b, "cy-string-walk", 25, string_walk)

    def brk():
        a, e = R.randint(0, 2), R.randint(5, 9)
        stop_form = R.choice(["==", "%", ">"])
        k = R.randint(a + 1, e - 1)
        cond = {"==": f"i == {k}", "%": f"i % {R.choice([3, 4])} == 0", ">": f"i > {k}"}[stop_form]
        f = lambda i: eval(cond.replace("&&", "and"), {"i": i})
        before = R.random() < 0.6
        out, cont, stopped = "", "", None
        for i in range(a, e + 1):
            if before and f(i):
                stopped = i; break
            out += str(i)
            if not before and f(i):
                stopped = i; break
        for i in range(a, e + 1):
            if f(i):
                continue
            cont += str(i)
        if stopped is None or out == "" or stopped == e:
            return False
        full = "".join(str(i) for i in range(a, e + 1))
        other = out + str(stopped) if before else out[:-1]
        if other == "":
            other = full[:2]
        wr = pick_wrong(out, [other, cont, full], fallback=[out[:-1] if len(out) > 1 else out + str(int(out[-1]) + 1), full[::-1], out + str(int(out[-1]) + 1)])
        if not wr:
            return False
        sk, en = text_answers([code_ans(out)] + [ca(x) for x in wr])
        body = (f"    if ({cond})\n        break;\n    Console.Write(i);" if before else f"    Console.Write(i);\n    if ({cond})\n        break;")
        code = f"for (int i = {a}; i <= {e}; i++)\n{{\n{body}\n}}"
        extra_sk = "" if before else f" Hodnota {stopped} sa ešte vypíše, lebo `Console.Write` je pred `break`."
        extra_en = "" if before else f" {stopped} is still printed because `Console.Write` comes before `break`."
        return b.add("cy-break", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"`break` okamžite ukončí celý cyklus pri `i = {stopped}`.{extra_sk}",
                     en_expl=f"`break` ends the whole loop immediately at `i = {stopped}`.{extra_en}",
                     verify={"type": "output"})
    fill(b, "cy-break", 25, brk)

    def cont():
        a, e = R.randint(0, 2), R.randint(6, 9)
        cond = R.choice(["i % 2 == 0", "i % 2 == 1", "i % 3 == 0", f"i == {R.randint(a + 1, e - 1)}", f"i < {R.randint(a + 2, e - 2)}"])
        f = lambda i: eval(cond, {"i": i})
        out = "".join(str(i) for i in range(a, e + 1) if not f(i))
        skipped = [i for i in range(a, e + 1) if f(i)]
        brk_out = ""
        for i in range(a, e + 1):
            if f(i):
                break
            brk_out += str(i)
        if not out or not skipped:
            return False
        full = "".join(str(i) for i in range(a, e + 1))
        cands = ["".join(map(str, skipped)), full, brk_out if brk_out else None, out[:-1]]
        wrong = pick_wrong(out, [c for c in cands if c])
        if not wrong:
            return False
        code = f"for (int i = {a}; i <= {e}; i++)\n{{\n    if ({cond})\n        continue;\n    Console.Write(i);\n}}"
        return b.add("cy-continue", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`continue` preskočí zvyšok tela pre {lst(skipped)} a cyklus pokračuje ďalej.",
                     en_expl=f"`continue` skips the rest of the body for {lst(skipped)}, and the loop goes on.",
                     verify={"type": "output"})
    fill(b, "cy-continue", 25, cont)

    INFINITE = [
        ("int i = 0; while (i < 10) { }", "v `while` chýba krok – `i` sa nikdy nezmení", "the `while` has no step – `i` never changes"),
        ("for (int i = 0; i < 10; i = i * 2) { }", "`i` začína na 0 a `0 * 2` je stále 0", "`i` starts at 0 and `0 * 2` is still 0"),
        ("for (int i = 1; i != 10; i = i + 2) { }", "`i` je vždy nepárne, takže nikdy nebude 10", "`i` is always odd, so it never equals 10"),
        ("for (int i = 0; i < 10; ) { }", "v hlavičke chýba krok – `i` zostane 0", "the header has no step – `i` stays 0"),
        ("int x = 7; while (x != 0) { x = x - 2; }", "`x` je stále nepárne, takže nikdy nebude 0", "`x` stays odd, so it never becomes 0"),
        ("int i = 5; while (i > 0) { i = i + 0; }", "`i = i + 0` hodnotu nezmení", "`i = i + 0` doesn't change the value"),
    ]
    FINITE = ["for (int i = 10; i > 0; i = i - 3) { }", "for (int i = 0; i < 10; i = i + 4) { }", "for (int i = 1; i < 100; i = i * 2) { }",
              "int i = 1; while (i < 10) { i = i * 3; }", "int x = 8; while (x != 0) { x = x - 2; }", "for (int i = 20; i >= 0; i = i - 5) { }",
              "int i = 0; while (i < 10) { i++; }"]
    def infinite():
        line, rsk, ren = R.choice(INFINITE)
        wrong = R.sample(FINITE, 3)
        return b.add("cy-infinite", 2, code=None, sk_body="Ktorý z týchto cyklov sa nikdy neskončí?", en_body="Which of these loops never ends?",
                     answers=[code_ans(line)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Nekonečný je `{line}`: {rsk} – podmienka bude platiť stále.",
                     en_expl=f"`{line}` never ends: {ren} – the condition holds forever.",
                     verify={"type": "which-line", "expect": "timeout"})
    fill(b, "cy-infinite", 25, infinite)

    # =================================================================== HARD
    def nested_count():
        a, c = R.randint(2, 6), R.randint(2, 6)
        extra = R.random() < 0.3
        inner = f"        {W('*')}"
        outer_extra = f"\n    {W('|')}" if extra else ""
        code = f"for (int i = 0; i < {a}; i++)\n{{\n    for (int j = 0; j < {c}; j++)\n{inner}{outer_extra}\n}}" if extra else \
               f"for (int i = 0; i < {a}; i++)\n    for (int j = 0; j < {c}; j++)\n        {W('*')}"
        cnt = a * c
        wrong = pick_wrong(cnt, [a + c, cnt + a, cnt - c, c, a * (c + 1)])
        out = ("*" * c + "|") * a if extra else "*" * cnt
        return b.add("cy-nested-count", 3, code=code,
                     sk_body="{code}\nKoľkokrát sa vypíše `*`?", en_body="{code}\nHow many times is `*` printed?",
                     answers=[code_ans(cnt)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Vnútorný cyklus prebehne {c}-krát pre každú z {a} iterácií vonkajšieho: {a} · {c} = {cnt}.",
                     en_expl=f"The inner loop runs {c} times for each of the {a} outer iterations: {a} · {c} = {cnt}.",
                     verify={"type": "output", "expected": out})
    fill(b, "cy-nested-count", 25, nested_count)

    def nested_dep():
        n = R.randint(3, 7)
        form = R.choice(["j = i; j < n", "j < i", "j <= i", "j = i + 1; j < n", "1..i", "j = i; j <= n"])
        outer = f"for (int i = 0; i < {n}; i++)"
        if form == "j = i; j < n":
            header = f"for (int j = i; j < {n}; j++)"; parts = [n - i for i in range(n)]
        elif form == "j < i":
            header = "for (int j = 0; j < i; j++)"; parts = [i for i in range(n)]
        elif form == "j <= i":
            header = "for (int j = 0; j <= i; j++)"; parts = [i + 1 for i in range(n)]
        elif form == "j = i + 1; j < n":
            header = f"for (int j = i + 1; j < {n}; j++)"; parts = [n - i - 1 for i in range(n)]
        elif form == "1..i":
            outer = f"for (int i = 1; i <= {n}; i++)"; header = "for (int j = 1; j <= i; j++)"; parts = [i for i in range(1, n + 1)]
        else:
            outer = f"for (int i = 1; i <= {n}; i++)"; header = f"for (int j = i; j <= {n}; j++)"; parts = [n - i + 1 for i in range(1, n + 1)]
        cnt = sum(parts)
        code = f"int pocet = 0;\n{outer}\n    {header}\n        pocet = pocet + 1;"
        wrong = pick_wrong(cnt, [n * n, cnt + n, cnt - n, n, cnt + 1])
        return b.add("cy-nested-dependent", 3, code=code, sk_body=val_q("pocet")[0], en_body=val_q("pocet")[1],
                     answers=[code_ans(cnt)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Vnútorný cyklus prebehne postupne {' + '.join(map(str, parts))}-krát, spolu {cnt}.",
                     en_expl=f"The inner loop runs {' + '.join(map(str, parts))} times, {cnt} in total.",
                     verify={"type": "value", "expr": "pocet"})
    fill(b, "cy-nested-dependent", 25, nested_dep)

    def nested_break():
        a, c = R.randint(2, 4), R.randint(3, 5)
        kind = R.choice(["eq", "ge", "mod"])
        if kind == "eq":
            k = R.randint(2, c); cs = f"j == {k}"; f = lambda j: j == k
        elif kind == "ge":
            k = R.randint(2, c); cs = f"j >= {k}"; f = lambda j: j >= k
        else:
            k = R.choice([2, 3]); cs = f"j % {k} == 0"; f = lambda j: j % k == 0
        def run(mode):
            out = ""
            for i in range(1, a + 1):
                stop_all = False
                for j in range(1, c + 1):
                    if f(j):
                        if mode == "break":
                            break
                        if mode == "continue":
                            continue
                        if mode == "both":
                            stop_all = True; break
                    out += str(j)
                if stop_all:
                    break
                out += "|"
            return out
        correct = run("break")
        wrong = pick_wrong(correct, [run("both"), run("none"), run("continue")])
        if not wrong:
            return False
        code = (f"for (int i = 1; i <= {a}; i++)\n{{\n    for (int j = 1; j <= {c}; j++)\n    {{\n        if ({cs})\n            break;\n"
                f"        Console.Write(j);\n    }}\n    {W('|')}\n}}")
        return b.add("cy-nested-break", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl="`break` ukončí iba najvnútornejší cyklus; vonkajší pokračuje ďalšou iteráciou.",
                     en_expl="`break` ends only the innermost loop; the outer one continues with its next iteration.",
                     verify={"type": "output"})
    fill(b, "cy-nested-break", 25, nested_break)

    def pattern():
        n = R.randint(2, 4); ch = R.choice(["*", "#", "o"])
        form = R.choice(["tri", "rev", "rect", "num"])
        if form == "tri":
            inner = "for (int j = 1; j <= i; j++)"; rows = [ch * i for i in range(1, n + 1)]; pr = W(ch)
        elif form == "rev":
            inner = f"for (int j = i; j <= {n}; j++)"; rows = [ch * (n - i + 1) for i in range(1, n + 1)]; pr = W(ch)
        elif form == "rect":
            m = R.randint(2, 4); inner = f"for (int j = 1; j <= {m}; j++)"; rows = [ch * m for _ in range(n)]; pr = W(ch)
        else:
            inner = "for (int j = 1; j <= i; j++)"; rows = ["".join(str(j) for j in range(1, i + 1)) for i in range(1, n + 1)]; pr = "Console.Write(j);"
        out = "".join(r + "|" for r in rows)
        alt = {"tri": "".join(ch * (n - i + 1) + "|" for i in range(1, n + 1)), "rev": "".join(ch * i + "|" for i in range(1, n + 1)),
               "rect": "".join(ch * i + "|" for i in range(1, n + 1)), "num": "".join(str(i) * i + "|" for i in range(1, n + 1))}[form]
        square = "".join((rows[-1] if form != "num" else rows[-1]) + "|" for _ in range(n))
        off = "".join((r[:-1] if len(r) > 1 else r + r) + "|" for r in rows)
        wrong = pick_wrong(out, [alt, square, off, "|" + out[:-1]])
        if not wrong:
            return False
        code = f"for (int i = 1; i <= {n}; i++)\n{{\n    {inner}\n        {pr}\n    {W('|')}\n}}"
        return b.add("cy-pattern", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Vnútorný cyklus vypíše jeden riadok, `|` ho ukončí: {', '.join(rows)}.",
                     en_expl=f"The inner loop prints one row and `|` ends it: {', '.join(rows)}.",
                     verify={"type": "output"})
    fill(b, "cy-pattern", 25, pattern)

    def counter_mod():
        n = R.randint(5, 9)
        change = R.choice([("i = i + 1;", lambda i: i + 1), ("i = i + 2;", lambda i: i + 2), ("i = i * 2;", lambda i: i * 2)])
        before = R.random() < 0.5
        start = 1 if change[0] == "i = i * 2;" else 0
        out, i, steps = "", start, 0
        while i < n and steps < 50:
            if before:
                i = change[1](i)
                if i >= 10:
                    return False
                out += str(i)
            else:
                out += str(i); i = change[1](i)
            i += 1; steps += 1
        if not out or len(out) > 8:
            return False
        plain = "".join(str(k) for k in range(start, n))
        wrong = pick_wrong(out, [plain, out + str(int(out[-1]) + 2) if out[-1].isdigit() and int(out[-1]) + 2 < 10 else plain[::2], plain[1::2], plain[::2]])
        if not wrong:
            return False
        body = f"    {change[0]}\n    Console.Write(i);" if before else f"    Console.Write(i);\n    {change[0]}"
        code = f"for (int i = {start}; i < {n}; i++)\n{{\n{body}\n}}"
        return b.add("cy-counter-modified", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`i` sa mení dvakrát za iteráciu – v tele (`{change[0]}`) aj v kroku `i++`, preto sa vypíše {', '.join(out)}.",
                     en_expl=f"`i` changes twice per iteration – in the body (`{change[0]}`) and in the step `i++` – so {', '.join(out)} is printed.",
                     verify={"type": "output"})
    fill(b, "cy-counter-modified", 25, counter_mod)

    def semicolon():
        ch = R.choice(["A", "B", "X", "*"])
        if R.random() < 0.6:
            n = R.randint(2, 6); block = R.random() < 0.5; v = R.choice(["i", "k"])
            body = f"{{\n    {W(ch)}\n}}" if block else f"    {W(ch)}"
            code = f"for (int {v} = 0; {v} < {n}; {v}++);\n{body}"
            sk, en = text_answers([code_ans(ch), code_ans(ch * n), NOTHING, COMPILE])
            return b.add("cy-semicolon", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                         sk_expl=f"Bodkočiarka za hlavičkou je prázdne telo cyklu – cyklus {n}-krát nespraví nič a riadok s `{ch}` sa vykoná iba raz.",
                         en_expl=f"The semicolon after the header is an empty loop body – the loop does nothing {n} times and the line with `{ch}` runs once.",
                         verify={"type": "output"})
        x0 = R.randint(0, 2); lim = R.randint(x0 + 2, 8)
        code = f"int x = {x0};\nwhile (x < {lim});\n{{\n    {W(ch)}\n    x = x + 1;\n}}"
        sk, en = text_answers([INF, code_ans(ch * (lim - x0)), code_ans(ch), NOTHING])
        return b.add("cy-semicolon", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"Bodkočiarka za `while (x < {lim})` je prázdne telo – blok pod ním do cyklu nepatrí, `x` sa nemení a cyklus sa nikdy neskončí.",
                     en_expl=f"The semicolon after `while (x < {lim})` is an empty body – the block below isn't part of the loop, `x` never changes, and the loop never ends.",
                     verify={"type": "timeout"})
    fill(b, "cy-semicolon", 25, semicolon)

    def no_braces():
        n = R.randint(2, 5); third = R.random() < 0.4
        l1, l2, l3 = R.sample(["A", "B", "C", "X", "Y", "*"], 3)
        code = f"for (int i = 0; i < {n}; i++)\n    {W(l1)}\n    {W(l2)}" + (f"\n{W(l3)}" if third else "")
        tail = l3 if third else ""
        correct = l1 * n + l2 + tail
        wrong = pick_wrong(correct, [(l1 + l2) * n + tail, l1 + l2 + tail, l1 * n + l2 * n + tail])
        return b.add("cy-no-braces", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Bez zložených zátvoriek patrí do cyklu iba prvý príkaz; odsadenie na tom nič nemení – `{l2}` sa vypíše iba raz po cykle.",
                     en_expl=f"Without braces only the first statement belongs to the loop; indentation doesn't matter – `{l2}` is printed once after the loop.",
                     verify={"type": "output"})
    fill(b, "cy-no-braces", 25, no_braces)

    def scope():
        n = R.randint(3, 6); var = R.choice(["sucet", "pocet", "s"])
        op = R.choice(["+ i", "+ 1", "+ i * 2"])
        code = f"int {var} = 0;\nfor (int i = 0; i < {n}; i++)\n{{\n    {var} = {var} {op};\n}}"
        bad = R.choice(["Console.Write(i);", "int k = i + 1;", "i = 0;", f"{var} = {var} + i;"])
        valid = R.sample([f"Console.Write({var});", f"{var} = {var} * 2;", f"int j = {var};", f"int k = {var} + 1;", f"Console.Write({var} + 1);"], 3)
        return b.add("cy-scope", 3, code=code,
                     sk_body="{code}\nKtorý riadok, pridaný **za** cyklus, spôsobí chybu pri preklade?",
                     en_body="{code}\nWhich line, added **after** the loop, causes a compile error?",
                     answers=[code_ans(bad)] + [code_ans(v) for v in valid],
                     sk_expl="Premenná `i` deklarovaná v hlavičke `for` existuje iba vnútri cyklu – za ním ju už použiť nemožno.",
                     en_expl="The variable `i` declared in the `for` header exists only inside the loop – it can't be used after it.",
                     verify={"type": "which-line", "expect": "compile-error"})
    fill(b, "cy-scope", 25, scope)

    def digits():
        n = R.randint(100, 9999)
        form = R.choice(["sum", "count", "rev"])
        ds = [int(c) for c in str(n)]
        if form == "sum":
            res = sum(ds); code = f"int n = {n};\nint s = 0;\nwhile (n > 0)\n{{\n    s = s + n % 10;\n    n = n / 10;\n}}"; name = "s"
            wrong = pick_wrong(res, [n, res - ds[0], res - ds[-1], int(str(n)[::-1])])
            steps = " + ".join(map(str, ds[::-1])) + f" = {res}"
        elif form == "count":
            res = len(ds); code = f"int n = {n};\nint pocet = 0;\nwhile (n > 0)\n{{\n    pocet = pocet + 1;\n    n = n / 10;\n}}"; name = "pocet"
            wrong = pick_wrong(res, [res - 1, res + 1, sum(ds), n % 10])
            steps = f"{n} má {res} cifry" if res < 5 else f"{n} má {res} cifier"
        else:
            if n % 10 == 0:
                return False
            res = int(str(n)[::-1]); code = f"int n = {n};\nint r = 0;\nwhile (n > 0)\n{{\n    r = r * 10 + n % 10;\n    n = n / 10;\n}}"; name = "r"
            wrong = pick_wrong(res, [n, sum(ds), int(str(res)[:-1]) if len(str(res)) > 1 else 0, int(str(n)[1:] + str(n)[0])])
            steps = f"cifry odzadu sú {', '.join(str(n)[::-1])}"
        if not wrong:
            return False
        steps_en = steps.replace("cifry odzadu sú", "the digits from the end are").replace("má", "has").replace("cifry", "digits").replace("cifier", "digits")
        return b.add("cy-digits", 3, code=code, sk_body=val_q(name)[0], en_body=val_q(name)[1],
                     answers=[code_ans(res)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`n % 10` dá poslednú cifru, `n / 10` ju odstráni: {steps}.",
                     en_expl=f"`n % 10` gives the last digit, `n / 10` removes it: {steps_en}.",
                     verify={"type": "value", "expr": name})
    fill(b, "cy-digits", 25, digits)

    def off_by_one():
        n = R.randint(4, 9)
        forms = [("int i = 1; i < n; i++", range(1, n)), ("int i = 0; i <= n - 1; i++", range(0, n)), ("int i = 2; i < n + 1; i++", range(2, n + 1)),
                 ("int i = n; i > 1; i--", range(n, 1, -1)), ("int i = 1; i <= n + 1; i++", range(1, n + 2)), ("int i = n - 1; i >= 0; i--", range(n - 1, -1, -1))]
        header, rng = R.choice(forms)
        vals = list(rng); cnt = len(vals)
        code = f"int n = {n};\nfor ({header})\n    {W('A')}"
        wrong = pick_wrong(cnt, [n, n - 1, n + 1, n - 2])
        return b.add("cy-off-by-one-ends", 3, code=code,
                     sk_body="{code}\nKoľkokrát sa vykoná telo cyklu?", en_body="{code}\nHow many times does the loop body run?",
                     answers=[code_ans(cnt)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Pre `n = {n}` nadobúda `i` hodnoty {lst(vals)}, to je {cnt}.",
                     en_expl=f"For `n = {n}`, `i` takes the values {lst(vals)}, that's {cnt}.",
                     verify={"type": "output", "expected": "A" * cnt})
    fill(b, "cy-off-by-one-ends", 25, off_by_one)

    def while_continue():
        n = R.randint(4, 7); k = R.randint(1, n - 2)
        if R.random() < 0.55:
            code = f"int i = 0;\nwhile (i < {n})\n{{\n    if (i == {k})\n        continue;\n    Console.Write(i);\n    i++;\n}}"
            printed = "".join(str(i) for i in range(k))
            skip_print = "".join(str(i) for i in range(n) if i != k)
            sk, en = text_answers([INF, code_ans(skip_print), code_ans(printed) if printed else NOTHING, NOTHING if printed else code_ans(str(k))])
            return b.add("cy-while-continue", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                         sk_expl=f"Pri `i == {k}` sa `continue` vykoná skôr ako `i++`, takže `i` zostane {k} navždy – program vypíše {printed or 'nič'} a potom sa zasekne.",
                         en_expl=f"At `i == {k}`, `continue` runs before `i++`, so `i` stays {k} forever – the program prints {printed or 'nothing'} and then hangs.",
                         verify={"type": "timeout"})
        code = f"int i = 0;\nwhile (i < {n})\n{{\n    i++;\n    if (i == {k})\n        continue;\n    Console.Write(i);\n}}"
        out = "".join(str(i) for i in range(1, n + 1) if i != k)
        sk, en = text_answers([code_ans(out), INF, code_ans("".join(str(i) for i in range(n) if i != k)), code_ans("".join(str(i) for i in range(1, n + 1)))])
        return b.add("cy-while-continue", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"`i++` je pred `continue`, takže sa `i` zvýši v každej iterácii; pri `i == {k}` sa preskočí iba výpis.",
                     en_expl=f"`i++` comes before `continue`, so `i` grows in every iteration; at `i == {k}` only the print is skipped.",
                     verify={"type": "output"})
    fill(b, "cy-while-continue", 25, while_continue)

    def trace():
        form = R.choice(["fib", "swap", "dep", "two"])
        n = R.randint(3, 5)
        if form == "fib":
            a0, b0 = R.choice([(1, 1), (0, 1), (1, 2), (2, 3)])
            body = "    int c = a + b;\n    a = b;\n    b = c;"
            def step(a, b): return b, a + b
        elif form == "swap":
            a0, b0 = R.randint(1, 9), R.randint(1, 9)
            body = "    a = a + b;\n    b = a - b;"
            def step(a, b): a2 = a + b; return a2, a2 - b
        elif form == "dep":
            a0, b0 = R.randint(0, 3), R.randint(1, 3)
            body = "    a = a + b;\n    b = b + 1;"
            def step(a, b): return a + b, b + 1
        else:
            a0, b0 = R.randint(1, 5), R.randint(10, 20)
            body = "    a = a * 2;\n    b = b - a;"
            def step(a, b): a2 = a * 2; return a2, b - a2
        a, bb = a0, b0
        hist = [(a, bb)]
        for _ in range(n):
            a, bb = step(a, bb); hist.append((a, bb))
        fmt = lambda p: f"a = {p[0]}, b = {p[1]}"
        correct = fmt(hist[-1])
        cands = [fmt(hist[-2]), fmt((hist[-1][1], hist[-1][0])), fmt(step(*hist[-1]))]
        wrong = pick_wrong(correct, cands)
        if not wrong:
            return False
        code = f"int a = {a0};\nint b = {b0};\nfor (int i = 0; i < {n}; i++)\n{{\n{body}\n}}"
        steps = "; ".join(f"({p[0]}, {p[1]})" for p in hist[1:])
        return b.add("cy-trace", 3, code=code,
                     sk_body="{code}\nAké hodnoty budú mať `a` a `b` na konci?", en_body="{code}\nWhat values will `a` and `b` have at the end?",
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Po iteráciách (a, b): {steps}.", en_expl=f"After each iteration (a, b): {steps}.",
                     verify={"type": "value", "expr": '$"a = {a}, b = {b}"'})
    fill(b, "cy-trace", 25, trace)
    return b


if __name__ == "__main__":
    main().write()
