"""Generator for topic functions (36 templates × 25). Local functions in a top-level program."""
import random
from common import Batch, fill, code_ans, pick_wrong, fmt_double

R = random.Random(20261025)
DATE = "2026-10-22"
OUT_Q = ("{code}\nČo vypíše tento kód?", "{code}\nWhat does this code print?")
NOTHING = ("Nič", "Nothing")
W = lambda s: f'Console.Write("{s}");'


def val_q(name):
    return f"{{code}}\nAkú hodnotu bude mať premenná `{name}`?", f"{{code}}\nWhat value will the variable `{name}` have?"


def text_answers(answers):
    sk = [a[0] if isinstance(a, tuple) else a for a in answers]
    en = [a[1] if isinstance(a, tuple) else a for a in answers]
    return sk, (en if en != sk else None)


def bstr(v):
    return "true" if v else "false"


BOOLS = ["`true`", "`false`", "`1`", "`0`"]


def bool_answers(v):
    c = f"`{bstr(v)}`"
    return [c] + [x for x in BOOLS if x != c]


def fn(header, body_lines):
    body = "\n".join("    " + l for l in body_lines)
    return f"{header}\n{{\n{body}\n}}"


def prog(main_lines, *functions):
    return "\n".join(main_lines) + "\n\n" + "\n\n".join(functions)


