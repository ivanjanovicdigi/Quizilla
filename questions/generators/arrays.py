"""Generator for topic arrays (39 templates × 25). No foreach, no 2D; Array.Sort / Reverse / IndexOf only."""
import random
from common import Batch, fill, code_ans, pick_wrong, fmt_double

R = random.Random(20261026)
DATE = "2026-10-22"
OUT_Q = ("{code}\nČo vypíše tento kód?", "{code}\nWhat does this code print?")
CRASH = ("Program spadne (IndexOutOfRangeException)", "The program crashes (IndexOutOfRangeException)")
NOTHING = ("Nič", "Nothing")
PRINT = "for (int i = 0; i < a.Length; i++)\n    Console.Write(a[i]);"
PRINT_SP = "for (int i = 0; i < a.Length; i++)\n    Console.Write(a[i] + \" \");"


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


def arr(vals, name="a", t="int"):
    return f"{t}[] {name} = {{{', '.join(map(str, vals))}}};"


def digits(n, lo=0, hi=9, distinct=True):
    return R.sample(range(lo, hi + 1), n) if distinct else [R.randint(lo, hi) for _ in range(n)]


def s(vals):
    return "".join(map(str, vals))


def sp(vals):
    return " ".join(map(str, vals))


def main():
    b = Batch(f"{DATE}_arrays", "arrays", DATE)

    # =================================================================== EASY
    def index_value():
        n = R.randint(3, 6); a = digits(n, 0, 20); i = R.randrange(n)
        v = a[i]
        cands = ([a[i - 1]] if i > 0 else []) + ([a[i + 1]] if i + 1 < n else []) + [i, a[(i + 2) % n]]
        wrong = pick_wrong(v, cands)
        if not wrong:
            return False
        code = f"{arr(a)}\nint v = a[{i}];"
        return b.add("ar-index-value", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Indexy začínajú od `0`, `a[{i}]` je {i + 1}. prvok: `{v}`.",
                     en_expl=f"Indexes start at `0`; `a[{i}]` is element number {i + 1}: `{v}`.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ar-index-value", 25, index_value)

    def length():
        n = R.randint(2, 7)
        if R.random() < 0.7:
            a = digits(n, 0, 12); code = f"{arr(a)}\nint v = a.Length;"; last = a[-1]
        else:
            names = R.sample(["\"Eva\"", "\"Ján\"", "\"Ola\"", "\"Peter\"", "\"Zuzka\"", "\"Tom\"", "\"Mia\""], n)
            code = f"string[] mena = {{{', '.join(names)}}};\nint v = mena.Length;"; last = None
        wrong = pick_wrong(n, [n - 1, n + 1] + ([last] if isinstance(last, int) else []) + [0])
        return b.add("ar-length", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(n)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`Length` je počet prvkov – pole má {n} prvkov (posledný index je {n - 1}).",
                     en_expl=f"`Length` is the number of elements – the array has {n} (the last index is {n - 1}).",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ar-length", 25, length)

    WHICH = [("prvého", "first", lambda n: 0), ("posledného", "last", lambda n: n - 1), ("druhého", "second", lambda n: 1), ("tretieho", "third", lambda n: 2),
             ("predposledného", "second-to-last", lambda n: n - 2)]
    def first_last():
        n = R.randint(4, 8); a = digits(n, 0, 20)
        wsk, wen, f = R.choice(WHICH); idx = f(n)
        wrong = pick_wrong(idx, [idx + 1, n if idx == n - 1 else idx - 1, a[idx], n])
        if not wrong:
            return False
        return b.add("ar-first-last-index", 1, code=arr(a),
                     sk_body=f"{{code}}\nAký je index **{wsk}** prvku?", en_body=f"{{code}}\nWhat is the index of the **{wen}** element?",
                     answers=[code_ans(idx)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Indexy idú od `0` po `Length - 1` = {n - 1}; {wsk} prvok má index `{idx}`.",
                     en_expl=f"Indexes go from `0` to `Length - 1` = {n - 1}; the {wen} element has index `{idx}`.",
                     verify={"type": "none"})
    fill(b, "ar-first-last-index", 25, first_last)

    GOOD = ["int[] a = {1, 2, 3};", "int[] a = new int[3];", 'string[] s = {"x", "y"};', "double[] d = new double[5];", "bool[] b = new bool[2];",
            "char[] c = {'a', 'b'};", "int[] cisla = {7};", "double[] d = {1.5, 2.5};"]
    BAD = ["int a[] = {1, 2};", "int[] a = new int;", "int[3] a;", 'int[] a = {"1", "2"};', "int[] a = new int(3);", "int[] a = int[3];",
           "int a = {1, 2, 3};", "[]int a = {1, 2};", "int[] a = new[3];", "string[] s = {'x', 'y'};"]
    def declaration():
        good = R.choice(GOOD); wrong = R.sample(BAD, 3)
        return b.add("ar-declaration", 1, code=None, sk_body="Ktorá deklarácia poľa je správna?", en_body="Which array declaration is correct?",
                     answers=[code_ans(good)] + [code_ans(w) for w in wrong],
                     sk_expl="Pole sa deklaruje ako `typ[] názov` a vytvorí sa zoznamom hodnôt `{…}` alebo cez `new typ[počet]`.",
                     en_expl="An array is declared as `type[] name` and created with a value list `{…}` or `new type[count]`.",
                     verify={"type": "which-line", "expect": "compile-error", "invert": True})
    fill(b, "ar-declaration", 25, declaration)

    DEF = [("int", "0", "int v"), ("bool", "false", "bool v"), ("double", "0", "double v"), ("string", "null", "string v"), ("char", None, None)]
    def default_values():
        t, d, decl = R.choice(DEF[:4]); n = R.randint(2, 8); i = R.randrange(n)
        code = f"{t}[] a = new {t}[{n}];\n{decl} = a[{i}];"
        if t == "string":
            wrong = ['`""`', f"`{i}`", "`\"null\"`"]
        elif t == "bool":
            wrong = ["`true`", f"`{i}`" if i != 0 else "`1`", "`null`"]
        else:
            wrong = [f"`{n}`", f"`{i}`" if i != 0 else "`1`", "`null`"]
        if len(set(wrong + [f"`{d}`"])) < 4:
            wrong = [w for w in wrong if w != f"`{d}`"] + ["`1`" if "`1`" not in wrong else "`-1`"]
        return b.add("ar-default-values", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[f"`{d}`"] + wrong[:3],
                     sk_expl=f"Nové pole sa naplní predvolenými hodnotami – pre `{t}` je to `{d}`.",
                     en_expl=f"A new array is filled with default values – for `{t}` it's `{d}`.",
                     verify={"type": "value", "expr": "v", "expected": d})
    fill(b, "ar-default-values", 25, default_values)

    def change_element():
        n = R.randint(3, 5); a = digits(n, 0, 9); i = R.randrange(n); x = R.choice([v for v in range(10, 30)])
        j = i if R.random() < 0.6 else R.choice([k for k in range(n) if k != i])
        a2 = a[:]; a2[i] = x
        v = a2[j]
        wrong = pick_wrong(v, [a[j], x, a[(j + 1) % n], i])
        code = f"{arr(a)}\na[{i}] = {x};\nint v = a[{j}];"
        return b.add("ar-change-element", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`a[{i}] = {x}` prepíše iba prvok na indexe {i}" + (f", preto `a[{j}]` je teraz `{x}`." if j == i else f"; `a[{j}]` zostáva `{v}`."),
                     en_expl=f"`a[{i}] = {x}` overwrites only the element at index {i}" + (f", so `a[{j}]` is now `{x}`." if j == i else f"; `a[{j}]` stays `{v}`."),
                     verify={"type": "value", "expr": "v"})
    fill(b, "ar-change-element", 25, change_element)

    TERMS = {
        "index": [("poradové číslo prvku v poli, začína od 0", "the position number of an element, starting at 0")],
        "prvok": [("jedna hodnota uložená v poli", "one value stored in the array")],
        "`Length`": [("počet prvkov poľa", "the number of elements in the array")],
        "`new int[5]`": [("vytvorí nové pole s 5 prvkami (všetky 0)", "creates a new array with 5 elements (all 0)")],
        "`Array.Sort(a)`": [("zoradí prvky poľa vzostupne", "sorts the array elements in ascending order")],
        "`Array.Reverse(a)`": [("otočí poradie prvkov poľa", "reverses the order of the array elements")],
        "`Array.IndexOf(a, x)`": [("vráti index prvého výskytu hodnoty x, alebo -1", "returns the index of the first occurrence of x, or -1")],
    }
    FAKE = [("index posledného prvku", "the index of the last element"), ("najväčšia hodnota v poli", "the largest value in the array"),
            ("zoradí prvky zostupne", "sorts the elements in descending order"), ("hodnota prvku na danom indexe", "the value of the element at an index")]
    TQ = [("Čo je {t}?", "What is {t}?"), ("Čo znamená {t}?", "What does {t} mean?"), ("Čo robí / vráti {t}?", "What does {t} do / return?")]
    def term_purpose():
        t = R.choice(list(TERMS)); q = R.choice(TQ)
        correct = TERMS[t][0]
        others = [TERMS[o][0] for o in TERMS if o != t]
        pool = others + FAKE
        R.shuffle(pool)
        sk, en = text_answers([correct] + pool[:3])
        return b.add("ar-term-purpose", 1, code=None, sk_body=q[0].format(t=t), en_body=q[1].format(t=t), answers=sk, en_answers=en,
                     sk_expl=f"{t}: {correct[0]}.", en_expl=f"{t}: {correct[1]}.", verify={"type": "none"})
    fill(b, "ar-term-purpose", 25, term_purpose)

    PT = [("Ako sa volá poradové číslo prvku v poli?", "What is the position number of an element in an array called?", ("index", "index"), [("prvok", "element"), ("dĺžka", "length"), ("hodnota", "value")]),
          ("Ako zistíme počet prvkov poľa `a`?", "How do we get the number of elements of array `a`?", "`a.Length`", ["`a.Count`", "`a.Size`", "`a.Length()`", "`a[a.Length]`"]),
          ("Ktorá metóda zoradí prvky poľa od najmenšieho po najväčší?", "Which method sorts an array from the smallest to the largest?", "`Array.Sort`", ["`Array.Reverse`", "`Array.IndexOf`", "`Length`"]),
          ("Ktorá metóda otočí poradie prvkov poľa?", "Which method reverses the order of the array elements?", "`Array.Reverse`", ["`Array.Sort`", "`Array.IndexOf`", "`a.Length`"]),
          ("Ktorá metóda zistí, na ktorom indexe je hodnota x?", "Which method finds the index of the value x?", "`Array.IndexOf`", ["`Array.Sort`", "`Array.Reverse`", "`a.Length`"]),
          ("Ktorým zápisom vytvoríme pole 5 celých čísel?", "How do we create an array of 5 whole numbers?", "`new int[5]`", ["`new int(5)`", "`int[5]`", "`new int`", "`new[5] int`"]),
          ("Aký je index posledného prvku poľa `a`?", "What is the index of the last element of array `a`?", "`a.Length - 1`", ["`a.Length`", "`a.Length + 1`", "`-1`"]),
          ("Aký je index prvého prvku poľa?", "What is the index of the first element of an array?", "`0`", ["`1`", "`-1`", "`a.Length`"]),
          ("Čo vráti `Array.IndexOf`, keď hodnota v poli nie je?", "What does `Array.IndexOf` return when the value isn't in the array?", "`-1`", ["`0`", "`a.Length`", "`null`"])]
    def purpose_term():
        sq, eq, good, bads = R.choice(PT)
        wrong = R.sample(bads, 3)
        if R.random() < 0.5:
            sq, eq = sq + " Vyber jednu možnosť.", eq + " Pick one option."
        sk, en = text_answers([good] + wrong)
        return b.add("ar-purpose-term", 1, code=None, sk_body=sq, en_body=eq, answers=sk, en_answers=en,
                     sk_expl=f"Správne je {good[0] if isinstance(good, tuple) else good}.", en_expl=f"The correct answer is {good[1] if isinstance(good, tuple) else good}.",
                     verify={"type": "none"})
    fill(b, "ar-purpose-term", 25, purpose_term, tries=5000)

    def loop_print():
        n = R.randint(3, 5); a = digits(n, 0, 9)
        idx = s(range(n))
        wrong = pick_wrong(s(a), [idx, s(a[:-1]), s(a[::-1]), s(a[1:])])
        return b.add("ar-loop-print", 1, code=f"{arr(a)}\n{PRINT}", sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(s(a))] + [code_ans(w) for w in wrong],
                     sk_expl=f"Cyklus prejde indexy 0 až {n - 1} a vypíše hodnoty `a[i]` (nie indexy).",
                     en_expl=f"The loop goes through indexes 0 to {n - 1} and prints the values `a[i]` (not the indexes).",
                     verify={"type": "output"})
    fill(b, "ar-loop-print", 25, loop_print)

    def new_size():
        n = R.randint(2, 10); t = R.choice(["int", "int", "double", "bool", "string"])
        set_line = ""
        x = None
        if R.random() < 0.5 and t == "int":
            x = R.randint(11, 30); set_line = f"\na[0] = {x};"
        code = f"{t}[] a = new {t}[{n}];{set_line}\nint v = a.Length;"
        wrong = pick_wrong(n, [n - 1, 0, x if x else 1, n + 1])
        return b.add("ar-new-size", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(n)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`new {t}[{n}]` vytvorí pole s {n} prvkami; dĺžka sa nemení.",
                     en_expl=f"`new {t}[{n}]` creates an array with {n} elements; the length doesn't change.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ar-new-size", 25, new_size)

    def find_index():
        n = R.randint(4, 6); a = digits(n, 0, 20); i = R.randrange(n); x = a[i]
        wrong = pick_wrong(i, [i + 1, x, i - 1 if i > 0 else n, a.index(a[(i + 1) % n])])
        if not wrong:
            return False
        return b.add("ar-find-index", 1, code=arr(a),
                     sk_body=f"{{code}}\nNa ktorom indexe je hodnota `{x}`?", en_body=f"{{code}}\nAt which index is the value `{x}`?",
                     answers=[code_ans(i)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`{x}` je {i + 1}. prvok, indexy začínajú od 0, preto index `{i}`.",
                     en_expl=f"`{x}` is element number {i + 1}; indexes start at 0, so the index is `{i}`.",
                     verify={"type": "value", "expr": f"Array.IndexOf(a, {x})", "expected": str(i)})
    fill(b, "ar-find-index", 25, find_index)

    ET = [("string", ['"Eva"', '"Ján"', '"Ola"'], "mena", "String"), ("int", ["3", "5", "8"], "cisla", "Int32"), ("double", ["1.5", "2.0"], "ceny", "Double"),
          ("bool", ["true", "false"], "odpovede", "Boolean"), ("char", ["'a'", "'b'", "'c'"], "znaky", "Char"),
          ("int", ["10", "20", "30", "40"], "body", "Int32"), ("string", ['"pes"', '"mačka"'], "zvierata", "String"), ("double", ["36.6", "37.2", "38.0"], "teploty", "Double")]
    NET = {"string": "String", "int": "Int32", "double": "Double", "bool": "Boolean", "char": "Char"}
    def element_type():
        t, vals, name, _ = R.choice(ET)
        form = R.choice(["el", "el", "arr", "len"])
        if form == "el":
            expr = f"{name}[{R.randrange(len(vals))}]"; correct = t; wrong = [f"{t}[]", "int" if t != "int" else "double", "char" if t == "string" else "string"]
            sk_r, en_r = f"Prvok poľa `{t}[]` je typu `{t}`.", f"An element of a `{t}[]` array is a `{t}`."
            net = NET[t]
        elif form == "arr":
            expr = name; correct = f"{t}[]"; wrong = [t, "int", "char" if t != "char" else "string"]
            sk_r, en_r = f"Celé pole je typu `{t}[]`, jeho prvky sú `{t}`.", f"The whole array is a `{t}[]`; its elements are `{t}`."
            net = NET[t] + "[]"
        else:
            expr = f"{name}.Length"; correct = "int"; wrong = [t if t != "int" else "double", f"{t}[]", "string" if t != "string" else "char"]
            sk_r, en_r = "`Length` je počet prvkov, a ten je vždy `int`.", "`Length` is the number of elements, which is always an `int`."
            net = "Int32"
        wrong = pick_wrong(correct, wrong + ["bool", "double"])
        code = f"{t}[] {name} = {{{', '.join(vals)}}};"
        return b.add("ar-element-type", 1, code=code,
                     sk_body=f"{{code}}\nAký typ má `{expr}`?", en_body=f"{{code}}\nWhat is the type of `{expr}`?",
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong], sk_expl=sk_r, en_expl=en_r,
                     verify={"type": "value", "expr": f"({expr}).GetType().Name", "expected": net})
    fill(b, "ar-element-type", 25, element_type)

    # =================================================================== MEDIUM
    def sum_():
        n = R.randint(4, 6); a = [R.randint(-9, 15) for _ in range(n)]
        tot = sum(a)
        wrong = pick_wrong(tot, [tot - a[0], tot - a[-1], sum(range(n)), n])
        code = f"{arr(a)}\nint s = 0;\nfor (int i = 0; i < a.Length; i++)\n    s = s + a[i];"
        acc, steps = 0, []
        for x in a:
            acc += x; steps.append(str(acc))
        return b.add("ar-sum", 2, code=code, sk_body=val_q("s")[0], en_body=val_q("s")[1],
                     answers=[code_ans(tot)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Súčet postupne: {', '.join(steps)}.", en_expl=f"Running sum: {', '.join(steps)}.",
                     verify={"type": "value", "expr": "s"})
    fill(b, "ar-sum", 25, sum_)

    def max_min():
        n = R.randint(3, 6); kind = R.choice(["max", "min"])
        neg_bug = kind == "max" and R.random() < 0.35
        a = [R.randint(-15, -1) for _ in range(n)] if neg_bug else [R.randint(-10, 20) for _ in range(n)]
        op = ">" if kind == "max" else "<"
        start = "0" if neg_bug else "a[0]"
        m = 0 if neg_bug else a[0]
        for x in a:
            if (x > m) if kind == "max" else (x < m):
                m = x
        true_val = max(a) if kind == "max" else min(a)
        other = min(a) if kind == "max" else max(a)
        wrong = pick_wrong(m, [true_val, other, a[0], a[-1]])
        if not wrong:
            return False
        code = f"{arr(a)}\nint m = {start};\nfor (int i = 0; i < a.Length; i++)\n{{\n    if (a[i] {op} m)\n        m = a[i];\n}}"
        if neg_bug:
            esk = f"`m` začína na 0 a všetky prvky sú záporné – žiadny nie je väčší ako 0, preto `m` zostane `0`."
            een = f"`m` starts at 0 and all elements are negative – none is greater than 0, so `m` stays `0`."
        else:
            esk = f"`m` si pamätá {'najväčšiu' if kind == 'max' else 'najmenšiu'} doteraz videnú hodnotu – na konci `{m}`."
            een = f"`m` keeps the {'largest' if kind == 'max' else 'smallest'} value seen so far – at the end `{m}`."
        return b.add("ar-max-min", 2, code=code, sk_body=val_q("m")[0], en_body=val_q("m")[1],
                     answers=[code_ans(m)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "value", "expr": "m"})
    fill(b, "ar-max-min", 25, max_min)

    CC = [("a[i] % 2 == 0", lambda x: x % 2 == 0), ("a[i] > {k}", None), ("a[i] == {k}", None), ("a[i] < 0", lambda x: x < 0), ("a[i] % 3 == 0", lambda x: x % 3 == 0)]
    def count_matches():
        n = R.randint(5, 7); a = [R.randint(-5, 12) for _ in range(n)]
        c, f = R.choice(CC)
        if f is None:
            k = R.choice(a) if "==" in c else R.randint(0, 8)
            c = c.format(k=k); f = (lambda x, k=k: x == k) if "==" in c else (lambda x, k=k: x > k)
        match = [x for x in a if f(x)]
        cnt = len(match)
        if cnt == 0:
            return False
        wrong = pick_wrong(cnt, [sum(match), cnt + 1, cnt - 1, n])
        code = f"{arr(a)}\nint pocet = 0;\nfor (int i = 0; i < a.Length; i++)\n{{\n    if ({c})\n        pocet = pocet + 1;\n}}"
        return b.add("ar-count-matches", 2, code=code, sk_body=val_q("pocet")[0], en_body=val_q("pocet")[1],
                     answers=[code_ans(cnt)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Podmienku `{c}` spĺňajú {', '.join(map(str, match))}, to je {cnt}.",
                     en_expl=f"{', '.join(map(str, match))} satisfy `{c}`, that's {cnt}.",
                     verify={"type": "value", "expr": "pocet"})
    fill(b, "ar-count-matches", 25, count_matches)

    def print_back():
        n = R.randint(4, 6); a = digits(n, 0, 9)
        if R.random() < 0.7:
            loop = "for (int i = a.Length - 1; i >= 0; i--)"; out = s(a[::-1]); idx = list(range(n - 1, -1, -1))
            wrong = pick_wrong(out, [s(a), s(a[::-1][:-1]), s(a[::-1][1:]), s(range(n - 1, -1, -1))])
        else:
            loop = "for (int i = a.Length - 1; i >= 0; i = i - 2)"; idx = list(range(n - 1, -1, -2)); out = s(a[i] for i in idx)
            wrong = pick_wrong(out, [s(a[::-1]), s(a[i] for i in range(n - 2, -1, -2)), s(a[i] for i in range(0, n, 2))])
        if not wrong:
            return False
        code = f"{arr(a)}\n{loop}\n    Console.Write(a[i]);"
        return b.add("ar-print-backwards", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Cyklus prechádza indexy {', '.join(map(str, idx))}.", en_expl=f"The loop goes through indexes {', '.join(map(str, idx))}.",
                     verify={"type": "output"})
    fill(b, "ar-print-backwards", 25, print_back)

    MOD = [("a[i] = a[i] * 2;", lambda x, i: x * 2), ("a[i] = a[i] + i;", lambda x, i: x + i), ("a[i] = a[i] - 1;", lambda x, i: x - 1), ("a[i] = i * i;", lambda x, i: i * i)]
    def modify_loop():
        n = R.randint(3, 5); a = digits(n, 1, 9); stmt, f = R.choice(MOD); k = R.randrange(n)
        new = [f(x, i) for i, x in enumerate(a)]
        v = new[k]
        wrong = pick_wrong(v, [a[k], new[(k + 1) % n], f(a[k], k + 1), v + 1])
        code = f"{arr(a)}\nfor (int i = 0; i < a.Length; i++)\n    {stmt}\nint v = a[{k}];"
        return b.add("ar-modify-loop", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Cyklus zmení každý prvok; `a[{k}]` bol {a[k]}, po `{stmt}` je `{v}`.",
                     en_expl=f"The loop changes every element; `a[{k}]` was {a[k]}, after `{stmt}` it's `{v}`.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ar-modify-loop", 25, modify_loop)

    def out_of_range():
        n = R.randint(3, 6); a = digits(n, 0, n - 1, distinct=False) if R.random() < 0.5 else digits(n, 0, 9)
        bad = R.choice(["int x = a[a.Length];", "int x = a[-1];", f"int x = a[{n}];", f"a[{n}] = 1;", "int x = a[a.Length + 1];"])
        valid_pool = ["int x = a[a.Length - 1];", "int x = a[0];", f"int x = a[{n - 1}];", f"a[{n - 2}] = 5;", "int x = a.Length;"]
        if all(0 <= v < n for v in a):
            valid_pool.append("int x = a[a[0]];")
        valid = R.sample(valid_pool, 3)
        sk, en = (f"Platné indexy sú 0 až {n - 1}; `{bad}` je mimo rozsahu → IndexOutOfRangeException.",
                  f"Valid indexes are 0 to {n - 1}; `{bad}` is out of range → IndexOutOfRangeException.")
        return b.add("ar-out-of-range", 2, code=arr(a), sk_body="{code}\nKtorý riadok spôsobí pád programu?", en_body="{code}\nWhich line makes the program crash?",
                     answers=[code_ans(bad)] + [code_ans(v) for v in valid], sk_expl=sk, en_expl=en,
                     verify={"type": "which-line", "expect": "exception"})
    fill(b, "ar-out-of-range", 25, out_of_range)

    def value_as_index():
        n = R.randint(4, 6); a = [R.randrange(n) for _ in range(n)]
        i = R.randrange(n); plus = R.random() < 0.3
        inner = a[i]; j = inner + (1 if plus else 0)
        if j >= n:
            return False
        v = a[j]
        expr = f"a[a[{i}] + 1]" if plus else f"a[a[{i}]]"
        wrong = pick_wrong(v, [inner, a[inner - 1] if inner > 0 else i, i, a[(j + 1) % n]])
        if not wrong:
            return False
        code = f"{arr(a)}\nint v = {expr};"
        return b.add("ar-value-as-index", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Najprv `a[{i}]` = {inner}, potom `a[{j}]` = {v}.", en_expl=f"First `a[{i}]` = {inner}, then `a[{j}]` = {v}.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ar-value-as-index", 25, value_as_index)

    AF = [("Sucet", ["int s = 0;", "for (int i = 0; i < pole.Length; i++)", "    s = s + pole[i];", "return s;"], lambda a: sum(a)),
          ("Najvacsi", ["int m = pole[0];", "for (int i = 1; i < pole.Length; i++)", "{", "    if (pole[i] > m)", "        m = pole[i];", "}", "return m;"], lambda a: max(a)),
          ("PocetParnych", ["int p = 0;", "for (int i = 0; i < pole.Length; i++)", "{", "    if (pole[i] % 2 == 0)", "        p = p + 1;", "}", "return p;"], lambda a: sum(1 for x in a if x % 2 == 0)),
          ("Posledny", ["return pole[pole.Length - 1];"], lambda a: a[-1])]
    def to_function():
        name, body, f = R.choice(AF); n = R.randint(3, 6); a = [R.randint(0, 15) for _ in range(n)]
        v = f(a)
        wrong = pick_wrong(v, [n, a[0], v + 1, sum(a) if name != "Sucet" else max(a)])
        bl = "\n".join("    " + l for l in body)
        code = f"{arr(a, 'cisla')}\nint v = {name}(cisla);\n\nint {name}(int[] pole)\n{{\n{bl}\n}}"
        return b.add("ar-to-function", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Funkcia `{name}` prejde pole `{{{', '.join(map(str, a))}}}` a vráti `{v}`.",
                     en_expl=f"The function `{name}` goes through `{{{', '.join(map(str, a))}}}` and returns `{v}`.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ar-to-function", 25, to_function)

    def average():
        n = R.randint(3, 5); a = [R.randint(1, 10) for _ in range(n)]
        tot = sum(a)
        if tot % n == 0:
            return False
        form = R.choice(["int", "double_bug", "cast"])
        exact = tot / n
        if form == "int":
            line = "int p = s / a.Length;"; correct = str(tot // n); name = "p"; exp = correct
        elif form == "double_bug":
            line = "double p = s / a.Length;"; correct = str(tot // n); name = "p"; exp = correct
        else:
            line = "double p = (double)s / a.Length;"; correct = fmt_double(exact); name = "p"; exp = correct
            if len(correct) > 8:
                return False
        cands = [fmt_double(exact) if len(fmt_double(exact)) <= 8 else str(round(exact, 2)), str(tot // n + 1), str(tot), str(tot // n)]
        wrong = pick_wrong(correct, cands)
        code = f"{arr(a)}\nint s = 0;\nfor (int i = 0; i < a.Length; i++)\n    s = s + a[i];\n{line}"
        if form == "cast":
            esk, een = f"`(double)s` zmení súčet na `double`, takže delenie {tot} / {n} je desatinné.", f"`(double)s` turns the sum into a `double`, so {tot} / {n} keeps the fraction."
        else:
            esk, een = (f"`s / a.Length` je delenie dvoch `int` – {tot} / {n} = {tot // n}, desatinná časť sa zahodí" + (" ešte pred uložením do `double`." if form == "double_bug" else "."),
                        f"`s / a.Length` divides two `int`s – {tot} / {n} = {tot // n}; the fraction is dropped" + (" before the result becomes a `double`." if form == "double_bug" else "."))
        return b.add("ar-average", 2, code=code, sk_body=val_q(name)[0], en_body=val_q(name)[1],
                     answers=[code_ans(correct)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "value", "expr": name, "expected": exp})
    fill(b, "ar-average", 25, average)

    def contains_flag():
        n = R.randint(3, 5); a = digits(n, 0, 12); bug = R.random() < 0.4
        x = R.choice(a) if R.random() < 0.65 else R.choice([v for v in range(13) if v not in a])
        if bug:
            v = a[-1] == x
            body = f"    if (a[i] == {x})\n        nasiel = true;\n    else\n        nasiel = false;"
            esk = "`else` prepíše `nasiel` pri každom ďalšom prvku – rozhoduje iba posledný prvok."
            een = "`else` overwrites `nasiel` for every later element – only the last element decides."
        else:
            v = x in a
            body = f"    if (a[i] == {x})\n        nasiel = true;"
            esk = f"Hodnota {x} v poli {'je' if v else 'nie je'}, preto `nasiel` je `{bstr(v)}`."
            een = f"The value {x} {'is' if v else 'is not'} in the array, so `nasiel` is `{bstr(v)}`."
        if bug and v == (x in a) and R.random() < 0.6:
            return False
        code = f"{arr(a)}\nbool nasiel = false;\nfor (int i = 0; i < a.Length; i++)\n{{\n{body}\n}}"
        return b.add("ar-contains-flag", 2, code=code, sk_body=val_q("nasiel")[0], en_body=val_q("nasiel")[1], answers=bool_answers(v),
                     sk_expl=esk, en_expl=een, verify={"type": "value", "expr": "nasiel", "expected": bstr(v)})
    fill(b, "ar-contains-flag", 25, contains_flag)

    def swap():
        n = R.randint(3, 5); a = digits(n, 1, 9); i, j = sorted(R.sample(range(n), 2)); bug = R.random() < 0.4
        good = a[:]; good[i], good[j] = good[j], good[i]
        bad = a[:]; bad[i] = bad[j]; bad[j] = bad[i]
        if bug:
            code = f"{arr(a)}\na[{i}] = a[{j}];\na[{j}] = a[{i}];\n{PRINT}"; out = s(bad)
            cands = [s(good), s(a), s(a[:i] + [a[i]] + a[i + 1:j] + [a[i]] + a[j + 1:])]
            esk = f"Bez pomocnej premennej sa pôvodná hodnota `a[{i}]` stratí – oba prvky budú {a[j]}."
            een = f"Without a helper variable the original `a[{i}]` is lost – both elements become {a[j]}."
        else:
            code = f"{arr(a)}\nint temp = a[{i}];\na[{i}] = a[{j}];\na[{j}] = temp;\n{PRINT}"; out = s(good)
            cands = [s(a), s(bad), s(a[::-1])]
            esk = f"Pomocná premenná `temp` si zapamätá `a[{i}]`, takže sa prvky na indexoch {i} a {j} vymenia."
            een = f"The helper `temp` remembers `a[{i}]`, so the elements at indexes {i} and {j} are swapped."
        wrong = pick_wrong(out, cands + [s(a[1:] + a[:1])])
        if not wrong:
            return False
        return b.add("ar-swap", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "output"})
    fill(b, "ar-swap", 25, swap)

    def loop_le_length():
        n = R.randint(2, 4); a = digits(n, 0, 9)
        form = R.choice(["le", "le", "lt", "from1"])
        if form == "le":
            loop = "for (int i = 0; i <= a.Length; i++)"
            sk, en = text_answers([(f"`{s(a)}` a potom pád (IndexOutOfRangeException)", f"`{s(a)}` then a crash (IndexOutOfRangeException)"),
                                   code_ans(s(a)), CRASH, code_ans(s(a[1:]))])
            esk, een = (f"Pri `i = {n}` platí `i <= a.Length`, ale `a[{n}]` neexistuje – najprv sa vypíše `{s(a)}`, potom program spadne.",
                        f"At `i = {n}`, `i <= a.Length` holds but `a[{n}]` doesn't exist – `{s(a)}` is printed first, then the program crashes.")
            verify = {"type": "exception", "name": "IndexOutOfRangeException", "stdout": s(a)}
        elif form == "lt":
            loop = "for (int i = 0; i < a.Length; i++)"
            sk, en = text_answers([code_ans(s(a)), (f"`{s(a)}` a potom pád (IndexOutOfRangeException)", f"`{s(a)}` then a crash (IndexOutOfRangeException)"), CRASH, code_ans(s(a[1:]))])
            esk, een = "`i < a.Length` zastaví cyklus pri poslednom platnom indexe – nič nespadne.", "`i < a.Length` stops the loop at the last valid index – nothing crashes."
            verify = {"type": "output"}
        else:
            loop = "for (int i = 1; i < a.Length; i++)"
            sk, en = text_answers([code_ans(s(a[1:])), code_ans(s(a)), CRASH, (f"`{s(a[1:])}` a potom pád (IndexOutOfRangeException)", f"`{s(a[1:])}` then a crash (IndexOutOfRangeException)")])
            esk, een = "Cyklus začína od indexu 1, takže prvý prvok sa vynechá.", "The loop starts at index 1, so the first element is skipped."
            verify = {"type": "output"}
        code = f"{arr(a)}\n{loop}\n    Console.Write(a[i]);"
        return b.add("ar-loop-le-length", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=esk, en_expl=een, verify=verify)
    fill(b, "ar-loop-le-length", 25, loop_le_length)

    def sort_reverse():
        n = R.randint(3, 5); a = digits(n, 0, 9)
        ops = R.choice([["Sort"], ["Reverse"], ["Sort", "Reverse"], ["Reverse", "Sort"]])
        cur = a[:]
        for op in ops:
            cur = sorted(cur) if op == "Sort" else cur[::-1]
        out = s(cur)
        wrong = pick_wrong(out, [s(a), s(sorted(a)), s(sorted(a, reverse=True)), s(a[::-1])])
        if not wrong:
            return False
        lines = "\n".join(f"Array.{op}(a);" for op in ops)
        code = f"{arr(a)}\n{lines}\n{PRINT}"
        trap_sk = " Pozor: `Array.Reverse` samo nezoradí – iba otočí aktuálne poradie." if ops == ["Reverse"] else ""
        trap_en = " Note: `Array.Reverse` alone doesn't sort – it only reverses the current order." if ops == ["Reverse"] else ""
        return b.add("ar-sort-reverse", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl="`Array.Sort` zoradí prvky vzostupne, `Array.Reverse` otočí aktuálne poradie." + trap_sk,
                     en_expl="`Array.Sort` sorts ascending; `Array.Reverse` reverses the current order." + trap_en,
                     verify={"type": "output"})
    fill(b, "ar-sort-reverse", 25, sort_reverse)

    def indexof():
        n = R.randint(4, 6); a = [R.randint(0, 9) for _ in range(n)]
        form = R.choice(["once", "dup", "missing"])
        if form == "missing":
            x = R.choice([v for v in range(10) if v not in a]); v = -1
        else:
            x = R.choice(a); v = a.index(x)
            if form == "dup" and a.count(x) < 2:
                j = R.choice([k for k in range(n) if k != v]); a[j] = x; v = a.index(x)
        last = n - 1 - a[::-1].index(x) if x in a else n
        wrong = pick_wrong(v, [last, v + 1, 0, x, n])
        code = f"{arr(a)}\nint v = Array.IndexOf(a, {x});"
        return b.add("ar-indexof", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl="`Array.IndexOf` vráti index prvého výskytu, a `-1`, keď hodnota v poli nie je." + (f" Hodnota {x} v poli nie je." if v == -1 else ""),
                     en_expl="`Array.IndexOf` returns the index of the first occurrence, or `-1` when the value isn't there." + (f" {x} isn't in the array." if v == -1 else ""),
                     verify={"type": "value", "expr": "v"})
    fill(b, "ar-indexof", 25, indexof)

    # =================================================================== HARD
    def reference_copy():
        n = R.randint(3, 5); a = digits(n, 1, 9); i = R.randrange(n); x = R.randint(10, 30)
        real_copy = R.random() < 0.33
        if real_copy:
            code = f"{arr(a)}\nint[] b = new int[a.Length];\nfor (int i = 0; i < a.Length; i++)\n    b[i] = a[i];\nb[{i}] = {x};\nint v = a[{i}];"
            v = a[i]; esk = "`b` je nové pole s kópiami prvkov – zmena `b` pole `a` nezmení."; een = "`b` is a new array with copies of the elements – changing `b` doesn't change `a`."
        else:
            code = f"{arr(a)}\nint[] b = a;\nb[{i}] = {x};\nint v = a[{i}];"
            v = x; esk = "`b = a` neskopíruje prvky – obe premenné ukazujú na to isté pole, takže zmena cez `b` je viditeľná aj v `a`."
            een = "`b = a` doesn't copy the elements – both variables point to the same array, so the change through `b` shows in `a` too."
        wrong = pick_wrong(v, [a[i] if v == x else x, a[(i + 1) % n], 0, x + a[i]])
        return b.add("ar-reference-copy", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "value", "expr": "v"})
    fill(b, "ar-reference-copy", 25, reference_copy)

    def function_modifies():
        x0 = R.randint(1, 9); p0 = R.randint(1, 9); k = R.randint(1, 5)
        op = R.choice(["+", "*"]) if k > 1 else "+"
        f = (lambda v: v + k) if op == "+" else (lambda v: v * k)
        code = (f"int x = {x0};\nint[] pole = {{{p0}}};\nZmenCislo(x);\nZmenPole(pole);\n\nvoid ZmenCislo(int c)\n{{\n    c = c {op} {k};\n}}\n\n"
                f"void ZmenPole(int[] p)\n{{\n    p[0] = p[0] {op} {k};\n}}")
        c = f"x = {x0}, pole[0] = {f(p0)}"
        wrong = pick_wrong(c, [f"x = {f(x0)}, pole[0] = {f(p0)}", f"x = {x0}, pole[0] = {p0}", f"x = {f(x0)}, pole[0] = {p0}"])
        if not wrong:
            return False
        return b.add("ar-function-modifies", 3, code=code,
                     sk_body="{code}\nAké hodnoty budú mať `x` a `pole[0]`?", en_body="{code}\nWhat values will `x` and `pole[0]` have?",
                     answers=[code_ans(c)] + [code_ans(w) for w in wrong],
                     sk_expl="`int` sa do funkcie skopíruje, pole nie – funkcia `ZmenPole` mení to isté pole, ktoré má hlavný program.",
                     en_expl="An `int` is copied into the function, an array isn't – `ZmenPole` changes the very array the main program has.",
                     verify={"type": "value", "expr": '$"x = {x}, pole[0] = {pole[0]}"'})
    fill(b, "ar-function-modifies", 25, function_modifies)

    def reverse_in_place():
        n = R.randint(3, 6); a = digits(n, 1, 9); bug = R.random() < 0.4
        lim = "a.Length" if bug else "a.Length / 2"
        out = s(a) if bug else s(a[::-1])
        half = a[:]
        for i in range(n // 2):
            half[i], half[n - 1 - i] = half[n - 1 - i], half[i]
        cands = [s(a[::-1]) if bug else s(a), s([a[-1]] + a[1:-1] + [a[0]]), s(a[n // 2:] + a[:n // 2])]
        wrong = pick_wrong(out, cands + [s(sorted(a))])
        if not wrong:
            return False
        code = (f"{arr(a)}\nfor (int i = 0; i < {lim}; i++)\n{{\n    int temp = a[i];\n    a[i] = a[a.Length - 1 - i];\n    a[a.Length - 1 - i] = temp;\n}}\n{PRINT}")
        esk = ("Cyklus ide cez celé pole, takže každú dvojicu vymení dvakrát – pole sa vráti do pôvodného stavu." if bug
               else "Cyklus vymení prvý s posledným, druhý s predposledným… až po stred – pole sa otočí.")
        een = ("The loop runs over the whole array, so every pair is swapped twice – the array ends up as it was." if bug
               else "The loop swaps the first with the last, the second with the second-to-last… up to the middle – the array is reversed.")
        return b.add("ar-reverse-in-place", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "output"})
    fill(b, "ar-reverse-in-place", 25, reverse_in_place)

    def shift():
        n = R.randint(3, 5); a = digits(n, 1, 9)
        form = R.choice(["left_wrap", "left_zero", "right_ok", "right_bug"])
        if form == "left_wrap":
            code_body = "int prvy = a[0];\nfor (int i = 0; i < a.Length - 1; i++)\n    a[i] = a[i + 1];\na[a.Length - 1] = prvy;"
            res = a[1:] + a[:1]; esk = "Prvky sa posunú doľava a prvý sa uloží na koniec."; een = "The elements move left and the first one goes to the end."
        elif form == "left_zero":
            code_body = "for (int i = 0; i < a.Length - 1; i++)\n    a[i] = a[i + 1];\na[a.Length - 1] = 0;"
            res = a[1:] + [0]; esk = "Prvky sa posunú doľava, na koniec sa zapíše 0."; een = "The elements move left and 0 is written at the end."
        elif form == "right_ok":
            code_body = "for (int i = a.Length - 1; i > 0; i--)\n    a[i] = a[i - 1];\na[0] = 0;"
            res = [0] + a[:-1]; esk = "Cyklus ide odzadu, preto sa každý prvok posunie doprava bez prepísania."; een = "The loop runs backwards, so every element moves right without being overwritten."
        else:
            code_body = "for (int i = 1; i < a.Length; i++)\n    a[i] = a[i - 1];"
            res = [a[0]] * n; esk = "Cyklus ide odpredu a vždy skopíruje už prepísaný prvok – všade skončí prvá hodnota."
            een = "The loop runs forwards and always copies an already overwritten element – the first value ends up everywhere."
        out = s(res)
        wrong = pick_wrong(out, [s([a[0]] + a[:-1]), s(a[1:] + a[:1]), s([0] + a[:-1]), s(a[1:] + [0]), s(a)])
        code = f"{arr(a)}\n{code_body}\n{PRINT}"
        return b.add("ar-shift", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "output"})
    fill(b, "ar-shift", 25, shift)

    def nested_pairs():
        n = R.randint(4, 6); a = [R.randint(0, 6) for _ in range(n)]
        form = R.choice(["eq", "sum", "gt"])
        if form == "eq":
            cond, f = "a[i] == a[j]", lambda x, y: x == y
        elif form == "sum":
            k = R.randint(4, 9); cond, f = f"a[i] + a[j] == {k}", (lambda x, y, k=k: x + y == k)
        else:
            cond, f = "a[i] > a[j]", lambda x, y: x > y
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if f(a[i], a[j])]
        cnt = len(pairs)
        if cnt == 0:
            return False
        all_pairs = sum(1 for i in range(n) for j in range(n) if f(a[i], a[j]))
        wrong = pick_wrong(cnt, [all_pairs, cnt + 1, cnt - 1, len(set(a))])
        code = f"{arr(a)}\nint pocet = 0;\nfor (int i = 0; i < a.Length; i++)\n    for (int j = i + 1; j < a.Length; j++)\n        if ({cond})\n            pocet = pocet + 1;"
        ps = ", ".join(f"({i}, {j})" for i, j in pairs)
        return b.add("ar-nested-pairs", 3, code=code, sk_body=val_q("pocet")[0], en_body=val_q("pocet")[1],
                     answers=[code_ans(cnt)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Dvojice indexov (i, j) s i < j, ktoré spĺňajú podmienku: {ps}.", en_expl=f"Index pairs (i, j) with i < j that satisfy the condition: {ps}.",
                     verify={"type": "value", "expr": "pocet"})
    fill(b, "ar-nested-pairs", 25, nested_pairs)

    NAMES = ["Eva", "Ján", "Ola", "Peter", "Zuzka", "Tomáš", "Mia", "Karol", "Lea"]
    def string_chars():
        names = R.sample(NAMES, R.randint(3, 4)); i = R.randrange(len(names)); w = names[i]
        if R.random() < 0.7:
            j = R.randrange(len(w)); c = w[j]
            code = f"string[] mena = {{{', '.join(chr(34) + x + chr(34) for x in names)}}};\nchar v = mena[{i}][{j}];"
            cands = [f"'{names[(i + 1) % len(names)][min(j, len(names[(i + 1) % len(names)]) - 1)]}'", f"'{w[j + 1]}'" if j + 1 < len(w) else f"'{w[j - 1]}'", f'"{c}"', f'"{w}"']
            wrong = pick_wrong(f"'{c}'", cands)
            if not wrong:
                return False
            return b.add("ar-string-chars", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                         answers=[code_ans(f"'{c}'")] + [code_ans(x) for x in wrong],
                         sk_expl=f"`mena[{i}]` je `\"{w}\"`, jeho znak na indexe {j} je `'{c}'`.", en_expl=f"`mena[{i}]` is `\"{w}\"`; its character at index {j} is `'{c}'`.",
                         verify={"type": "value", "expr": "v"})
        code = f"string[] mena = {{{', '.join(chr(34) + x + chr(34) for x in names)}}};\nint v = mena[{i}].Length;"
        wrong = pick_wrong(len(w), [len(names), len(w) - 1, len(w) + 1, i])
        return b.add("ar-string-chars", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(len(w))] + [code_ans(x) for x in wrong],
                     sk_expl=f"`mena[{i}]` je `\"{w}\"`, `.Length` je dĺžka tohto textu: {len(w)} (nie počet mien).",
                     en_expl=f"`mena[{i}]` is `\"{w}\"`; `.Length` is the length of that text: {len(w)} (not the number of names).",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ar-string-chars", 25, string_chars)

    def running_sum():
        n = R.randint(3, 5); a = digits(n, 1, 9)
        res = a[:]
        for i in range(1, n):
            res[i] = res[i] + res[i - 1]
        orig = [a[0]] + [a[i] + a[i - 1] for i in range(1, n)]
        out = sp(res)
        wrong = pick_wrong(out, [sp(orig), sp(a), sp(res[1:] + [res[-1]]), sp([sum(a)] * n)])
        if not wrong:
            return False
        code = f"{arr(a)}\nfor (int i = 1; i < a.Length; i++)\n    a[i] = a[i] + a[i - 1];\n{PRINT_SP}"
        steps = ", ".join(f"a[{i}] = {a[i]} + {res[i - 1]} = {res[i]}" for i in range(1, n))
        return b.add("ar-running-sum", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`a[i - 1]` už obsahuje nový súčet, preto: {steps}.", en_expl=f"`a[i - 1]` already holds the new sum, so: {steps}.",
                     verify={"type": "output"})
    fill(b, "ar-running-sum", 25, running_sum)

    def compare_eq():
        n = R.randint(2, 4); a = digits(n, 0, 9)
        form = R.choice(["sep", "sep", "ref", "elem"])
        if form == "sep":
            code = f"{arr(a)}\n{arr(a, 'b')}\nbool v = a == b;"; v = False
            esk, een = "`==` pri poliach porovnáva, či ide o to isté pole, nie či majú rovnaké prvky – sú to dve rôzne polia.", "`==` on arrays checks whether it's the same array, not whether the elements are equal – these are two different arrays."
        elif form == "ref":
            code = f"{arr(a)}\nint[] b = a;\nbool v = a == b;"; v = True
            esk, een = "`b = a` neskopíruje pole – `a` aj `b` ukazujú na to isté pole, preto `==` vráti `true`.", "`b = a` doesn't copy the array – `a` and `b` point to the same array, so `==` returns `true`."
        else:
            i = R.randrange(n); code = f"{arr(a)}\n{arr(a, 'b')}\nbool v = a[{i}] == b[{i}];"; v = True
            esk, een = f"Porovnávajú sa dve hodnoty typu `int` ({a[i]} a {a[i]}), nie polia.", f"Two `int` values are compared ({a[i]} and {a[i]}), not arrays."
        return b.add("ar-compare-eq", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1], answers=bool_answers(v),
                     sk_expl=esk, en_expl=een, verify={"type": "value", "expr": "v", "expected": bstr(v)})
    fill(b, "ar-compare-eq", 25, compare_eq)

    def index_of_max():
        n = R.randint(4, 6); a = [R.randint(1, 9) for _ in range(n)]
        m = max(a)
        if a.count(m) < 2 and R.random() < 0.6:
            j = R.choice([k for k in range(n) if a[k] != m]); a[j] = m
        ge = R.random() < 0.35
        idx = 0
        for i in range(1, n):
            if (a[i] >= a[idx]) if ge else (a[i] > a[idx]):
                idx = i
        first = a.index(m); last = n - 1 - a[::-1].index(m)
        wrong = pick_wrong(idx, [last if idx == first else first, m, idx + 1, n - 1])
        if not wrong:
            return False
        op = ">=" if ge else ">"
        code = f"{arr(a)}\nint idx = 0;\nfor (int i = 1; i < a.Length; i++)\n{{\n    if (a[i] {op} a[idx])\n        idx = i;\n}}"
        return b.add("ar-index-of-max", 3, code=code, sk_body=val_q("idx")[0], en_body=val_q("idx")[1],
                     answers=[code_ans(idx)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`idx` je index (nie hodnota) najväčšieho prvku; pri `{op}` vyhrá {'posledný' if ge else 'prvý'} z rovnakých maxím.",
                     en_expl=f"`idx` is the index (not the value) of the largest element; with `{op}` the {'last' if ge else 'first'} of equal maxima wins.",
                     verify={"type": "value", "expr": "idx"})
    fill(b, "ar-index-of-max", 25, index_of_max)

    def bubble_pass():
        n = R.randint(4, 5); a = digits(n, 1, 9)
        res = a[:]
        for i in range(n - 1):
            if res[i] > res[i + 1]:
                res[i], res[i + 1] = res[i + 1], res[i]
        if res == sorted(a) and R.random() < 0.7:
            return False
        first = a[:]
        if first[0] > first[1]:
            first[0], first[1] = first[1], first[0]
        wrong = pick_wrong(s(res), [s(sorted(a)), s(a), s(first), s(sorted(a, reverse=True))])
        if not wrong:
            return False
        code = (f"{arr(a)}\nfor (int i = 0; i < a.Length - 1; i++)\n{{\n    if (a[i] > a[i + 1])\n    {{\n        int temp = a[i];\n        a[i] = a[i + 1];\n        a[i + 1] = temp;\n    }}\n}}\n{PRINT}")
        return b.add("ar-bubble-pass", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(s(res))] + [code_ans(w) for w in wrong],
                     sk_expl="Jeden prechod porovná susedov zľava doprava a posunie najväčší prvok na koniec – zvyšok ešte nemusí byť zoradený.",
                     en_expl="One pass compares neighbours from left to right and moves the largest element to the end – the rest may not be sorted yet.",
                     verify={"type": "output"})
    fill(b, "ar-bubble-pass", 25, bubble_pass)

    def filter_copy():
        n = R.randint(4, 5); a = digits(n, 0, 9); k = R.randint(2, 7)
        form = R.choice(["k_all", "k_all", "i_bug"])
        keep = [x for x in a if x > k]
        if not keep or len(keep) == n:
            return False
        if form == "k_all":
            bb = keep + [0] * (n - len(keep)); idx = "k"
            esk, een = "`k` počíta zapísané prvky; zvyšok `b` ostane 0.", "`k` counts the written elements; the rest of `b` stays 0."
        else:
            bb = [x if x > k else 0 for x in a]; idx = "i"
            esk, een = "Zapisuje sa na index `i`, nie `k` – vybrané prvky zostanú na pôvodných miestach a medzi nimi sú nuly.", "It writes to index `i`, not `k` – the chosen elements stay in their original places with zeros between them."
        out = s(bb)
        other = s([x if x > k else 0 for x in a]) if form == "k_all" else s(keep + [0] * (n - len(keep)))
        wrong = pick_wrong(out, [s(keep), other, s(a), s([x for x in a if x <= k])])
        if not wrong:
            return False
        code = (f"{arr(a)}\nint[] b = new int[a.Length];\nint k = 0;\nfor (int i = 0; i < a.Length; i++)\n{{\n    if (a[i] > {k})\n    {{\n        b[{idx}] = a[i];\n        k = k + 1;\n    }}\n}}\n"
                f"for (int i = 0; i < b.Length; i++)\n    Console.Write(b[i]);")
        return b.add("ar-filter-copy", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "output"})
    fill(b, "ar-filter-copy", 25, filter_copy)

    def methods_reference():
        n = R.randint(3, 5); a = digits(n, 0, 9)
        shared = R.random() < 0.65; op = R.choice(["Sort", "Reverse"])
        changed = sorted(a) if op == "Sort" else a[::-1]
        if shared:
            code = f"{arr(a)}\nint[] b = a;\nArray.{op}(b);\n{PRINT}"; out = s(changed)
            esk, een = f"`b` ukazuje na to isté pole ako `a`, takže `Array.{op}(b)` zmení aj `a`.", f"`b` points to the same array as `a`, so `Array.{op}(b)` changes `a` too."
        else:
            code = f"{arr(a)}\nint[] b = new int[a.Length];\nfor (int i = 0; i < a.Length; i++)\n    b[i] = a[i];\nArray.{op}(b);\n{PRINT}"; out = s(a)
            esk, een = f"`b` je samostatná kópia – `Array.{op}(b)` pole `a` nezmení.", f"`b` is a separate copy – `Array.{op}(b)` doesn't change `a`."
        wrong = pick_wrong(out, [s(changed) if not shared else s(a), s(a[::-1] if op == "Sort" else sorted(a)), s(sorted(a, reverse=True)), s(a[1:] + a[:1])])
        if not wrong:
            return False
        return b.add("ar-methods-reference", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "output"})
    fill(b, "ar-methods-reference", 25, methods_reference)

    def trace():
        n = R.randint(3, 5)
        form = R.choice(["next_double", "even_odd", "idx"])
        if form == "next_double":
            a = digits(n, 1, 5)
            loop = "for (int i = 0; i < a.Length - 1; i++)\n    a[i + 1] = a[i] * 2;"
            res = a[:]
            for i in range(n - 1):
                res[i + 1] = res[i] * 2
            naive = [a[0]] + [a[i] * 2 for i in range(n - 1)]
        elif form == "even_odd":
            a = digits(n, 1, 9)
            loop = "for (int i = 1; i < a.Length; i++)\n{\n    if (a[i] % 2 == 0)\n        a[i] = a[i] / 2;\n    else\n        a[i] = a[i] + a[i - 1];\n}"
            res = a[:]
            for i in range(1, n):
                res[i] = res[i] // 2 if res[i] % 2 == 0 else res[i] + res[i - 1]
            naive = [a[0]] + [a[i] // 2 if a[i] % 2 == 0 else a[i] + a[i - 1] for i in range(1, n)]
        else:
            a = [R.randrange(n) for _ in range(n)]
            loop = "for (int i = 0; i < a.Length; i++)\n    a[i] = a[a[i]];"
            res = a[:]
            for i in range(n):
                res[i] = res[res[i]]
            naive = [a[a[i]] for i in range(n)]
        if res == naive and R.random() < 0.8:
            return False
        out = sp(res)
        wrong = pick_wrong(out, [sp(naive), sp(a), sp(res[::-1]), sp([x + 1 for x in res])])
        if not wrong:
            return False
        code = f"{arr(a)}\n{loop}\n{PRINT_SP}"
        return b.add("ar-trace", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Cyklus číta prvky, ktoré už mohol zmeniť: z `{{{', '.join(map(str, a))}}}` vznikne `{{{', '.join(map(str, res))}}}`.",
                     en_expl=f"The loop reads elements it may already have changed: `{{{', '.join(map(str, a))}}}` becomes `{{{', '.join(map(str, res))}}}`.",
                     verify={"type": "output"})
    fill(b, "ar-trace", 25, trace)
    return b


if __name__ == "__main__":
    main().write()
