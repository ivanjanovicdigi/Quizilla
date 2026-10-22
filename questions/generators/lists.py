"""Generator for topic lists (36 templates × 25). List<int> / List<string>, no foreach, no lambdas, no LINQ."""
import random
from common import Batch, fill, code_ans, pick_wrong

R = random.Random(20261027)
DATE = "2026-10-22"
OUT_Q = ("{code}\nČo vypíše tento kód?", "{code}\nWhat does this code print?")
CRASH = ("Program spadne (ArgumentOutOfRangeException)", "The program crashes (ArgumentOutOfRangeException)")
PRINT = "for (int i = 0; i < z.Count; i++)\n    Console.Write(z[i]);"


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


def lst(vals, name="z", t="int"):
    return f"List<{t}> {name} = new List<{t}> {{ {', '.join(map(str, vals))} }};"


def s(vals):
    return "".join(map(str, vals))


def dig(n, lo=0, hi=9, distinct=True):
    return R.sample(range(lo, hi + 1), n) if distinct else [R.randint(lo, hi) for _ in range(n)]


def main():
    b = Batch(f"{DATE}_lists", "lists", DATE)

    # =================================================================== EASY
    def count_after_add():
        n = R.randint(1, 5); vals = [R.randint(0, 9) for _ in range(n)]
        start = R.choice([0, 0, 2]); init = dig(start) if start else []
        code = (lst(init) if init else "List<int> z = new List<int>();") + "\n" + "\n".join(f"z.Add({v});" for v in vals) + "\nint v = z.Count;"
        cnt = start + n
        wrong = pick_wrong(cnt, [cnt - 1, n if start else cnt + 1, vals[-1], 0])
        return b.add("ls-count-after-add", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(cnt)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Každé `Add` pridá jeden prvok – v zozname je {cnt} prvkov" + (f" ({start} na začiatku + {n} pridané)." if start else "."),
                     en_expl=f"Each `Add` adds one element – the list has {cnt} elements" + (f" ({start} at the start + {n} added)." if start else "."),
                     verify={"type": "value", "expr": "v"})
    fill(b, "ls-count-after-add", 25, count_after_add)

    def index_value():
        n = R.randint(3, 5); vals = dig(n, 0, 20); i = R.randrange(n)
        if R.random() < 0.5:
            code = "List<int> z = new List<int>();\n" + "\n".join(f"z.Add({v});" for v in vals) + f"\nint v = z[{i}];"
        else:
            code = f"{lst(vals)}\nint v = z[{i}];"
        v = vals[i]
        wrong = pick_wrong(v, ([vals[i - 1]] if i else []) + ([vals[i + 1]] if i + 1 < n else []) + [i, vals[-1]])
        return b.add("ls-index-value", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Indexy v zozname začínajú od `0` rovnako ako v poli – `z[{i}]` je {i + 1}. prvok.",
                     en_expl=f"List indexes start at `0`, just like in an array – `z[{i}]` is element number {i + 1}.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ls-index-value", 25, index_value)

    GOOD = ["List<int> z = new List<int>();", "List<int> z = new List<int> { 1, 2 };", "List<string> m = new List<string>();",
            'List<string> m = new List<string> { "Eva", "Ján" };', "List<double> d = new List<double>();", "List<int> cisla = new List<int> { 7 };"]
    BAD = ["List z = new List();", "List<int> z = new List<int>;", "List<int> z = new List<int>[3];", "List<int> z = new int[3];", "int<List> z = new int<List>();",
           "List<int> z = List<int>();", "List[int] z = new List[int]();", 'List<int> z = new List<int> { "1" };']
    def creation():
        good = R.choice(GOOD); wrong = R.sample(BAD, 3)
        return b.add("ls-creation", 1, code=None, sk_body="Ktorý riadok správne vytvorí zoznam?", en_body="Which line correctly creates a list?",
                     answers=[code_ans(good)] + [code_ans(w) for w in wrong],
                     sk_expl="Zoznam sa vytvára ako `new List<typ>()` – so zátvorkami a typom v `< >`; hodnoty môžu byť hneď v `{ … }`.",
                     en_expl="A list is created with `new List<type>()` – with brackets and the type in `< >`; values may follow in `{ … }`.",
                     verify={"type": "which-line", "expect": "compile-error", "invert": True})
    fill(b, "ls-creation", 25, creation)

    def add_order():
        n = R.randint(3, 5); vals = dig(n)
        code = "List<int> z = new List<int>();\n" + "\n".join(f"z.Add({v});" for v in vals) + "\n" + PRINT
        out = s(vals)
        wrong = pick_wrong(out, [s(vals[::-1]), s(sorted(vals)), s(vals[:-1]), s(vals[1:])])
        return b.add("ls-add-order", 1, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl="`Add` vždy pridá prvok na koniec zoznamu, takže poradie zostane také, v akom sme pridávali.",
                     en_expl="`Add` always appends to the end of the list, so the order stays the order of adding.",
                     verify={"type": "output"})
    fill(b, "ls-add-order", 25, add_order)

    M = {
        "Add": ("pridá prvok na koniec zoznamu", "adds an element to the end of the list"),
        "Remove": ("odstráni prvý výskyt danej hodnoty", "removes the first occurrence of a value"),
        "RemoveAt": ("odstráni prvok na danom indexe", "removes the element at an index"),
        "Insert": ("vloží prvok na daný index", "inserts an element at an index"),
        "Count": ("počet prvkov zoznamu", "the number of elements in the list"),
        "Contains": ("zistí, či zoznam obsahuje hodnotu", "checks whether the list contains a value"),
        "IndexOf": ("vráti index prvého výskytu hodnoty alebo -1", "returns the index of the first occurrence of a value, or -1"),
        "Clear": ("odstráni všetky prvky", "removes all elements"),
        "Sort": ("zoradí prvky vzostupne", "sorts the elements in ascending order"),
        "Reverse": ("otočí poradie prvkov", "reverses the order of the elements"),
    }
    LOOK = {"Add": ["Insert", "Count"], "Remove": ["RemoveAt", "Clear"], "RemoveAt": ["Remove", "Clear"], "Insert": ["Add", "IndexOf"], "Count": ["IndexOf", "Contains"],
            "Contains": ["IndexOf", "Count"], "IndexOf": ["Contains", "Insert"], "Clear": ["Remove", "RemoveAt"], "Sort": ["Reverse", "Insert"], "Reverse": ["Sort", "Remove"]}
    FAKE = [("odstráni posledný prvok", "removes the last element"), ("vytvorí kópiu zoznamu", "creates a copy of the list"), ("zoradí prvky zostupne", "sorts the elements descending")]
    TQ = [("Čo robí `z.{m}`?", "What does `z.{m}` do?"), ("Na čo slúži `{m}` pri zozname?", "What is `{m}` for in a list?")]
    def term_purpose():
        m = R.choice(list(M)); q = R.choice(TQ)
        looks = [M[x] for x in LOOK[m]]
        other = R.choice([M[x] for x in M if x != m and x not in LOOK[m]] + FAKE)
        sk, en = text_answers([M[m]] + looks + [other])
        return b.add("ls-term-purpose", 1, code=None, sk_body=q[0].format(m=m), en_body=q[1].format(m=m), answers=sk, en_answers=en,
                     sk_expl=f"`{m}`: {M[m][0]}.", en_expl=f"`{m}`: {M[m][1]}.", verify={"type": "none"})
    fill(b, "ls-term-purpose", 25, term_purpose)

    PQ = [("Ktorá metóda {d}?", "Which method {d}?"), ("Čo použijeme, keď chceme, aby sa {d2}?", "What do we use when we want to {d3}?")]
    def purpose_term():
        m = R.choice(list(M)); d_sk, d_en = M[m]
        wrong = LOOK[m] + [R.choice([x for x in M if x != m and x not in LOOK[m]])]
        if R.random() < 0.5 or m == "Count":
            sq, eq = f"Ktorý člen zoznamu {d_sk.replace('počet', 'vráti počet')}?" if m == "Count" else f"Ktorá metóda {d_sk}?", f"Which member {'gives ' + d_en if m == 'Count' else d_en}?"
        else:
            sq, eq = f"Ako sa volá metóda zoznamu, ktorá {d_sk}?", f"What is the name of the list method that {d_en}?"
        return b.add("ls-purpose-term", 1, code=None, sk_body=sq, en_body=eq,
                     answers=[code_ans(m)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`{m}`: {d_sk}.", en_expl=f"`{m}`: {d_en}.", verify={"type": "none"})
    fill(b, "ls-purpose-term", 25, purpose_term)

    CVL = [("Ako zistíme počet prvkov zoznamu `{n}`?", "How do we get the number of elements of the list `{n}`?", "`{n}.Count`", ["`{n}.Length`", "`{n}.Size`", "`{n}.Size()`", "`{n}.Length()`"]),
           ("Ako zistíme počet prvkov poľa `{n}`?", "How do we get the number of elements of the array `{n}`?", "`{n}.Length`", ["`{n}.Count`", "`{n}.Size`", "`{n}.Length()`"]),
           ("Ktorý index má posledný prvok zoznamu `{n}`?", "What is the index of the last element of the list `{n}`?", "`{n}.Count - 1`", ["`{n}.Count`", "`{n}.Length - 1`", "`-1`"])]
    def count_vs_length():
        sq, eq, good, bads = R.choice(CVL); n = R.choice(["z", "zoznam", "cisla", "mena", "body", "a"])
        wrong = R.sample(bads, 3)
        f = lambda x: x.replace("{n}", n)
        return b.add("ls-count-vs-length", 1, code=None, sk_body=f(sq), en_body=f(eq),
                     answers=[f(good)] + [f(w) for w in wrong],
                     sk_expl="Pole má `Length`, zoznam má `Count` (bez zátvoriek).", en_expl="An array has `Length`, a list has `Count` (no brackets).",
                     verify={"type": "none"})
    fill(b, "ls-count-vs-length", 25, count_vs_length)

    def contains():
        n = R.randint(3, 5); vals = dig(n, 0, 12)
        form = R.choice(["in", "out", "index"])
        if form == "in":
            x = R.choice(vals); v = True; why = (f"hodnota {x} v zozname je", f"{x} is in the list")
        elif form == "out":
            x = R.choice([k for k in range(13) if k not in vals]); v = False; why = (f"hodnota {x} v zozname nie je", f"{x} isn't in the list")
        else:
            cand = [k for k in range(n) if k not in vals]
            if not cand:
                return False
            x = R.choice(cand); v = False; why = (f"{x} je síce platný index, ale taká hodnota v zozname nie je", f"{x} is a valid index, but no element has that value")
        code = f"{lst(vals)}\nbool v = z.Contains({x});"
        return b.add("ls-contains", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1], answers=bool_answers(v),
                     sk_expl=f"`Contains` hľadá hodnotu, nie index – {why[0]}.", en_expl=f"`Contains` looks for a value, not an index – {why[1]}.",
                     verify={"type": "value", "expr": "v", "expected": bstr(v)})
    fill(b, "ls-contains", 25, contains)

    def clear():
        n = R.randint(2, 5); vals = dig(n); add = R.choice([0, 0, 1, 2])
        code = f"{lst(vals)}\nz.Clear();" + "".join(f"\nz.Add({R.randint(0, 9)});" for _ in range(add)) + "\nint v = z.Count;"
        wrong = pick_wrong(add, [n, n + add, 1 if add != 1 else 0, -1])
        return b.add("ls-clear", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(add)] + [code_ans(w) for w in wrong],
                     sk_expl="`Clear` odstráni všetky prvky" + (f"; potom sa pridali {add}." if add else "."),
                     en_expl="`Clear` removes all elements" + (f"; then {add} were added." if add else "."),
                     verify={"type": "value", "expr": "v"})
    fill(b, "ls-clear", 25, clear)

    def new_empty():
        n = R.randint(2, 9); t = R.choice(["int", "string", "double"])
        if R.random() < 0.65:
            code = f"List<{t}> z = new List<{t}>();\nint v = z.Count;"; v = 0
            esk, een = "Nový zoznam je prázdny – má 0 prvkov.", "A new list is empty – it has 0 elements."
        else:
            code = f"{t}[] a = new {t}[{n}];\nint v = a.Length;"; v = n
            esk, een = f"`new {t}[{n}]` má hneď {n} prvkov (s predvolenými hodnotami) – na rozdiel od nového zoznamu.", f"`new {t}[{n}]` has {n} elements right away (default values) – unlike a new list."
        wrong = pick_wrong(v, [n if v == 0 else 0, 1, -1, n - 1])
        return b.add("ls-new-empty", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "value", "expr": "v"})
    fill(b, "ls-new-empty", 25, new_empty)

    def loop_print():
        n = R.randint(3, 5); vals = dig(n)
        back = R.random() < 0.35
        loop = "for (int i = z.Count - 1; i >= 0; i--)" if back else "for (int i = 0; i < z.Count; i++)"
        out = s(vals[::-1] if back else vals)
        wrong = pick_wrong(out, [s(vals if back else vals[::-1]), s(range(n)), s(vals[:-1]), s(vals[1:])])
        code = f"{lst(vals)}\n{loop}\n    Console.Write(z[i]);"
        return b.add("ls-loop-print", 1, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl="Cyklus prejde indexy 0 až `Count - 1`" + (" odzadu" if back else "") + " a vypíše hodnoty `z[i]`.",
                     en_expl="The loop goes through indexes 0 to `Count - 1`" + (" backwards" if back else "") + " and prints the values `z[i]`.",
                     verify={"type": "output"})
    fill(b, "ls-loop-print", 25, loop_print)

    NAMES = ["Eva", "Ján", "Ola", "Peter", "Zuzka", "Tomáš", "Mia", "Karol", "Lea", "Adam"]
    def string_list():
        names = R.sample(NAMES, R.randint(3, 5)); code0 = f"List<string> mena = new List<string> {{ {', '.join(chr(34) + x + chr(34) for x in names)} }};"
        if R.random() < 0.7:
            i = R.randrange(len(names)); w = names[i]
            ans = [f'"{w}"', f'"{names[i - 1]}"' if i else f'"{names[i + 1]}"', w, "`string`"]
            ans = [code_ans(a) if a != "`string`" else a for a in ans]
            code = f"{code0}\nstring v = mena[{i}];"
            return b.add("ls-string-list", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1], answers=ans,
                         sk_expl=f"`mena[{i}]` je {i + 1}. meno v zozname: `\"{w}\"`.", en_expl=f"`mena[{i}]` is name number {i + 1} in the list: `\"{w}\"`.",
                         verify={"type": "value", "expr": "v"})
        n = len(names); code = f"{code0}\nint v = mena.Count;"
        wrong = pick_wrong(n, [n - 1, n + 1, len(names[0])])
        return b.add("ls-string-list", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(n)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`Count` je počet prvkov – v zozname je {n} mien.", en_expl=f"`Count` is the number of elements – the list has {n} names.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ls-string-list", 25, string_list)

    # =================================================================== MEDIUM
    def remove_value():
        n = R.randint(4, 5); vals = [R.randint(1, 6) for _ in range(n)]
        x = R.choice(vals)
        if vals.count(x) < 2 and R.random() < 0.7:
            j = R.choice([k for k in range(n) if vals[k] != x]); vals[j] = x
        res = vals[:]; res.remove(x)
        all_rm = [v for v in vals if v != x]
        last_rm = vals[:]; del last_rm[n - 1 - vals[::-1].index(x)]
        idx_rm = vals[:x] + vals[x + 1:] if x < n else None
        out = s(res)
        wrong = pick_wrong(out, [s(all_rm), s(last_rm), s(idx_rm) if idx_rm else None, s(vals)])
        if not wrong or None in wrong:
            wrong = pick_wrong(out, [c for c in [s(all_rm), s(last_rm), s(idx_rm) if idx_rm else None, s(vals), s(res[::-1])] if c])
        if not wrong:
            return False
        code = f"{lst(vals)}\nz.Remove({x});\n{PRINT}"
        return b.add("ls-remove-value", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`Remove({x})` odstráni iba prvý výskyt hodnoty {x}" + (" (nie prvok na indexe " + str(x) + ")." if x < n else "."),
                     en_expl=f"`Remove({x})` removes only the first occurrence of {x}" + (" (not the element at index " + str(x) + ")." if x < n else "."),
                     verify={"type": "output"})
    fill(b, "ls-remove-value", 25, remove_value)

    def removeat():
        n = R.randint(4, 6); vals = dig(n, 0, 20); i = R.randrange(n - 1)
        res = vals[:]; del res[i]
        if R.random() < 0.7:
            code = f"{lst(vals)}\nz.RemoveAt({i});\nint v = z[{i}];"; v = res[i]
            wrong = pick_wrong(v, [vals[i], res[i + 1] if i + 1 < len(res) else vals[0], i])
            esk, een = f"Po `RemoveAt({i})` sa prvky za ním posunú o jedno dopredu – na index {i} sa dostane {v}.", f"After `RemoveAt({i})` the elements behind it move forward – {v} moves to index {i}."
        else:
            code = f"{lst(vals)}\nz.RemoveAt({i});\nint v = z.Count;"; v = n - 1
            wrong = pick_wrong(v, [n, n - 2, vals[i]])
            esk, een = f"`RemoveAt` odstráni jeden prvok, zostane {v}.", f"`RemoveAt` removes one element; {v} remain."
        if not wrong:
            return False
        return b.add("ls-removeat", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "value", "expr": "v"})
    fill(b, "ls-removeat", 25, removeat)

    def insert():
        n = R.randint(3, 4); vals = dig(n, 1, 8); i = R.choice(list(range(0, n + 1))); x = 9 if 9 not in vals else 0
        res = vals[:]; res.insert(i, x)
        replace = vals[:]
        if i < n:
            replace[i] = x
        out = s(res)
        wrong = pick_wrong(out, [s(replace) if i < n else s([x] + vals), s(vals[:i + 1] + [x] + vals[i + 1:]), s(vals + [x]), s([x] + vals)])
        if not wrong:
            return False
        code = f"{lst(vals)}\nz.Insert({i}, {x});\n{PRINT}"
        return b.add("ls-insert", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`Insert({i}, {x})` vloží {x} na index {i} a ostatné prvky posunie dozadu – nič neprepíše.",
                     en_expl=f"`Insert({i}, {x})` puts {x} at index {i} and shifts the rest back – nothing is overwritten.",
                     verify={"type": "output"})
    fill(b, "ls-insert", 25, insert)

    def remove_vs_removeat():
        n = R.randint(4, 5); vals = [R.randint(0, n - 1) for _ in range(n)]
        k = R.randrange(n); method = R.choice(["Remove", "RemoveAt"])
        if method == "Remove" and k not in vals:
            return False
        a = vals[:]; a.remove(k) if k in vals else None
        b_ = vals[:]; del b_[k]
        res = a if method == "Remove" else b_
        other = b_ if method == "Remove" else a
        if res == other:
            return False
        out = s(res)
        wrong = pick_wrong(out, [s(other), s([v for v in vals if v != k]), s(vals)])
        if not wrong:
            return False
        code = f"{lst(vals)}\nz.{method}({k});\n{PRINT}"
        return b.add("ls-remove-vs-removeat", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`Remove({k})` hľadá hodnotu {k}, `RemoveAt({k})` odstráni prvok na indexe {k}. Tu je použité `{method}`.",
                     en_expl=f"`Remove({k})` looks for the value {k}; `RemoveAt({k})` removes the element at index {k}. Here it's `{method}`.",
                     verify={"type": "output"})
    fill(b, "ls-remove-vs-removeat", 25, remove_vs_removeat)

    def ops_sequence():
        vals = dig(R.randint(2, 3), 1, 5); cur = vals[:]; lines, steps = [], []
        for _ in range(R.randint(3, 4)):
            op = R.choice(["Add", "Insert", "Remove", "RemoveAt"])
            if op == "Add":
                x = R.randint(6, 9); cur.append(x); lines.append(f"z.Add({x});")
            elif op == "Insert":
                i = R.randint(0, len(cur)); x = R.randint(6, 9); cur.insert(i, x); lines.append(f"z.Insert({i}, {x});")
            elif op == "Remove":
                if not cur:
                    return False
                x = R.choice(cur); cur.remove(x); lines.append(f"z.Remove({x});")
            else:
                if not cur:
                    return False
                i = R.randrange(len(cur)); del cur[i]; lines.append(f"z.RemoveAt({i});")
            steps.append("{" + ", ".join(map(str, cur)) + "}")
        if not cur:
            return False
        out = s(cur)
        before_last = steps[-2].strip("{}").replace(", ", "")
        wrong = pick_wrong(out, [before_last, s(cur[::-1]), s(sorted(cur)), s(cur[:-1]), s(vals)])
        if not wrong:
            return False
        code = f"{lst(vals)}\n" + "\n".join(lines) + f"\n{PRINT}"
        return b.add("ls-ops-sequence", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Po krokoch: {' → '.join(steps)}.", en_expl=f"Step by step: {' → '.join(steps)}.",
                     verify={"type": "output"})
    fill(b, "ls-ops-sequence", 25, ops_sequence)

    def sum_max():
        n = R.randint(4, 6); vals = [R.randint(-8, 15) for _ in range(n)]; kind = R.choice(["sum", "max", "min"])
        if kind == "sum":
            v = sum(vals); code = f"{lst(vals)}\nint v = 0;\nfor (int i = 0; i < z.Count; i++)\n    v = v + z[i];"
            wrong = pick_wrong(v, [v - vals[0], v - vals[-1], n, max(vals)])
            esk, een = f"Súčet všetkých prvkov je {v}.", f"The sum of all elements is {v}."
        else:
            op = ">" if kind == "max" else "<"; v = max(vals) if kind == "max" else min(vals)
            code = f"{lst(vals)}\nint v = z[0];\nfor (int i = 1; i < z.Count; i++)\n{{\n    if (z[i] {op} v)\n        v = z[i];\n}}"
            wrong = pick_wrong(v, [min(vals) if kind == "max" else max(vals), vals[0], vals[-1], sum(vals)])
            esk, een = f"`v` si pamätá {'najväčší' if kind == 'max' else 'najmenší'} doteraz videný prvok – na konci {v}.", f"`v` keeps the {'largest' if kind == 'max' else 'smallest'} element seen so far – at the end {v}."
        if not wrong:
            return False
        return b.add("ls-sum-max", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "value", "expr": "v"})
    fill(b, "ls-sum-max", 25, sum_max)

    def indexof():
        n = R.randint(4, 6); vals = [R.randint(0, 9) for _ in range(n)]; form = R.choice(["once", "dup", "missing", "shift"])
        extra = ""
        if form == "missing":
            x = R.choice([k for k in range(10) if k not in vals]); v = -1
        else:
            x = R.choice(vals)
            if form == "dup" and vals.count(x) < 2:
                j = R.choice([k for k in range(n) if vals[k] != x]); vals[j] = x
            cur = vals[:]
            if form == "shift":
                y = R.choice([k for k in range(10, 20)]); cur.insert(0, y); extra = f"\nz.Insert(0, {y});"
            v = cur.index(x)
        last = n - 1 - vals[::-1].index(x) if x in vals else n
        wrong = pick_wrong(v, [vals.index(x) if x in vals and form == "shift" else last, v + 1, 0, x])
        if not wrong:
            return False
        code = f"{lst(vals)}{extra}\nint v = z.IndexOf({x});"
        return b.add("ls-indexof", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl="`IndexOf` vráti index prvého výskytu, alebo `-1`." + (" `Insert(0, …)` posunul všetky prvky o jedno dozadu." if form == "shift" else ""),
                     en_expl="`IndexOf` returns the index of the first occurrence, or `-1`." + (" `Insert(0, …)` moved every element one place back." if form == "shift" else ""),
                     verify={"type": "value", "expr": "v"})
    fill(b, "ls-indexof", 25, indexof)

    FC = [("a[i] % 2 == 0", lambda x: x % 2 == 0), ("a[i] > {k}", None), ("a[i] < {k}", None), ("a[i] % 3 == 0", lambda x: x % 3 == 0)]
    def filter_new():
        n = R.randint(5, 7); vals = [R.randint(0, 12) for _ in range(n)]
        c, f = R.choice(FC)
        if f is None:
            k = R.randint(3, 9); c = c.format(k=k); f = (lambda x, k=k: x > k) if ">" in c else (lambda x, k=k: x < k)
        keep = [x for x in vals if f(x)]
        if not keep:
            return False
        ask_count = R.random() < 0.6
        code = f"{lst(vals, 'a')}\nList<int> b = new List<int>();\nfor (int i = 0; i < a.Count; i++)\n{{\n    if ({c})\n        b.Add(a[i]);\n}}\n"
        if ask_count:
            code += "int v = b.Count;"; v = len(keep); wrong = pick_wrong(v, [n, v + 1, v - 1, sum(keep)])
        else:
            k2 = R.randrange(len(keep)); code += f"int v = b[{k2}];"; v = keep[k2]; wrong = pick_wrong(v, [vals[k2], k2, keep[(k2 + 1) % len(keep)] if len(keep) > 1 else v + 1, v + 1])
        if not wrong:
            return False
        return b.add("ls-filter-new", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Do `b` sa pridajú iba prvky, pre ktoré platí `{c}`: {', '.join(map(str, keep))}.",
                     en_expl=f"Only elements for which `{c}` holds are added to `b`: {', '.join(map(str, keep))}.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ls-filter-new", 25, filter_new)

    def sort_reverse():
        n = R.randint(3, 5); vals = dig(n)
        ops = R.choice([["Sort"], ["Reverse"], ["Sort", "Reverse"], ["Reverse", "Sort"]])
        cur = vals[:]
        for op in ops:
            cur = sorted(cur) if op == "Sort" else cur[::-1]
        out = s(cur)
        wrong = pick_wrong(out, [s(vals), s(sorted(vals)), s(sorted(vals, reverse=True)), s(vals[::-1])])
        if not wrong:
            return False
        code = f"{lst(vals)}\n" + "\n".join(f"z.{op}();" for op in ops) + f"\n{PRINT}"
        return b.add("ls-sort-reverse", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl="`Sort` zoradí vzostupne, `Reverse` otočí aktuálne poradie." + (" `Reverse` samo nezoradí." if ops == ["Reverse"] else ""),
                     en_expl="`Sort` sorts ascending; `Reverse` reverses the current order." + (" `Reverse` alone doesn't sort." if ops == ["Reverse"] else ""),
                     verify={"type": "output"})
    fill(b, "ls-sort-reverse", 25, sort_reverse)

    def function_adds():
        vals = dig(R.randint(1, 3)); form = R.choice(["add", "add2", "removeat"])
        if form == "add":
            x = R.randint(5, 9); body = [f"zoznam.Add({x});"]; res = vals + [x]
        elif form == "add2":
            x, y = R.randint(5, 9), R.randint(5, 9); body = [f"zoznam.Add({x});", f"zoznam.Add({y});"]; res = vals + [x, y]
        else:
            if len(vals) < 2:
                return False
            body = ["zoznam.RemoveAt(0);"]; res = vals[1:]
        ask = R.choice(["count", "last"])
        expr = "z.Count" if ask == "count" else "z[z.Count - 1]"
        v = len(res) if ask == "count" else res[-1]
        before = len(vals) if ask == "count" else vals[-1]
        wrong = pick_wrong(v, [before, v + 1, 0, len(body)])
        bl = "\n".join("    " + l for l in body)
        code = f"{lst(vals)}\nUprav(z);\nint v = {expr};\n\nvoid Uprav(List<int> zoznam)\n{{\n{bl}\n}}"
        return b.add("ls-function-adds", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl="Funkcia dostane ten istý zoznam, nie kópiu – zmena je viditeľná aj mimo nej.",
                     en_expl="The function gets the same list, not a copy – the change is visible outside it.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ls-function-adds", 25, function_adds)

    def out_of_range():
        n = R.randint(3, 5); vals = dig(n)
        bad = R.choice([f"int x = z[{n}];", "int x = z[z.Count];", "z.RemoveAt(z.Count);", "int x = z[-1];", f"z.Insert({n + 1}, 0);", f"z[{n}] = 1;"])
        valid = R.sample([f"z.Insert({n}, 7);", "z.Remove(99);", f"int x = z[{n - 1}];", "int x = z[z.Count - 1];", "z.RemoveAt(0);", "z.Add(5);"], 3)
        sk = f"Platné indexy sú 0 až `Count - 1` = {n - 1} (pri `Insert` aj `Count`). `{bad}` je mimo rozsahu."
        en = f"Valid indexes are 0 to `Count - 1` = {n - 1} (for `Insert` also `Count`). `{bad}` is out of range."
        if "z.Remove(99);" in valid:
            sk += " `Remove` hodnoty, ktorá v zozname nie je, nespadne."; en += " `Remove` of a missing value doesn't crash."
        return b.add("ls-out-of-range", 2, code=lst(vals), sk_body="{code}\nKtorý riadok spôsobí pád programu?", en_body="{code}\nWhich line makes the program crash?",
                     answers=[code_ans(bad)] + [code_ans(v) for v in valid], sk_expl=sk, en_expl=en,
                     verify={"type": "which-line", "expect": "exception"})
    fill(b, "ls-out-of-range", 25, out_of_range)

    def remove_missing():
        n = R.randint(3, 5); vals = dig(n, 0, 9)
        cand = [k for k in range(n) if k not in vals] if R.random() < 0.5 else []
        x = R.choice(cand) if cand else R.choice([k for k in range(10, 20)])
        out = s(vals)
        idx_rm = vals[:x] + vals[x + 1:] if x < n else None
        sk, en = text_answers([code_ans(out), CRASH, code_ans(s(idx_rm)) if idx_rm else code_ans(s(vals[:-1])), code_ans(s(vals[1:]))])
        if len(set(sk)) < 4:
            return False
        code = f"{lst(vals)}\nz.Remove({x});\n{PRINT}"
        return b.add("ls-remove-missing", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"`Remove` hodnotu {x} nenájde, preto nič neodstráni a nespadne" + (f" – {x} by bol index, ale `Remove` hľadá hodnotu." if x < n else "."),
                     en_expl=f"`Remove` doesn't find {x}, so it removes nothing and doesn't crash" + (f" – {x} would be an index, but `Remove` looks for a value." if x < n else "."),
                     verify={"type": "output"})
    fill(b, "ls-remove-missing", 25, remove_missing)

    # =================================================================== HARD
    COND = [("z[i] % 2 == 0", lambda x: x % 2 == 0), ("z[i] > {k}", None), ("z[i] == {k}", None)]
    def pick_cond():
        c, f = R.choice(COND)
        if f is None:
            k = R.randint(2, 6); c = c.format(k=k); f = (lambda x, k=k: x > k) if ">" in c else (lambda x, k=k: x == k)
        return c, f
    def forward_loop():
        c, f = pick_cond()
        n = R.randint(4, 6); vals = [R.randint(1, 9) for _ in range(n)]
        cur, i = vals[:], 0
        while i < len(cur):
            if f(cur[i]):
                del cur[i]
            i += 1
        correct_filter = [x for x in vals if not f(x)]
        if cur == correct_filter:
            return False
        out = s(cur)
        wrong = pick_wrong(out, [s(correct_filter), s(vals), s([x for x in vals if f(x)])])
        if not wrong:
            return False
        code = f"{lst(vals)}\nfor (int i = 0; i < z.Count; i++)\n{{\n    if ({c})\n        z.RemoveAt(i);\n}}\n{PRINT}"
        return b.add("ls-remove-forward-loop", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl="Po `RemoveAt(i)` sa ďalší prvok posunie na index i, ale cyklus pokračuje s `i + 1` – ten prvok sa preskočí a nemusí sa odstrániť.",
                     en_expl="After `RemoveAt(i)` the next element moves to index i, but the loop continues with `i + 1` – that element is skipped and may stay.",
                     verify={"type": "output"})
    fill(b, "ls-remove-forward-loop", 25, forward_loop)

    def backward_loop():
        c, f = pick_cond()
        n = R.randint(4, 6); vals = [R.randint(1, 9) for _ in range(n)]
        res = [x for x in vals if not f(x)]
        if len(res) in (0, n):
            return False
        cur, i = vals[:], 0
        while i < len(cur):
            if f(cur[i]):
                del cur[i]
            i += 1
        out = s(res)
        wrong = pick_wrong(out, [s(cur), s(vals), s([x for x in vals if f(x)]), s(res[::-1])])
        if not wrong:
            return False
        code = f"{lst(vals)}\nfor (int i = z.Count - 1; i >= 0; i--)\n{{\n    if ({c})\n        z.RemoveAt(i);\n}}\n{PRINT}"
        return b.add("ls-remove-backward-loop", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl="Pri mazaní odzadu sa posúvajú iba už skontrolované prvky, takže sa nič nepreskočí – odstránia sa všetky prvky, pre ktoré platí podmienka.",
                     en_expl="When removing from the back, only already-checked elements move, so nothing is skipped – every matching element is removed.",
                     verify={"type": "output"})
    fill(b, "ls-remove-backward-loop", 25, backward_loop)

    def add_in_loop():
        vals = [R.randint(0, 4) for _ in range(R.randint(1, 3))]
        if sum(vals) > 6 or max(vals) == 0:
            return False
        saved = R.random() < 0.4
        cur = vals[:]
        if saved:
            n = len(cur)
            for i in range(n):
                if cur[i] > 0:
                    cur.append(cur[i] - 1)
            loop = "int n = z.Count;\nfor (int i = 0; i < n; i++)"
        else:
            i = 0
            while i < len(cur):
                if cur[i] > 0:
                    cur.append(cur[i] - 1)
                i += 1
            loop = "for (int i = 0; i < z.Count; i++)"
        out = s(cur)
        alt = vals[:]
        for i in range(len(vals)):
            if alt[i] > 0:
                alt.append(alt[i] - 1)
        full = vals[:]
        i = 0
        while i < len(full):
            if full[i] > 0:
                full.append(full[i] - 1)
            i += 1
        wrong = pick_wrong(out, [s(alt), s(full), s(vals), s(sorted(cur, reverse=True)), s(cur[::-1]), s(cur[:-1])])
        if not wrong:
            return False
        code = f"{lst(vals)}\n{loop}\n{{\n    if (z[i] > 0)\n        z.Add(z[i] - 1);\n}}\n{PRINT}"
        esk = ("Počet opakovaní je uložený v `n` vopred, takže sa spracujú iba pôvodné prvky." if saved
               else "Podmienka `i < z.Count` sa kontroluje stále znova a `Count` rastie, takže cyklus spracuje aj novo pridané prvky – kým nedôjde k nule.")
        een = ("The number of repetitions is saved in `n` beforehand, so only the original elements are processed." if saved
               else "`i < z.Count` is checked again every time and `Count` grows, so the loop also processes the newly added elements – until it reaches zero.")
        return b.add("ls-add-in-loop", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "output"})
    fill(b, "ls-add-in-loop", 25, add_in_loop)

    def reference_copy():
        vals = dig(R.randint(2, 4)); form = R.choice(["add", "removeat", "set"])
        if form == "add":
            x = R.randint(10, 20); op = f"b.Add({x});"; expr = "a.Count"; v = len(vals) + 1; wrong = [len(vals), v + 1, x]
        elif form == "removeat":
            op = "b.RemoveAt(0);"; expr = "a.Count"; v = len(vals) - 1; wrong = [len(vals), 0, v - 1 if v > 0 else 2]
        else:
            x = R.randint(10, 20); op = f"b[0] = {x};"; expr = "a[0]"; v = x; wrong = [vals[0], 0, vals[-1]]
        wrong = pick_wrong(v, wrong)
        code = f"{lst(vals, 'a')}\nList<int> b = a;\n{op}\nint v = {expr};"
        return b.add("ls-reference-copy", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl="`b = a` neskopíruje zoznam – obe premenné ukazujú na ten istý, takže zmena cez `b` je viditeľná aj v `a`.",
                     en_expl="`b = a` doesn't copy the list – both variables point to the same one, so the change through `b` shows in `a` too.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ls-reference-copy", 25, reference_copy)

    def real_copy():
        vals = dig(R.randint(2, 4)); na = len(vals)
        ops_b = R.choice([["b.Add(7);"], ["b.Add(7);", "b.Add(8);"], ["b.RemoveAt(0);"], ["b.Clear();"]])
        ops_a = R.choice([[], [], ["a.Add(1);"]])
        nb = na
        for o in ops_b:
            nb = nb + 1 if "Add" in o else (nb - 1 if "RemoveAt" in o else 0)
        na2 = na + len(ops_a)
        copy = R.choice(["new List<int>(a)", "loop"])
        cl = "List<int> b = new List<int>(a);" if copy == "new List<int>(a)" else "List<int> b = new List<int>();\nfor (int i = 0; i < a.Count; i++)\n    b.Add(a[i]);"
        c = f"a.Count = {na2}, b.Count = {nb}"
        wrong = pick_wrong(c, [f"a.Count = {nb}, b.Count = {nb}", f"a.Count = {na}, b.Count = {na}", f"a.Count = {nb}, b.Count = {na2}", f"a.Count = {na2 + nb - na}, b.Count = {nb}"])
        if not wrong:
            return False
        code = f"{lst(vals, 'a')}\n{cl}\n" + "\n".join(ops_b + ops_a)
        return b.add("ls-real-copy", 3, code=code,
                     sk_body="{code}\nAké hodnoty budú mať `a.Count` a `b.Count`?", en_body="{code}\nWhat values will `a.Count` and `b.Count` have?",
                     answers=[code_ans(c)] + [code_ans(w) for w in wrong],
                     sk_expl="`b` je nový zoznam s kópiou prvkov – zmeny jedného zoznamu druhý neovplyvnia.",
                     en_expl="`b` is a new list with copies of the elements – changes to one list don't affect the other.",
                     verify={"type": "value", "expr": '$"a.Count = {a.Count}, b.Count = {b.Count}"'})
    fill(b, "ls-real-copy", 25, real_copy)

    def insert_bounds():
        n = R.randint(2, 4); vals = dig(n, 1, 8); x = 9 if 9 not in vals else 0
        form = R.choice(["count", "count", "count1", "index"])
        line = {"count": "z.Insert(z.Count, {x});", "count1": "z.Insert(z.Count + 1, {x});", "index": "z[z.Count] = {x};"}[form].format(x=x)
        code = f"{lst(vals)}\n{line}\n{PRINT}"
        if form == "count":
            sk, en = text_answers([code_ans(s(vals + [x])), CRASH, code_ans(s([x] + vals)), code_ans(s(vals))])
            esk, een = "`Insert(z.Count, …)` je povolené – vloží prvok na koniec, rovnako ako `Add`.", "`Insert(z.Count, …)` is allowed – it puts the element at the end, like `Add`."
            verify = {"type": "output"}
        else:
            sk, en = text_answers([CRASH, code_ans(s(vals + [x])), code_ans(s(vals)), code_ans(s([x] + vals))])
            esk, een = ("`Insert` dovolí index najviac `Count`; `Count + 1` je mimo rozsahu." if form == "count1" else "`z[z.Count]` neexistuje – indexovaním sa nedá pridať nový prvok, na to slúži `Add`.",
                        "`Insert` allows an index up to `Count`; `Count + 1` is out of range." if form == "count1" else "`z[z.Count]` doesn't exist – indexing can't add an element; that's what `Add` is for.")
            verify = {"type": "exception", "name": "ArgumentOutOfRangeException", "stdout": ""}
        return b.add("ls-insert-bounds", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=esk, en_expl=een, verify=verify)
    fill(b, "ls-insert-bounds", 25, insert_bounds)

    def remove_dupes_index():
        n = R.randint(4, 5); vals = [R.randint(0, 3) for _ in range(n)]
        cur = vals[:]; lines, steps = [], []
        for _ in range(R.randint(2, 3)):
            if R.random() < 0.5:
                x = R.choice(cur); cur.remove(x); lines.append(f"z.Remove({x});")
            else:
                i = R.randrange(len(cur)); del cur[i]; lines.append(f"z.RemoveAt({i});")
            steps.append("{" + ", ".join(map(str, cur)) + "}")
            if not cur:
                return False
        # the "swapped" interpretation
        alt = vals[:]
        for l in lines:
            k = int(l[l.index("(") + 1:-2])
            if l.startswith("z.Remove("):
                if k < len(alt):
                    del alt[k]
            else:
                if k in alt:
                    alt.remove(k)
        out = s(cur)
        wrong = pick_wrong(out, [s(alt), s(vals), s(cur[:-1]) if len(cur) > 1 else s(vals[:2]), steps[0].strip("{}").replace(", ", "")])
        if not wrong:
            return False
        code = f"{lst(vals)}\n" + "\n".join(lines) + f"\n{PRINT}"
        return b.add("ls-remove-dupes-index", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`Remove(x)` hľadá hodnotu, `RemoveAt(i)` index. Po krokoch: {' → '.join(steps)}.",
                     en_expl=f"`Remove(x)` looks for a value, `RemoveAt(i)` for an index. Step by step: {' → '.join(steps)}.",
                     verify={"type": "output"})
    fill(b, "ls-remove-dupes-index", 25, remove_dupes_index)

    def stale_index():
        n = R.randint(4, 5); vals = dig(n, 0, 20); x = R.choice(vals[1:-1]); idx = vals.index(x)
        if R.random() < 0.5:
            y = R.randint(21, 30); op = f"z.Insert(0, {y});"; cur = [y] + vals
        else:
            op = "z.RemoveAt(0);"; cur = vals[1:]
        v = cur[idx]
        wrong = pick_wrong(v, [x, cur[idx - 1] if idx > 0 else cur[-1], idx, cur[(idx + 1) % len(cur)]])
        if not wrong:
            return False
        code = f"{lst(vals)}\nint idx = z.IndexOf({x});\n{op}\nint v = z[idx];"
        return b.add("ls-stale-index", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`idx` je {idx}, ale po `{op}` sa prvky posunuli, takže na indexe {idx} je teraz `{v}`, nie {x}.",
                     en_expl=f"`idx` is {idx}, but after `{op}` the elements moved, so index {idx} now holds `{v}`, not {x}.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "ls-stale-index", 25, stale_index)

    def while_count():
        n = R.randint(4, 6); vals = dig(n); k = R.randint(1, n - 2)
        form = R.choice(["front", "back", "alt"])
        cur = vals[:]
        if form == "front":
            body = "z.RemoveAt(0);"; cur = cur[n - k:]
        elif form == "back":
            body = "z.RemoveAt(z.Count - 1);"; cur = cur[:k]
        else:
            body = "z.RemoveAt(0);\n    if (z.Count > " + str(k) + ")\n        z.RemoveAt(z.Count - 1);"
            while len(cur) > k:
                cur.pop(0)
                if len(cur) > k:
                    cur.pop()
        out = s(cur)
        wrong = pick_wrong(out, [s(vals[:k]) if form != "back" else s(vals[n - k:]), s(vals[n - k - 1:]), s(vals[:k + 1]), s(vals)])
        if not wrong:
            return False
        braces = "{\n    " + body + "\n}" if "\n" in body else "    " + body
        code = f"{lst(vals)}\nwhile (z.Count > {k})\n{braces if braces.startswith('{') else braces}\n{PRINT}"
        return b.add("ls-while-count", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Cyklus maže, kým je v zozname viac ako {k} prvkov; zostane `{{{', '.join(map(str, cur))}}}`.",
                     en_expl=f"The loop removes elements while the list has more than {k}; `{{{', '.join(map(str, cur))}}}` remains.",
                     verify={"type": "output"})
    fill(b, "ls-while-count", 25, while_count)

    VBAD = [("a.Add(4);", "pole nemá `Add` – má pevnú dĺžku", "an array has no `Add` – its length is fixed"),
            ("int n = z.Length;", "zoznam nemá `Length`, má `Count`", "a list has no `Length`, it has `Count`"),
            ("int n = a.Count;", "pole nemá `Count`, má `Length`", "an array has no `Count`, it has `Length`"),
            ("int[] b = z;", "zoznam nie je pole", "a list is not an array"),
            ("List<int> y = a;", "pole nie je zoznam", "an array is not a list"),
            ("a.RemoveAt(0);", "z poľa sa nedá odstrániť prvok", "you can't remove an element from an array")]
    VOK = ["z.Add(4);", "int n = a.Length;", "int x = z[0] + a[0];", "Array.Sort(a);", "z.Sort();", "int c = z.Count;", "a[0] = 5;", "z.Insert(0, a[1]);"]
    def vs_array():
        bad, rsk, ren = R.choice(VBAD); valid = R.sample(VOK, 3)
        return b.add("ls-vs-array-compile", 3, code="int[] a = { 1, 2, 3 };\nList<int> z = new List<int> { 1, 2, 3 };",
                     sk_body="{code}\nKtorý riadok spôsobí chybu pri preklade?", en_body="{code}\nWhich line causes a compile error?",
                     answers=[code_ans(bad)] + [code_ans(v) for v in valid],
                     sk_expl=f"`{bad}` sa nedá preložiť: {rsk}.", en_expl=f"`{bad}` does not compile: {ren}.",
                     verify={"type": "which-line", "expect": "compile-error"})
    fill(b, "ls-vs-array-compile", 25, vs_array)

    def unique():
        n = R.randint(5, 7); vals = [R.randint(1, 5) for _ in range(n)]
        u = []
        for x in vals:
            if x not in u:
                u.append(x)
        if len(u) == n:
            return False
        dupl = [x for x in u if vals.count(x) > 1]
        out = s(u)
        wrong = pick_wrong(out, [s(sorted(u)), s(vals), s(dupl), s(u[::-1])])
        if not wrong:
            return False
        code = (f"{lst(vals, 'a')}\nList<int> b = new List<int>();\nfor (int i = 0; i < a.Count; i++)\n{{\n    if (!b.Contains(a[i]))\n        b.Add(a[i]);\n}}\n"
                f"for (int i = 0; i < b.Count; i++)\n    Console.Write(b[i]);")
        return b.add("ls-unique", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl="Hodnota sa pridá iba vtedy, keď ešte v `b` nie je – zostane poradie prvých výskytov (nezoradené).",
                     en_expl="A value is added only when it isn't in `b` yet – the order of first appearances stays (not sorted).",
                     verify={"type": "output"})
    fill(b, "ls-unique", 25, unique)

    def trace():
        vals = dig(R.randint(3, 4), 1, 6); t = R.randint(2, 5)
        cur = vals[:]; n0 = len(vals)
        for i in range(n0):
            if cur[i] > t:
                cur.insert(0, 0)
            else:
                cur.append(cur[i] * 2)
        code = f"{lst(vals)}\nint n = z.Count;\nfor (int i = 0; i < n; i++)\n{{\n    if (z[i] > {t})\n        z.Insert(0, 0);\n    else\n        z.Add(z[i] * 2);\n}}\n{PRINT}"
        naive = vals[:]
        for i in range(n0):
            if vals[i] > t:
                naive.insert(0, 0)
            else:
                naive.append(vals[i] * 2)
        if naive == cur and R.random() < 0.6:
            return False
        out = s(cur)
        wrong = pick_wrong(out, [s(naive), s(vals), s(cur[::-1]), s(cur[1:])])
        if not wrong or len(out) > 14:
            return False
        return b.add("ls-trace", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`Insert(0, 0)` posunie prvky dozadu, takže ďalšie `z[i]` už ukazuje na iný prvok. Výsledok: `{{{', '.join(map(str, cur))}}}`.",
                     en_expl=f"`Insert(0, 0)` shifts the elements back, so the next `z[i]` points to a different element. Result: `{{{', '.join(map(str, cur))}}}`.",
                     verify={"type": "output"})
    fill(b, "ls-trace", 25, trace)
    return b


if __name__ == "__main__":
    main().write()