# one-parameter int functions: (name, expr in x, python)
UNARY = [("Dvojnasobok", "x * 2", lambda x: x * 2), ("Trojnasobok", "x * 3", lambda x: x * 3), ("Stvorec", "x * x", lambda x: x * x),
         ("PridajDesat", "x + 10", lambda x: x + 10), ("Nasledovnik", "x + 1", lambda x: x + 1), ("Predchodca", "x - 1", lambda x: x - 1),
         ("Polovica", "x / 2", lambda x: x // 2), ("Zvysok", "x % 3", lambda x: x % 3)]


def main():
    b = Batch(f"{DATE}_functions", "functions", DATE)

    # =================================================================== EASY
    def return_value():
        name, expr, f = R.choice(UNARY); n = R.randint(2, 12)
        v = f(n)
        others = [g(n) for nm, e, g in UNARY if nm != name]
        R.shuffle(others)
        wrong = pick_wrong(v, [n] + others)
        if not wrong:
            return False
        wrong = [n if n != v else wrong[0], wrong[1], name]
        if len(set(map(str, [v] + wrong))) < 4:
            return False
        code = prog([f"int v = {name}({n});"], fn(f"int {name}(int x)", [f"return {expr};"]))
        return b.add("fn-return-value", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Funkcia dostane `{n}` a vráti `{expr.replace('x', str(n))}` = `{v}`; táto hodnota sa uloží do `v`.",
                     en_expl=f"The function receives `{n}` and returns `{expr.replace('x', str(n))}` = `{v}`; that value is stored in `v`.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "fn-return-value", 25, return_value)

    HEADERS = [("int", "Sucet", [("int", "a"), ("int", "b")]), ("double", "Priemer", [("int", "a"), ("int", "b")]), ("bool", "JeParne", [("int", "x")]),
               ("string", "Pozdrav", [("string", "meno")]), ("void", "Vypis", [("int", "n")]), ("char", "PrvePismeno", [("string", "slovo")]),
               ("int", "Max", [("int", "a"), ("int", "b")]), ("bool", "JeVacsie", [("int", "x"), ("int", "y")]), ("string", "Opakuj", [("string", "text"), ("int", "n")]),
               ("void", "NakresliCiaru", [("int", "dlzka"), ("char", "znak")])]
    PARTS = [("návratový typ", "return type"), ("názov funkcie", "function name"), ("prvý parameter", "first parameter"), ("druhý parameter", "second parameter")]
    def header_parts():
        rt, name, params = R.choice(HEADERS)
        k = R.randrange(4 if len(params) == 2 else 3)
        header = f"{rt} {name}(" + ", ".join(f"{t} {p}" for t, p in params) + ")"
        pieces = [rt, name] + [f"{t} {p}" for t, p in params]
        correct = pieces[k]
        wrong = [p for i, p in enumerate(pieces) if i != k]
        extra = [params[0][1], f"{rt} {name}", "void" if rt != "void" else "int", "return"]
        for e in extra:
            if len(wrong) >= 3:
                break
            if e not in wrong and e != correct:
                wrong.append(e)
        wrong = wrong[:3]
        sk, en = PARTS[k]
        return b.add("fn-header-parts", 1, code=None,
                     sk_body=f"V hlavičke funkcie `{header}` čo je **{sk}**?", en_body=f"In the function header `{header}`, what is the **{en}**?",
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl="Hlavička: návratový typ, názov, v zátvorke parametre s typmi.",
                     en_expl="A header has the return type, the name, and the parameters with their types in brackets.",
                     verify={"type": "none"})
    fill(b, "fn-header-parts", 25, header_parts)

    TERMS = {
        "`return`": [("vráti hodnotu z funkcie a ukončí ju", "returns a value from the function and ends it"), ("ukončí funkciu a odovzdá výsledok volajúcemu", "ends the function and hands the result to the caller")],
        "`void`": [("označuje, že funkcia nevracia žiadnu hodnotu", "means the function returns no value"), ("návratový typ funkcie, ktorá iba niečo vykoná a nič nevráti", "the return type of a function that only does something and returns nothing")],
        "parameter": [("premenná v hlavičke funkcie, do ktorej sa odovzdá hodnota", "a variable in the function header that receives a value"), ("meno a typ hodnoty, ktorú funkcia očakáva", "the name and type of a value the function expects")],
        "argument": [("hodnota, ktorú pošleme funkcii pri volaní", "a value we pass to the function when calling it"), ("konkrétna hodnota v zátvorke pri volaní funkcie", "the actual value in the brackets when calling a function")],
    }
    FAKE = [("vypíše hodnotu na obrazovku", "prints the value on the screen"), ("vytvorí novú premennú v hlavnom programe", "creates a new variable in the main program"),
            ("zopakuje funkciu ešte raz", "runs the function once more")]
    TQ = [("Čo je {t}?", "What is {t}?"), ("Na čo slúži {t}?", "What is {t} for?"), ("Čo vo funkciách znamená {t}?", "What does {t} mean in functions?")]
    def term_purpose():
        t = R.choice(list(TERMS)); q = R.choice(TQ)
        correct = R.choice(TERMS[t])
        others = [R.choice(TERMS[o]) for o in TERMS if o != t]
        R.shuffle(others)
        wrong = others[:2] + [R.choice(FAKE)] if R.random() < 0.6 or t == "`return`" else others[:3]
        sk, en = text_answers([correct] + wrong)
        return b.add("fn-term-purpose", 1, code=None, sk_body=q[0].format(t=t), en_body=q[1].format(t=t), answers=sk, en_answers=en,
                     sk_expl=f"{t}: {TERMS[t][0][0]}." + (" Vypisovanie robí `Console.Write`, nie `return`." if t == "`return`" else ""),
                     en_expl=f"{t}: {TERMS[t][0][1]}." + (" Printing is done by `Console.Write`, not `return`." if t == "`return`" else ""),
                     verify={"type": "none"})
    fill(b, "fn-term-purpose", 25, term_purpose)

    PURP = [
        ("Ktoré kľúčové slovo označuje, že funkcia nevracia žiadnu hodnotu?", "Which keyword means a function returns no value?", "`void`", ["`return`", "`int`", "`Console.Write`"]),
        ("Ktoré kľúčové slovo vráti hodnotu z funkcie?", "Which keyword returns a value from a function?", "`return`", ["`void`", "`Console.Write`", "`break`"]),
        ("Ktoré kľúčové slovo okamžite ukončí funkciu?", "Which keyword ends a function immediately?", "`return`", ["`void`", "`continue`", "`Console.Write`"]),
        ("Ako sa volá premenná v hlavičke funkcie, do ktorej sa odovzdá hodnota?", "What is the variable in the function header that receives a value called?", ("parameter", "parameter"), [("argument", "argument"), ("návratová hodnota", "return value"), ("atribút", "field")]),
        ("Ako sa volá hodnota, ktorú pošleme funkcii pri volaní?", "What is the value we pass to a function when calling it called?", ("argument", "argument"), [("parameter", "parameter"), ("návratový typ", "return type"), ("index", "index")]),
        ("Ako sa volá typ uvedený pred názvom funkcie?", "What is the type written before the function name called?", ("návratový typ", "return type"), [("typ parametra", "parameter type"), ("argument", "argument"), ("typ triedy", "class type")]),
        ("Čo napíšeme ako návratový typ funkcie, ktorá iba vypíše text?", "What do we write as the return type of a function that only prints text?", "`void`", ["`string`", "`return`", "`null`"]),
        ("Ako sa volá časť funkcie medzi `{` a `}`?", "What is the part of a function between `{` and `}` called?", ("telo funkcie", "function body"), [("hlavička funkcie", "function header"), ("parameter", "parameter"), ("argument", "argument")]),
        ("Ako sa volá prvý riadok funkcie s typom, názvom a parametrami?", "What is the first line of a function, with the type, name and parameters, called?", ("hlavička funkcie", "function header"), [("telo funkcie", "function body"), ("volanie funkcie", "function call"), ("návratová hodnota", "return value")]),
        ("Ako sa volá zápis `Sucet(2, 3)` v programe?", "What is `Sucet(2, 3)` in a program called?", ("volanie funkcie", "function call"), [("deklarácia funkcie", "function declaration"), ("hlavička funkcie", "function header"), ("parameter", "parameter")]),
        ("Ktorý návratový typ má funkcia, ktorá vráti `true` alebo `false`?", "Which return type does a function returning `true` or `false` have?", "`bool`", ["`int`", "`void`", "`string`", "`char`"]),
        ("Ktorý návratový typ má funkcia, ktorá vráti celé číslo?", "Which return type does a function returning a whole number have?", "`int`", ["`void`", "`double`", "`string`", "`bool`"]),
        ("Ako v C# zavoláme funkciu `Pozdrav` bez argumentov?", "How do we call the function `Pozdrav` without arguments in C#?", "`Pozdrav();`", ["`Pozdrav;`", "`call Pozdrav();`", "`void Pozdrav();`"]),
    ]
    def purpose_term():
        sk_q, en_q, correct, wrong = R.choice(PURP)
        wrong = R.sample(wrong, 3)
        ans = [correct] + wrong
        sk, en = text_answers(ans)
        c_sk = correct[0] if isinstance(correct, tuple) else correct
        c_en = correct[1] if isinstance(correct, tuple) else correct
        if R.random() < 0.5:  # variety: reordering of wrong answers does not count, so vary phrasing
            sk_q2, en_q2 = sk_q, en_q
        else:
            sk_q2, en_q2 = sk_q + " Vyber jednu možnosť.", en_q + " Pick one option."
        return b.add("fn-purpose-term", 1, code=None, sk_body=sk_q2, en_body=en_q2, answers=sk, en_answers=en,
                     sk_expl=f"Správne je {c_sk}.", en_expl=f"The correct answer is {c_en}.", verify={"type": "none"})
    fill(b, "fn-purpose-term", 25, purpose_term, tries=5000)

    def void_print():
        name = R.choice(["Pozdrav", "Vypis", "Tlac", "Ukaz"])
        if R.random() < 0.5:
            letter = R.choice("ABHKX"); n = R.randint(1, 3)
            code = prog([f"{name}();"] * n, fn(f"void {name}()", [W(letter)]))
            out = letter * n
            cands = [c for c in [letter * (n - 1) if n > 1 else None, letter * (n + 1), letter * (n + 2)] if c]
            wrong = pick_wrong(out, cands, n=2)
            ans = [code_ans(out)] + [code_ans(w) for w in wrong] + [NOTHING]
        else:
            args = [R.randint(1, 9) for _ in range(R.randint(2, 3))]
            code = prog([f"{name}({a});" for a in args], fn(f"void {name}(int x)", ["Console.Write(x);"]))
            out = "".join(map(str, args))
            wr = pick_wrong(out, [out[::-1], str(args[0]), str(args[-1]), out + str(args[-1]), out[:-1]], n=2)
            if not wr:
                return False
            ans = [code_ans(out)] + [code_ans(w) for w in wr] + [NOTHING]
        n_calls = len([l for l in code.split("\n\n")[0].split("\n")])
        sk, en = text_answers(ans[:4])
        return b.add("fn-void-print", 1, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"Funkcia sa vykoná pri každom volaní – tu {n_calls}-krát.",
                     en_expl=f"The function runs on every call – here {n_calls} times.",
                     verify={"type": "output"})
    fill(b, "fn-void-print", 25, void_print)

    BIN = [("Sucet", "a + b", lambda a, c: a + c), ("Rozdiel", "a - b", lambda a, c: a - c), ("Sucin", "a * b", lambda a, c: a * c)]
    def two_params():
        name, expr, f = R.choice(BIN); x, y = R.randint(1, 12), R.randint(1, 12)
        if x == y:
            return False
        v = f(x, y)
        wrong = pick_wrong(v, [g(x, y) for n, e, g in BIN if n != name] + [y - x, int(f"{x}{y}")])
        code = prog([f"int v = {name}({x}, {y});"], fn(f"int {name}(int a, int b)", [f"return {expr};"]))
        return b.add("fn-two-params", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`a` = {x}, `b` = {y}, funkcia vráti `{expr}` = `{v}`.",
                     en_expl=f"`a` = {x}, `b` = {y}, the function returns `{expr}` = `{v}`.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "fn-two-params", 25, two_params)

    DESC = [("zistí, či je číslo párne (áno/nie)", "checks whether a number is even (yes/no)", "bool", "vráti áno/nie", "it returns yes/no"),
            ("vráti súčet dvoch celých čísel", "returns the sum of two whole numbers", "int", "vráti celé číslo", "it returns a whole number"),
            ("vráti priemer známok (napr. 2.5)", "returns the average of grades (e.g. 2.5)", "double", "vráti číslo s desatinnou časťou", "it returns a number with a decimal part"),
            ("vráti pozdrav „Ahoj, Eva!“", "returns the greeting “Ahoj, Eva!”", "string", "vráti text", "it returns text"),
            ("vráti prvé písmeno mena", "returns the first letter of a name", "char", "vráti jeden znak", "it returns a single character"),
            ("iba vypíše tabuľku na obrazovku", "only prints a table on the screen", "void", "nič nevracia, iba vypisuje", "it returns nothing, it only prints"),
            ("zistí, či je žiak plnoletý", "checks whether a student is an adult", "bool", "vráti áno/nie", "it returns yes/no"),
            ("vráti počet samohlások v slove", "returns the number of vowels in a word", "int", "vráti celé číslo", "it returns a whole number"),
            ("vráti meno spojené s priezviskom", "returns the first name joined with the surname", "string", "vráti text", "it returns text"),
            ("vráti obvod kruhu", "returns the circumference of a circle", "double", "vráti číslo s desatinnou časťou", "it returns a number with a decimal part"),
            ("vykreslí čiaru z hviezdičiek", "draws a line of stars", "void", "nič nevracia, iba vypisuje", "it returns nothing, it only prints"),
            ("vráti známku 1 až 5 podľa bodov", "returns a grade 1 to 5 based on points", "int", "vráti celé číslo", "it returns a whole number"),
            ("vráti písmeno známky (A až F)", "returns a letter grade (A to F)", "char", "vráti jeden znak", "it returns a single character")]
    TYPES = ["int", "double", "bool", "char", "string", "void"]
    def which_return_type():
        dsk, den, t, rsk, ren = R.choice(DESC)
        wrong = R.sample([x for x in TYPES if x != t], 3)
        return b.add("fn-which-return-type", 1, code=None,
                     sk_body=f"Funkcia {dsk}. Aký návratový typ má mať?", en_body=f"A function {den}. What should its return type be?",
                     answers=[code_ans(t)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Funkcia {rsk}, preto `{t}`.", en_expl=f"The function – {ren} – so `{t}`.",
                     verify={"type": "none"})
    fill(b, "fn-which-return-type", 25, which_return_type)

    def variable_arg():
        name, expr, f = R.choice(UNARY); a = R.randint(2, 12); var = R.choice(["a", "cislo", "n", "hodnota"])
        if var == "x":
            return False
        v = f(a)
        other = [g(a) for nm, e, g in UNARY if nm != name]
        R.shuffle(other)
        wrong = pick_wrong(v, [a] + other)
        wrong = [w for w in wrong][:2] + ["x"]
        if a == v or len(set(map(str, [v] + wrong))) < 4:
            return False
        code = prog([f"int {var} = {a};", f"int v = {name}({var});"], fn(f"int {name}(int x)", [f"return {expr};"]))
        return b.add("fn-variable-arg", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Hodnota premennej `{var}` ({a}) sa skopíruje do parametra `x`; funkcia vráti `{v}`.",
                     en_expl=f"The value of `{var}` ({a}) is copied into the parameter `x`; the function returns `{v}`.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "fn-variable-arg", 25, variable_arg)

    def output_order():
        l1, l2, l3, l4 = R.sample("ABCDEXYZ", 4)
        name = R.choice(["VypisB", "Pozdrav", "Krok", "Tlac"])
        two = R.random() < 0.4
        body = [W(l2)] + ([W(l4)] if two else [])
        inside = l2 + (l4 if two else "")
        pos = R.choice([0, 1, 1, 2])
        mains = [W(l1), W(l3)]
        mains.insert(pos, f"{name}();")
        out_parts = [l1, l3]; out_parts.insert(pos, inside)
        out = "".join(out_parts)
        written = l1 + l3 + inside
        no_call = l1 + l3
        func_first = inside + l1 + l3
        wrong = pick_wrong(out, [written, no_call, func_first, l3 + l1 + inside])
        code = prog(mains, fn(f"void {name}()", body))
        return b.add("fn-output-order", 1, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl="Kód sa vykonáva zhora; pri volaní sa vykoná telo funkcie a potom sa pokračuje ďalším riadkom. Na poradí, kde je funkcia v súbore napísaná, nezáleží.",
                     en_expl="Code runs from the top; at the call the function body runs, then execution continues with the next line. Where the function is written in the file doesn't matter.",
                     verify={"type": "output"})
    fill(b, "fn-output-order", 25, output_order)

    CALLS = [
        ("int Sucet(int a, int b)", ["return a + b;"], "int v = Sucet(2, 3);", ["int v = Sucet(2);", 'int v = Sucet("2", 3);', "int v = Sucet(int 2, int 3);", "string v = Sucet(2, 3);", "int v = Sucet(2, 3, 4);"]),
        ("bool JeParne(int x)", ["return x % 2 == 0;"], "bool p = JeParne(4);", ["int p = JeParne(4);", "bool p = JeParne();", 'bool p = JeParne("4");', "bool p = JeParne(int 4);"]),
        ("string Pozdrav(string meno)", ['return "Ahoj " + meno;'], 'string s = Pozdrav("Eva");', ["string s = Pozdrav(Eva);", "string s = Pozdrav();", 'int s = Pozdrav("Eva");', 'string s = Pozdrav(string "Eva");']),
        ("void Vypis(int n)", ["Console.Write(n);"], "Vypis(5);", ["int v = Vypis(5);", "Vypis();", 'Vypis("5");', "Vypis(int 5);"]),
        ("double Priemer(int a, int b)", ["return (a + b) / 2.0;"], "double p = Priemer(3, 4);", ["int p = Priemer(3, 4);", "double p = Priemer(3);", "double p = Priemer(3.5, 4);", "double p = Priemer[3, 4];"]),
        ("int Max(int a, int b)", ["if (a > b)", "    return a;", "return b;"], "int m = Max(7, 2);", ["int m = Max(7);", "int m = Max 7, 2;", 'int m = Max("7", "2");', "bool m = Max(7, 2);"]),
    ]
    def valid_call():
        header, body, good, bads = R.choice(CALLS)
        wrong = R.sample(bads, 3)
        decl = fn(header, body)
        return b.add("fn-valid-call", 1, code=decl, sk_body="{code}\nKtoré volanie je správne?", en_body="{code}\nWhich call is correct?",
                     answers=[code_ans(good)] + [code_ans(w) for w in wrong],
                     sk_expl="Volanie musí mať toľko argumentov a takých typov, ako sú parametre v hlavičke, a výsledok sa ukladá do premennej správneho typu.",
                     en_expl="A call must have as many arguments, of the same types, as the header has parameters, and the result goes into a variable of the right type.",
                     verify={"type": "which-line", "expect": "compile-error", "invert": True})
    fill(b, "fn-valid-call", 25, valid_call)

    def call_count():
        name = R.choice(["Pozdrav", "Krok", "Vypis", "Pipni"]); n = R.randint(2, 6); after = R.choice([0, 0, 1, 2])
        before = R.choice([0, 0, 1])
        lines = [f"{name}();"] * before + [f"for (int i = 0; i < {n}; i++)", f"    {name}();"] + [f"{name}();"] * after
        cnt = before + n + after
        code = prog(lines, fn(f"void {name}()", [W("*")]))
        wrong = pick_wrong(cnt, [n, 1, cnt + 1, cnt - 1])
        parts = (f"{before} + " if before else "") + f"{n}" + (f" + {after}" if after else "")
        return b.add("fn-call-count", 1, code=code,
                     sk_body=f"{{code}}\nKoľkokrát sa vykoná telo funkcie `{name}`?", en_body=f"{{code}}\nHow many times does the body of `{name}` run?",
                     answers=[code_ans(cnt)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Funkcia sa vykoná pri každom volaní: {parts} = {cnt}.", en_expl=f"The function runs on every call: {parts} = {cnt}.",
                     verify={"type": "output", "expected": "*" * cnt})
    fill(b, "fn-call-count", 25, call_count)

    BOOLF = [("JeParne", "x % 2 == 0", lambda x: x % 2 == 0), ("JeKladne", "x > 0", lambda x: x > 0), ("JeVacsieAkoDesat", "x > 10", lambda x: x > 10),
             ("JeDelitelneTromi", "x % 3 == 0", lambda x: x % 3 == 0), ("JeMale", "x < 5", lambda x: x < 5)]
    def bool_in_if():
        name, expr, f = R.choice(BOOLF); x = R.randint(-5, 20)
        v = f(x); l1, l2 = R.sample("ABNY", 2)
        code = prog([f"bool p = {name}({x});", "if (p)", f"    {W(l1)}", "else", f"    {W(l2)}"], fn(f"bool {name}(int x)", [f"return {expr};"]))
        correct = l1 if v else l2
        sk, en = text_answers([code_ans(correct), code_ans(l2 if v else l1), code_ans(l1 + l2), NOTHING])
        return b.add("fn-bool-in-if", 1, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"`{name}({x})` vráti `{bstr(v)}`, preto sa vypíše `{correct}`.",
                     en_expl=f"`{name}({x})` returns `{bstr(v)}`, so `{correct}` is printed.",
                     verify={"type": "output"})
    fill(b, "fn-bool-in-if", 25, bool_in_if)

    # =================================================================== MEDIUM
    def chain_calls():
        (n1, e1, f1), (n2, e2, f2) = R.sample(UNARY[:6], 2)
        x = R.randint(1, 9)
        v = f2(f1(x))
        wrong = pick_wrong(v, [f1(f2(x)), f1(x), f2(x), x])
        if not wrong:
            return False
        code = prog([f"int v = {n2}({n1}({x}));"], fn(f"int {n1}(int x)", [f"return {e1};"]), fn(f"int {n2}(int x)", [f"return {e2};"]))
        return b.add("fn-chain-calls", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Najprv sa vypočíta vnútorné volanie `{n1}({x})` = {f1(x)}, potom `{n2}({f1(x)})` = {v}.",
                     en_expl=f"First the inner call `{n1}({x})` = {f1(x)}, then `{n2}({f1(x)})` = {v}.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "fn-chain-calls", 25, chain_calls)

    BF = {"Max": (["if (a > b)", "    return a;", "return b;"], max), "Min": (["if (a < b)", "    return a;", "return b;"], min),
          "Sucet": (["return a + b;"], lambda a, c: a + c)}
    def nested_arg():
        name = R.choice(list(BF)); body, f = BF[name]
        x, y, z = R.randint(1, 15), R.randint(1, 15), R.randint(1, 15)
        if len({x, y, z}) < 3:
            return False
        inner_first = R.random() < 0.5
        if inner_first:
            call = f"{name}({name}({x}, {y}), {z})"; iv = f(x, y); v = f(iv, z); inner = f"{name}({x}, {y})"
        else:
            call = f"{name}({x}, {name}({y}, {z}))"; iv = f(y, z); v = f(x, iv); inner = f"{name}({y}, {z})"
        other = {"Max": min, "Min": max, "Sucet": lambda a, c: a * c}[name]
        wrong = pick_wrong(v, [iv, other(other(x, y), z), f(x, y) if not inner_first else f(y, z), x, z])
        if not wrong:
            return False
        code = prog([f"int v = {call};"], fn(f"int {name}(int a, int b)", body))
        return b.add("fn-nested-arg", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Vnútorné volanie `{inner}` = {iv}, potom vonkajšie = {v}.",
                     en_expl=f"The inner call `{inner}` = {iv}, then the outer one = {v}.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "fn-nested-arg", 25, nested_arg)

    MR = [("Max", "int Max(int a, int b)", ["if (a > b)", "    return a;", "else", "    return b;"], 2, lambda a, c: a if a > c else c),
          ("Min", "int Min(int a, int b)", ["if (a < b)", "    return a;", "else", "    return b;"], 2, lambda a, c: a if a < c else c),
          ("Abs", "int Abs(int x)", ["if (x < 0)", "    return -x;", "return x;"], 1, lambda a: -a if a < 0 else a),
          ("Znamienko", "int Znamienko(int x)", ["if (x > 0)", "    return 1;", "else if (x < 0)", "    return -1;", "else", "    return 0;"], 1, lambda a: (a > 0) - (a < 0)),
          ("Znamka", "int Znamka(int body)", ["if (body >= 90)", "    return 1;", "if (body >= 75)", "    return 2;", "if (body >= 50)", "    return 3;", "return 5;"], 1,
           lambda p: 1 if p >= 90 else 2 if p >= 75 else 3 if p >= 50 else 5)]
    def multiple_returns():
        name, header, body, ar, f = R.choice(MR)
        if ar == 2:
            a = R.randint(-5, 15); c = a if R.random() < 0.2 else R.randint(-5, 15); args = (a, c)
        elif name == "Znamka":
            args = (R.choice([90, 89, 75, 74, 50, 49, R.randint(0, 100)]),)
        else:
            args = (R.choice([0, R.randint(-9, -1), R.randint(1, 9)]),)
        v = f(*args)
        cands = list(args) + [-v, 0, v + 1, 1, -1, 2, 3, 5]
        wrong = pick_wrong(v, cands)
        code = prog([f"int v = {name}({', '.join(map(str, args))});"], fn(header, body))
        return b.add("fn-multiple-returns", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Pre argument(y) {', '.join(map(str, args))} sa vykoná vetva, ktorá vráti `{v}` – po `return` sa funkcia hneď skončí.",
                     en_expl=f"For the argument(s) {', '.join(map(str, args))}, the branch returning `{v}` runs – the function ends right at `return`.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "fn-multiple-returns", 25, multiple_returns)

    def loop_inside():
        form = R.choice(["sum", "div", "pow", "even"])
        if form == "sum":
            n = R.randint(3, 8); v = n * (n + 1) // 2
            f = fn("int SucetDo(int n)", ["int s = 0;", "for (int i = 1; i <= n; i++)", "    s = s + i;", "return s;"]); call = f"SucetDo({n})"
            wrong = pick_wrong(v, [v - n, v + n + 1, n])
            steps = " + ".join(map(str, range(1, n + 1))) + f" = {v}"
        elif form == "div":
            n = R.choice([6, 8, 10, 12, 15, 16, 18, 20, 9, 7]); divs = [d for d in range(1, n + 1) if n % d == 0]; v = len(divs)
            f = fn("int PocetDelitelov(int n)", ["int pocet = 0;", "for (int i = 1; i <= n; i++)", "{", "    if (n % i == 0)", "        pocet = pocet + 1;", "}", "return pocet;"]); call = f"PocetDelitelov({n})"
            wrong = pick_wrong(v, [v - 2, v - 1, sum(divs), n])
            steps = f"delitele {n}: {', '.join(map(str, divs))}"
        elif form == "pow":
            z, n = R.randint(2, 4), R.randint(2, 4); v = z ** n
            f = fn("int Mocnina(int z, int n)", ["int vysledok = 1;", "for (int i = 0; i < n; i++)", "    vysledok = vysledok * z;", "return vysledok;"]); call = f"Mocnina({z}, {n})"
            wrong = pick_wrong(v, [z * n, z ** (n - 1), z ** (n + 1), n ** z])
            steps = " · ".join([str(z)] * n) + f" = {v}"
        else:
            n = R.randint(5, 14); ev = [i for i in range(1, n + 1) if i % 2 == 0]; v = len(ev)
            f = fn("int PocetParnych(int n)", ["int pocet = 0;", "for (int i = 1; i <= n; i++)", "{", "    if (i % 2 == 0)", "        pocet = pocet + 1;", "}", "return pocet;"]); call = f"PocetParnych({n})"
            wrong = pick_wrong(v, [v + 1, v - 1, sum(ev), n])
            steps = f"párne čísla: {', '.join(map(str, ev))}"
        code = prog([f"int v = {call};"], f)
        steps_en = steps.replace("delitele", "divisors of").replace("párne čísla", "even numbers")
        return b.add("fn-loop-inside", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Cyklus vo funkcii: {steps}; funkcia vráti `{v}`.", en_expl=f"The loop in the function: {steps_en}; it returns `{v}`.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "fn-loop-inside", 25, loop_inside)

    def return_ends():
        l1, l2, l3 = R.sample("ABCXYZ", 3); k = R.randint(2, 8); x = R.randint(0, 10)
        op = R.choice([">", "<", "=="])
        if op == "==":
            x = k if R.random() < 0.6 else x
        hit = {">": x > k, "<": x < k, "==": x == k}[op]
        name = R.choice(["Test", "Skontroluj", "Over"])
        body = [W(l1), f"if (x {op} {k})", "    return;", W(l2)]
        code = prog([f"{name}({x});", W(l3)], fn(f"void {name}(int x)", body))
        out = l1 + ("" if hit else l2) + l3
        wrong = pick_wrong(out, [l1 + l2 + l3 if hit else l1 + l3, l1, l3, l1 + l2])
        return b.add("fn-return-ends", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=(f"Podmienka `x {op} {k}` platí, `return` okamžite ukončí funkciu – riadok s `{l2}` sa nevykoná. Potom program pokračuje výpisom `{l3}`." if hit
                              else f"Podmienka `x {op} {k}` neplatí, takže `return` sa nevykoná a funkcia vypíše aj `{l2}`."),
                     en_expl=(f"The condition `x {op} {k}` holds, so `return` ends the function at once – the line with `{l2}` doesn't run. Then the program prints `{l3}`." if hit
                              else f"The condition `x {op} {k}` is false, so `return` doesn't run and the function prints `{l2}` too."),
                     verify={"type": "output"})
    fill(b, "fn-return-ends", 25, return_ends)

    def param_copy():
        a = R.randint(1, 20); var = R.choice(["a", "cislo", "skore", "n"])
        ch = R.choice([("x = x + 10;", lambda x: x + 10), ("x = x * 2;", lambda x: x * 2), ("x = 0;", lambda x: 0), ("x = x - 5;", lambda x: x - 5)])
        changed = ch[1](a)
        if changed == a:
            return False
        name = R.choice(["Zmen", "Zvys", "Uprav"])
        code = prog([f"int {var} = {a};", f"{name}({var});"], fn(f"void {name}(int x)", [ch[0]]))
        wrong = pick_wrong(a, [changed, 0, 10, a + 1])
        return b.add("fn-param-copy", 2, code=code, sk_body=val_q(var)[0], en_body=val_q(var)[1],
                     answers=[code_ans(a)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Parameter `x` je kópia hodnoty `{var}`; zmena `x` vo funkcii premennú `{var}` nezmení.",
                     en_expl=f"The parameter `x` is a copy of `{var}`'s value; changing `x` in the function doesn't change `{var}`.",
                     verify={"type": "value", "expr": var})
    fill(b, "fn-param-copy", 25, param_copy)

    def ignored_return():
        name, expr, f = R.choice(UNARY[:6]); x = R.randint(2, 15)
        ret = f(x)
        code = prog([f"int x = {x};", f"{name}(x);"], fn(f"int {name}(int n)", [f"return {expr.replace('x', 'n')};"]))
        wrong = pick_wrong(x, [ret, 0, x + 1, x - 1])
        return b.add("fn-ignored-return", 2, code=code, sk_body=val_q("x")[0], en_body=val_q("x")[1],
                     answers=[code_ans(x)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Funkcia síce vráti `{ret}`, ale výsledok sa nikam neuložil – `x` sa nezmenila.",
                     en_expl=f"The function does return `{ret}`, but the result isn't stored anywhere – `x` doesn't change.",
                     verify={"type": "value", "expr": "x"})
    fill(b, "fn-ignored-return", 25, ignored_return)

    def arg_order():
        form = R.choice(["Rozdiel", "Rozdiel", "Podiel", "Spoj", "Mocnina"])
        if form == "Rozdiel":
            a, c = R.randint(1, 20), R.randint(1, 20)
            if a == c:
                return False
            f = fn("int Rozdiel(int a, int b)", ["return a - b;"]); v = a - c; sw = c - a; call = f"Rozdiel({a}, {c})"
            wrong = pick_wrong(v, [sw, a + c, a * c]); ans = [code_ans(v)] + [code_ans(w) for w in wrong]; t = "int"
        elif form == "Podiel":
            c = R.randint(2, 6); a = c * R.randint(2, 6)
            f = fn("int Podiel(int a, int b)", ["return a / b;"]); v = a // c; call = f"Podiel({a}, {c})"
            wrong = pick_wrong(v, [c // a, a * c, a - c]); ans = [code_ans(v)] + [code_ans(w) for w in wrong]; t = "int"
        elif form == "Spoj":
            w1, w2 = R.sample(["Ahoj", "svet", "C#", "kód", "Eva", "Ján", "pes", "mačka"], 2)
            f = fn("string Spoj(string a, string b)", ['return a + "-" + b;']); v = f'"{w1}-{w2}"'; call = f'Spoj("{w1}", "{w2}")'
            ans = [code_ans(v), code_ans(f'"{w2}-{w1}"'), code_ans(f'"{w1}{w2}"'), code_ans(f'"a-b"')]; t = "string"
        else:
            z, n = R.randint(2, 4), R.randint(2, 3)
            if z == n:
                return False
            f = fn("int Mocnina(int z, int n)", ["int r = 1;", "for (int i = 0; i < n; i++)", "    r = r * z;", "return r;"]); v = z ** n; call = f"Mocnina({z}, {n})"
            wrong = pick_wrong(v, [n ** z, z * n, z + n]); ans = [code_ans(v)] + [code_ans(w) for w in wrong]; t = "int"
        code = prog([f"{t} v = {call};"], f)
        return b.add("fn-arg-order", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1], answers=ans,
                     sk_expl="Argumenty sa priradia parametrom podľa poradia: prvý argument do prvého parametra, druhý do druhého.",
                     en_expl="Arguments go to parameters by position: the first argument to the first parameter, the second to the second.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "fn-arg-order", 25, arg_order)

    def string_fn():
        form = R.choice(["pozdrav", "opakuj", "prve", "dlzka", "posledne"])
        word = R.choice(["Eva", "Ján", "Peter", "Zuzana", "Robot", "Lucia", "Tomáš", "Mária"])
        if form == "pozdrav":
            f = fn("string Pozdrav(string meno)", ['return "Ahoj " + meno;']); call = f'Pozdrav("{word}")'; t = "string"
            v = f'"Ahoj {word}"'; ans = [v, f'"Ahoj{word}"', f'"{word}"', '"Ahoj meno"']
        elif form == "opakuj":
            n = R.randint(2, 3); w = word[:2]
            f = fn("string Opakuj(string text, int n)", ['string s = "";', "for (int i = 0; i < n; i++)", "    s = s + text;", "return s;"]); call = f'Opakuj("{w}", {n})'; t = "string"
            v = f'"{w * n}"'; ans = [v, f'"{w * (n - 1)}"', f'"{w * (n + 1)}"', f'"{w}{n}"']
        elif form == "prve":
            f = fn("char PrvePismeno(string s)", ["return s[0];"]); call = f'PrvePismeno("{word}")'; t = "char"
            v = f"'{word[0]}'"; ans = [v, f'"{word[0]}"', f"'{word[1]}'", f'"{word}"']
        elif form == "posledne":
            f = fn("char PoslednePismeno(string s)", ["return s[s.Length - 1];"]); call = f'PoslednePismeno("{word}")'; t = "char"
            v = f"'{word[-1]}'"; ans = [v, f"'{word[-2]}'", f"'{word[0]}'", f'"{word[-1]}"']
        else:
            f = fn("int Dlzka(string s)", ["return s.Length;"]); call = f'Dlzka("{word}")'; t = "int"
            v = str(len(word)); ans = [v, str(len(word) - 1), str(len(word) + 1), f'"{word}"']
        if len(set(ans)) < 4:
            return False
        name = "s" if t == "string" else ("c" if t == "char" else "n")
        code = prog([f"{t} {name} = {call};"], f)
        return b.add("fn-string", 2, code=code, sk_body=val_q(name)[0], en_body=val_q(name)[1], answers=[code_ans(a) for a in ans],
                     sk_expl=f"Funkcia vráti `{v}`.", en_expl=f"The function returns `{v}`.",
                     verify={"type": "value", "expr": name})
    fill(b, "fn-string", 25, string_fn)

    def in_loop():
        name, expr, f = R.choice([UNARY[0], UNARY[2], UNARY[3], UNARY[4], UNARY[1]])
        a, n = R.randint(0, 2), R.randint(3, 5)
        vals = [f(i) for i in range(a, a + n)]
        out = " ".join(map(str, vals))
        code = prog([f"for (int i = {a}; i < {a + n}; i++)", f"    Console.Write({name}(i) + \" \");"], fn(f"int {name}(int x)", [f"return {expr};"]))
        wrong = pick_wrong(out, [" ".join(str(i) for i in range(a, a + n)), " ".join(map(str, vals + [f(a + n)])), " ".join(map(str, vals[1:])),
                                 " ".join(str(UNARY[5][2](i)) for i in range(a, a + n))])
        return b.add("fn-in-loop", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Pre každé `i` sa zavolá `{name}(i)`: {', '.join(map(str, vals))}.",
                     en_expl=f"For each `i`, `{name}(i)` is called: {', '.join(map(str, vals))}.",
                     verify={"type": "output"})
    fill(b, "fn-in-loop", 25, in_loop)

    HD = [("vráti priemer dvoch celých čísel", "returns the average of two whole numbers", "double Priemer(int a, int b)",
           ["void Priemer(int a, int b)", "double Priemer(a, b)", "int Priemer(int a)"]),
          ("zistí, či je číslo kladné", "checks whether a number is positive", "bool JeKladne(int x)", ["int JeKladne(int x)", "bool JeKladne()", "void JeKladne(bool x)"]),
          ("vypíše pozdrav pre zadané meno", "prints a greeting for the given name", "void Pozdrav(string meno)", ["string Pozdrav()", "void Pozdrav(meno)", "int Pozdrav(string meno)"]),
          ("vráti väčšie z dvoch čísel", "returns the larger of two numbers", "int Max(int a, int b)", ["void Max(int a, int b)", "int Max(int a)", "bool Max(int a, int b)"]),
          ("vráti dĺžku textu", "returns the length of a text", "int Dlzka(string text)", ["string Dlzka(int text)", "void Dlzka(string text)", "int Dlzka(text)"]),
          ("vráti prvé písmeno slova", "returns the first letter of a word", "char PrvePismeno(string slovo)", ["string PrvePismeno(char slovo)", "char PrvePismeno()", "void PrvePismeno(string slovo)"]),
          ("vráti text zopakovaný n-krát", "returns a text repeated n times", "string Opakuj(string text, int n)", ["string Opakuj(int text, string n)", "void Opakuj(string text, int n)", "string Opakuj(text, n)"]),
          ("vráti počet slov v texte", "returns the number of words in a text", "int PocetSlov(string text)", ["string PocetSlov(int text)", "void PocetSlov(string text)", "int PocetSlov()", "bool PocetSlov(string text)"]),
          ("zistí podľa veku, či je žiak plnoletý", "checks from the age whether a student is an adult", "bool JePlnolety(int vek)", ["int JePlnolety(int vek)", "bool JePlnolety(vek)", "void JePlnolety(int vek)", "bool JePlnolety(string vek)"]),
          ("vypíše čiaru z n hviezdičiek", "prints a line of n stars", "void Ciara(int n)", ["int Ciara(int n)", "void Ciara()", "string Ciara(n)", "void Ciara(string n)"]),
          ("vráti známku ako písmeno podľa bodov", "returns a letter grade based on points", "char Znamka(int body)", ["int Znamka(char body)", "string Znamka()", "char Znamka(body)", "void Znamka(int body)"]),
          ("vráti celé meno spojené z mena a priezviska", "returns the full name joined from the first name and surname", "string CeleMeno(string meno, string priezvisko)",
           ["void CeleMeno(string meno, string priezvisko)", "string CeleMeno(meno, priezvisko)", "string CeleMeno(string meno)", "int CeleMeno(string meno, string priezvisko)"]),
          ("vypočíta obsah obdĺžnika so stranami a, b (celé čísla)", "computes the area of a rectangle with sides a, b (whole numbers)", "int Obsah(int a, int b)",
           ["void Obsah(int a, int b)", "int Obsah(int a)", "Obsah(int a, int b)"])]
    def header_from_desc():
        dsk, den, good, bads = R.choice(HD)
        wrong = R.sample(bads, 3)
        q = R.choice([("Ktorá hlavička patrí funkcii, ktorá {d}?", "Which header belongs to a function that {d}?"),
                      ("Funkcia {d}. Ktorá hlavička je správna?", "A function {d}. Which header is correct?")])
        return b.add("fn-header-from-desc", 2, code=None, sk_body=q[0].format(d=dsk), en_body=q[1].format(d=den),
                     answers=[code_ans(good)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Návratový typ zodpovedá tomu, čo funkcia vráti, a každý parameter má typ: `{good}`.",
                     en_expl=f"The return type matches what the function returns, and every parameter has a type: `{good}`.",
                     verify={"type": "none"})
    fill(b, "fn-header-from-desc", 25, header_from_desc, tries=4000)

    def compile_basic():
        decls = prog([], fn("void VypisAhoj()", ['Console.Write("Ahoj");']), fn("int Dvakrat(int x)", ["return x * 2;"])).strip()
        bad = R.choice(["int x = VypisAhoj();", "int y = Dvakrat();", 'int y = Dvakrat("5");', "string s = Dvakrat(5);", "VypisAhoj(5);", "bool b = Dvakrat(3);", "int y = Dvakrat(5, 1);"])
        tricky = ["Dvakrat(5);", "double d = Dvakrat(4);", "int z = Dvakrat(Dvakrat(2));"]
        normal = ["int y = Dvakrat(5);", "VypisAhoj();", "int a = 3;"]
        valid = R.sample(tricky, R.choice([1, 2]))
        valid += R.sample(normal, 3 - len(valid))
        R.shuffle(valid)
        reasons = {"int x = VypisAhoj();": ("`VypisAhoj` je `void` – nevracia nič, čo by sa dalo uložiť", "`VypisAhoj` is `void` – it returns nothing that could be stored"),
                   "int y = Dvakrat();": ("chýba argument", "the argument is missing"), 'int y = Dvakrat("5");': ("argument musí byť `int`, nie `string`", "the argument must be an `int`, not a `string`"),
                   "string s = Dvakrat(5);": ("`Dvakrat` vracia `int`, nedá sa uložiť do `string`", "`Dvakrat` returns an `int`, which can't be stored in a `string`"),
                   "VypisAhoj(5);": ("`VypisAhoj` nemá žiadny parameter", "`VypisAhoj` has no parameter"), "bool b = Dvakrat(3);": ("`int` sa nedá uložiť do `bool`", "an `int` can't be stored in a `bool`"),
                   "int y = Dvakrat(5, 1);": ("`Dvakrat` má iba jeden parameter", "`Dvakrat` has only one parameter")}
        rsk, ren = reasons[bad]
        return b.add("fn-compile-basic", 2, code=decls,
                     sk_body="{code}\nKtorý riadok v hlavnom programe spôsobí chybu pri preklade?", en_body="{code}\nWhich line in the main program causes a compile error?",
                     answers=[code_ans(bad)] + [code_ans(v) for v in valid],
                     sk_expl=f"`{bad}` sa nedá preložiť: {rsk}." + (" `Dvakrat(5);` je v poriadku – výsledok sa môže aj zahodiť." if "Dvakrat(5);" in valid else ""),
                     en_expl=f"`{bad}` does not compile: {ren}." + (" `Dvakrat(5);` is fine – the result may be thrown away." if "Dvakrat(5);" in valid else ""),
                     verify={"type": "which-line", "expect": "compile-error"})
    fill(b, "fn-compile-basic", 25, compile_basic)

    # =================================================================== HARD
    RB = [("x >= a && x < b", lambda x, a, c: a <= x < c), ("x > a && x <= b", lambda x, a, c: a < x <= c), ("x < a || x > b", lambda x, a, c: x < a or x > c),
          ("x >= a && x <= b", lambda x, a, c: a <= x <= c), ("x <= a || x >= b", lambda x, a, c: x <= a or x >= c)]
    def range_bool():
        expr, f = R.choice(RB); a = R.randint(0, 10); c = a + R.randint(3, 10)
        x = R.choice([a, c, a - 1, c + 1, R.randint(a, c)])
        v = f(x, a, c)
        code = prog([f"bool v = JeVRozsahu({x}, {a}, {c});"], fn("bool JeVRozsahu(int x, int a, int b)", [f"return {expr};"]))
        parts = expr.split(" && ") if "&&" in expr else expr.split(" || ")
        def evp(p):
            return eval(p.replace("x", str(x)).replace("a", str(a)).replace("b", str(c)))
        steps = ", ".join(f"`{p.replace('x', str(x)).replace('a', str(a)).replace('b', str(c))}` je `{bstr(evp(p))}`" for p in parts)
        return b.add("fn-range-bool", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1], answers=bool_answers(v),
                     sk_expl=f"Pre `x = {x}`, `a = {a}`, `b = {c}`: {steps}, výsledok `{bstr(v)}`.",
                     en_expl=f"For `x = {x}`, `a = {a}`, `b = {c}`: {steps.replace(' je ', ' is ')}, result `{bstr(v)}`.",
                     verify={"type": "value", "expr": "v", "expected": bstr(v)})
    fill(b, "fn-range-bool", 25, range_bool)

    def call_in_condition():
        n = R.randint(1, 4); body_ch, f_ch = R.sample(["A", "*", "#", "B", "o"], 2)
        code = prog([f"for (int i = 0; i < Pocet(); i++)", f"    {W(body_ch)}"], fn("int Pocet()", [W(f_ch), f"return {n};"]))
        out = (f_ch + body_ch) * n + f_ch
        wrong = pick_wrong(out, [f_ch + body_ch * n, (f_ch + body_ch) * n, body_ch * n, f_ch * n + body_ch * n, body_ch * n + f_ch, f_ch * (n + 1) + body_ch * n])
        return b.add("fn-call-in-condition", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Podmienka sa kontroluje pred každou iteráciou aj na konci – `Pocet()` sa zavolá {n + 1}-krát (o jeden raz viac, ako sa vykoná telo).",
                     en_expl=f"The condition is checked before each iteration and once more at the end – `Pocet()` is called {n + 1} times (once more than the body runs).",
                     verify={"type": "output"})
    fill(b, "fn-call-in-condition", 25, call_in_condition)

    NAP_BAD = [("int F(int x) { if (x > 0) return 1; }", "nie každá cesta vracia hodnotu (pre `x <= 0` chýba `return`)", "not every path returns a value (`return` is missing for `x <= 0`)"),
               ("void G() { return 5; }", "`void` funkcia nemôže vrátiť hodnotu", "a `void` function can't return a value"),
               ('int H(int x) { return "x"; }', "funkcia má vrátiť `int`, nie `string`", "the function must return an `int`, not a `string`"),
               ("bool J(int x) { if (x > 0) return true; else if (x < 0) return false; }", "pre `x == 0` funkcia nič nevráti", "for `x == 0` the function returns nothing"),
               ("int K(int x) { int y = x * 2; }", "chýba `return`", "`return` is missing")]
    NAP_OK = ["int F(int x) { if (x > 0) return 1; return 0; }", "void G() { return; }", "int H(int x) { if (x > 0) return 1; else return 0; }",
              "bool J(int x) { return x > 0; }", "int K(int x) { return x * 2; }", "void L(int x) { if (x > 0) return; Console.Write(x); }"]
    def not_all_paths():
        bad, rsk, ren = R.choice(NAP_BAD)
        valid = R.sample(NAP_OK, 3)
        return b.add("fn-not-all-paths", 3, code=None, sk_body="Ktorá funkcia spôsobí chybu pri preklade?", en_body="Which function causes a compile error?",
                     answers=[code_ans(bad)] + [code_ans(v) for v in valid],
                     sk_expl=f"`{bad}` sa nedá preložiť: {rsk}.", en_expl=f"`{bad}` does not compile: {ren}.",
                     verify={"type": "which-line", "expect": "compile-error"})
    fill(b, "fn-not-all-paths", 25, not_all_paths)

    def scope():
        fname = R.choice(["Vypocitaj", "Spracuj", "Spocitaj"]); local = R.choice(["vysledok", "medzivysledok", "pom"]); par = R.choice(["n", "x", "hodnota"])
        k = R.randint(2, 5); arg = R.randint(1, 9); top = R.choice(["a", "cislo", "v"])
        code = prog([f"int {top} = {arg};", f"int r = {fname}({top});"], fn(f"int {fname}(int {par})", [f"int {local} = {par} * {k};", f"return {local};"]))
        bad = R.choice([f"Console.Write({local});", f"int z = {local} + 1;", f"Console.Write({par});", f"{local} = 0;"])
        valid = R.sample([f"Console.Write(r);", f"Console.Write({top});", f"int z = {fname}(r);", f"r = r + {top};", f"int w = r * 2;"], 3)
        which = local if local in bad else par
        return b.add("fn-scope", 3, code=code,
                     sk_body="{code}\nKtorý riadok, pridaný do hlavného programu, spôsobí chybu pri preklade?",
                     en_body="{code}\nWhich line, added to the main program, causes a compile error?",
                     answers=[code_ans(bad)] + [code_ans(v) for v in valid],
                     sk_expl=f"Premenná `{which}` existuje iba vnútri funkcie `{fname}` – hlavný program ju nevidí.",
                     en_expl=f"The variable `{which}` only exists inside the function `{fname}` – the main program can't see it.",
                     verify={"type": "which-line", "expect": "compile-error"})
    fill(b, "fn-scope", 25, scope)

    def call_order_expr():
        la, lb = R.sample("ABCXYZ", 2); ra, rb = R.randint(1, 9), R.randint(1, 9)
        op = R.choice(["+", "*", "-"])
        first_b = R.random() < 0.3
        expr = f"B() {op} A()" if first_b else f"A() {op} B()"
        val = eval(f"{rb} {op} {ra}") if first_b else eval(f"{ra} {op} {rb}")
        order = lb + la if first_b else la + lb
        out = order + str(val)
        wrong = pick_wrong(out, [str(val) + order, order[::-1] + str(val), order, la + lb + str(eval(f'{ra} + {rb}'))])
        code = prog([f"int v = {expr};", "Console.Write(v);"], fn("int A()", [W(la), f"return {ra};"]), fn("int B()", [W(lb), f"return {rb};"]))
        return b.add("fn-call-order-expr", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Výraz sa vyhodnocuje zľava doprava: najprv sa zavolá {'`B()`' if first_b else '`A()`'}, potom {'`A()`' if first_b else '`B()`'} (každá vypíše svoje písmeno), nakoniec sa vypíše výsledok {val}.",
                     en_expl=f"The expression is evaluated left to right: first {'`B()`' if first_b else '`A()`'}, then {'`A()`' if first_b else '`B()`'} (each prints its letter), and finally the result {val} is printed.",
                     verify={"type": "output"})
    fill(b, "fn-call-order-expr", 25, call_order_expr)

    def early_return():
        form = R.choice(["delitel", "prvocislo", "cifra", "prvy_vacsi"])
        if form == "delitel":
            n = R.choice([15, 21, 25, 35, 49, 27, 33, 39, 13, 17, 91]); d = next((i for i in range(2, n) if n % i == 0), n)
            f = fn("int PrvyDelitel(int n)", ["for (int i = 2; i < n; i++)", "{", "    if (n % i == 0)", "        return i;", "}", "return n;"]); call = f"PrvyDelitel({n})"; t = "int"
            v = d; divs = [i for i in range(2, n) if n % i == 0]
            wrong = pick_wrong(v, ([divs[-1]] if divs else []) + [n, 2, 1, d + 2])
            esk, een = (f"`return` v cykle ukončí celú funkciu hneď pri prvom deliteli ({d})." if d != n else f"{n} nemá deliteľa medzi 2 a {n - 1}, cyklus dobehne a vráti sa `{n}`.",
                        f"`return` inside the loop ends the whole function at the first divisor ({d})." if d != n else f"{n} has no divisor between 2 and {n - 1}, so the loop finishes and `{n}` is returned.")
            ans = [code_ans(v)] + [code_ans(w) for w in wrong]
        elif form == "prvocislo":
            n = R.choice([7, 9, 11, 15, 13, 21, 2, 25, 29, 33]); v = all(n % i for i in range(2, n))
            f = fn("bool JePrvocislo(int n)", ["for (int i = 2; i < n; i++)", "{", "    if (n % i == 0)", "        return false;", "}", "return true;"]); call = f"JePrvocislo({n})"; t = "bool"
            ans = bool_answers(v)
            esk = "Pri prvom deliteli `return false` funkciu hneď ukončí." if not v else "Žiadne `i` nedelí n, cyklus dobehne a vykoná sa `return true`."
            een = "At the first divisor, `return false` ends the function right away." if not v else "No `i` divides n, so the loop finishes and `return true` runs."
        elif form == "cifra":
            n = R.randint(100, 9999); c = R.randint(0, 9); v = str(c) in str(n)
            f = fn("bool ObsahujeCifru(int n, int c)", ["while (n > 0)", "{", "    if (n % 10 == c)", "        return true;", "    n = n / 10;", "}", "return false;"]); call = f"ObsahujeCifru({n}, {c})"; t = "bool"
            ans = bool_answers(v)
            esk = f"Cifry {n} sa kontrolujú odzadu; " + ("pri nájdení cifry {c} `return true` ukončí funkciu.".replace("{c}", str(c)) if v else f"cifra {c} sa nenájde, preto `return false`.")
            een = f"The digits of {n} are checked from the end; " + (f"when {c} is found, `return true` ends the function." if v else f"{c} isn't found, so `return false`.")
        else:
            arr = [R.randint(1, 20) for _ in range(5)]; lim = R.randint(5, 15); v = next((x for x in arr if x > lim), -1)
            f = fn("int PrvyVacsi(int a, int b, int c, int d, int e, int hranica)", ["if (a > hranica) return a;", "if (b > hranica) return b;", "if (c > hranica) return c;",
                                                                                     "if (d > hranica) return d;", "if (e > hranica) return e;", "return -1;"])
            call = f"PrvyVacsi({', '.join(map(str, arr))}, {lim})"; t = "int"
            bigger = [x for x in arr if x > lim]
            wrong = pick_wrong(v, (bigger[1:] if len(bigger) > 1 else []) + [max(arr), -1, lim, arr[0]])
            ans = [code_ans(v)] + [code_ans(w) for w in wrong]
            esk = f"Prvý `return`, ktorého podmienka platí, funkciu ukončí – vráti sa `{v}`."
            een = f"The first `return` whose condition holds ends the function – `{v}` is returned."
        code = prog([f"{t} v = {call};"], f)
        return b.add("fn-early-return-loop", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1], answers=ans,
                     sk_expl=esk, en_expl=een, verify={"type": "value", "expr": "v", **({"expected": bstr(v)} if t == "bool" else {})})
    fill(b, "fn-early-return-loop", 25, early_return)

    def names_positions():
        a, c = R.randint(1, 15), R.randint(1, 15)
        if a == c:
            return False
        form = R.choice(["Rozdiel", "Podiel2", "Vzorec"])
        if form == "Rozdiel":
            f = fn("int Rozdiel(int a, int b)", ["return a - b;"]); real = c - a; naive = a - c; call = "Rozdiel(b, a)"
        elif form == "Podiel2":
            f = fn("int Vzorec(int a, int b)", ["return a * 10 + b;"]); real = c * 10 + a; naive = a * 10 + c; call = "Vzorec(b, a)"
        else:
            f = fn("int Vzorec(int a, int b)", ["return 2 * a + b;"]); real = 2 * c + a; naive = 2 * a + c; call = "Vzorec(b, a)"
        code = prog([f"int a = {a};", f"int b = {c};", f"int v = {call};"], f)
        wrong = pick_wrong(real, [naive, a + c, a * c, -real])
        return b.add("fn-names-vs-positions", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(real)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Na menách nezáleží: prvý argument (`b` = {c}) ide do parametra `a`, druhý (`a` = {a}) do parametra `b`.",
                     en_expl=f"Names don't matter: the first argument (`b` = {c}) goes to parameter `a`, the second (`a` = {a}) to parameter `b`.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "fn-names-vs-positions", 25, names_positions)

    def int_division():
        a, c = R.randint(1, 10), R.randint(1, 10)
        if (a + c) % 2 == 0:
            return False
        fixed = R.random() < 0.33
        div = "2.0" if fixed else "2"
        exact = (a + c) / 2; trunc = (a + c) // 2
        correct = fmt_double(exact) if fixed else str(trunc)
        wrong = pick_wrong(correct, [str(trunc) if fixed else fmt_double(exact), str(trunc + 1), str(a + c)])
        code = prog([f"double v = Priemer({a}, {c});"], fn("double Priemer(int a, int b)", [f"return (a + b) / {div};"]))
        return b.add("fn-int-division", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong],
                     sk_expl=("`(a + b) / 2.0` delí číslom typu `double`, preto sa desatinná časť zachová." if fixed
                              else f"`(a + b) / 2` je delenie dvoch `int` – `{a + c} / 2` = {trunc}, desatinná časť sa zahodí ešte pred uložením do `double`."),
                     en_expl=("`(a + b) / 2.0` divides by a `double`, so the decimal part is kept." if fixed
                              else f"`(a + b) / 2` divides two `int`s – `{a + c} / 2` = {trunc}; the fraction is dropped before the result becomes a `double`."),
                     verify={"type": "value", "expr": "v", "expected": correct})
    fill(b, "fn-int-division", 25, int_division)

    KROK = [("x * 2 - 1", lambda x: x * 2 - 1, ["return x * 2 - 1;"]), ("x + 3", lambda x: x + 3, ["return x + 3;"]),
            ("párne → x / 2, nepárne → x + 3", lambda x: x // 2 if x % 2 == 0 else x + 3, ["if (x % 2 == 0)", "    return x / 2;", "return x + 3;"]),
            ("x * x - x", lambda x: x * x - x, ["return x * x - x;"])]
    def chained_assign():
        desc, f, body = R.choice(KROK); x0 = R.randint(1, 9); n = R.randint(2, 4)
        vals = [x0]
        for _ in range(n):
            vals.append(f(vals[-1]))
        if abs(vals[-1]) > 500:
            return False
        code = prog([f"int x = {x0};"] + ["x = Krok(x);"] * n, fn("int Krok(int x)", body))
        wrong = pick_wrong(vals[-1], [vals[-2], f(vals[-1]), vals[1]])
        if not wrong:
            return False
        return b.add("fn-chained-assign", 3, code=code, sk_body=val_q("x")[0], en_body=val_q("x")[1],
                     answers=[code_ans(vals[-1])] + [code_ans(w) for w in wrong],
                     sk_expl=f"Postupne: {' → '.join(map(str, vals))}.", en_expl=f"Step by step: {' → '.join(map(str, vals))}.",
                     verify={"type": "value", "expr": "x"})
    fill(b, "fn-chained-assign", 25, chained_assign)

    def while_step():
        form = R.choice(["collatz", "collatz", "half"])
        if form == "collatz":
            x0 = R.randint(3, 40); body = ["if (x % 2 == 0)", "    return x / 2;", "return 3 * x + 1;"]
            f = lambda x: x // 2 if x % 2 == 0 else 3 * x + 1
        else:
            x0 = R.choice([16, 32, 64, 8, 128, 4]); body = ["return x / 2;"]; f = lambda x: x // 2
        vals, x = [x0], x0
        while x != 1:
            x = f(x); vals.append(x)
        steps = len(vals) - 1
        if not 2 <= steps <= 20:
            return False
        code = prog([f"int x = {x0};", "int pocet = 0;", "while (x != 1)", "{", "    x = Krok(x);", "    pocet = pocet + 1;", "}"], fn("int Krok(int x)", body))
        wrong = pick_wrong(steps, [steps - 1, steps + 1, max(vals)])
        return b.add("fn-while-step", 3, code=code, sk_body=val_q("pocet")[0], en_body=val_q("pocet")[1],
                     answers=[code_ans(steps)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Postupnosť: {' → '.join(map(str, vals))} – to je {steps} krokov.",
                     en_expl=f"The sequence: {' → '.join(map(str, vals))} – that's {steps} steps.",
                     verify={"type": "value", "expr": "pocet"})
    fill(b, "fn-while-step", 25, while_step)

    def change_vs_assign():
        a0 = R.randint(1, 9); b0 = R.randint(1, 9); k = R.randint(2, 9)
        op = R.choice([("+", lambda x: x + k), ("*", lambda x: x * k)])
        code = prog([f"int a = {a0};", f"int b = {b0};", "Zmen(a);", "b = Zmen(b);"], fn("int Zmen(int x)", [f"x = x {op[0]} {k};", "return x;"]))
        fa, fb = op[1](a0), op[1](b0)
        c = f"a = {a0}, b = {fb}"
        wrong = pick_wrong(c, [f"a = {fa}, b = {fb}", f"a = {a0}, b = {b0}", f"a = {fa}, b = {b0}"])
        return b.add("fn-change-vs-assign", 3, code=code,
                     sk_body="{code}\nAké hodnoty budú mať `a` a `b`?", en_body="{code}\nWhat values will `a` and `b` have?",
                     answers=[code_ans(c)] + [code_ans(w) for w in wrong],
                     sk_expl="`Zmen(a)` zmení iba kópiu a výsledok zahodí; `b = Zmen(b)` výsledok uloží.",
                     en_expl="`Zmen(a)` changes only a copy and throws the result away; `b = Zmen(b)` stores it.",
                     verify={"type": "value", "expr": '$"a = {a}, b = {b}"'})
    fill(b, "fn-change-vs-assign", 25, change_vs_assign)

    def trace():
        form = R.choice(["fg", "loop", "cond"])
        x0 = R.randint(1, 8)
        if form == "fg":
            k = R.randint(2, 4); m = R.randint(1, 5)
            fns = [fn("int F(int x)", [f"return G(x) + {m};"]), fn("int G(int x)", [f"return x * {k};"])]
            v = x0 * k + m; call = f"F({x0})"; wrong = [x0 + m, (x0 + m) * k, x0 * k]
            steps = f"F({x0}) = G({x0}) + {m} = {x0 * k} + {m} = {v}"
        elif form == "loop":
            n = R.randint(2, 4)
            fns = [fn("int F(int n)", ["int s = 0;", "for (int i = 1; i <= n; i++)", "    s = s + G(i);", "return s;"]), fn("int G(int x)", ["return x * x;"])]
            v = sum(i * i for i in range(1, n + 1)); call = f"F({n})"; wrong = [n * (n + 1) // 2, v - n * n, n * n]
            steps = f"F({n}) = " + " + ".join(f"G({i})" for i in range(1, n + 1)) + " = " + " + ".join(str(i * i) for i in range(1, n + 1)) + f" = {v}"
        else:
            t = R.randint(3, 8)
            fns = [fn("int F(int x)", [f"if (x > {t})", "    return G(x - 1);", "return G(x + 1);"]), fn("int G(int x)", ["return x * 2;"])]
            v = (x0 - 1) * 2 if x0 > t else (x0 + 1) * 2; call = f"F({x0})"; wrong = [(x0 + 1) * 2 if x0 > t else (x0 - 1) * 2, x0 * 2, x0 + 1]
            steps = f"`{x0} > {t}` je `{bstr(x0 > t)}` → G({x0 - 1 if x0 > t else x0 + 1}) = {v}"
        code = prog([f"int v = {call};"], *fns)
        wrong = pick_wrong(v, wrong)
        return b.add("fn-trace", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Volania: {steps}.", en_expl=f"Calls: {steps.replace(' je ', ' is ')}.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "fn-trace", 25, trace)
    return b


if __name__ == "__main__":
    main().write()
