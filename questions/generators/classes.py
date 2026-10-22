"""Generator for topic classes (36 templates × 25).
Scope: classes, objects, new, public/private fields, methods. NO constructors, properties, static, this, inheritance."""
import random
from common import Batch, fill, code_ans, pick_wrong

R = random.Random(20261028)
DATE = "2026-10-22"
OUT_Q = ("{code}\nČo vypíše tento kód?", "{code}\nWhat does this code print?")
NULLCRASH = ("Program spadne (NullReferenceException)", "The program crashes (NullReferenceException)")
COMPILE = ("Chyba pri preklade", "Compile error")
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


def method(header, body):
    lines = [f"    {header}", "    {"] + [f"        {l}" for l in body] + ["    }"]
    return "\n".join(lines)


def cls(name, fields, methods=()):
    blocks = []
    if fields:
        blocks.append("\n".join(f"    {f}" for f in fields))
    blocks += list(methods)
    return f"class {name}\n{{\n" + "\n\n".join(blocks) + "\n}"


def prog(main, *rest):
    return "\n".join(main) + "\n\n" + "\n\n".join(rest)


NAMES = ["Rex", "Max", "Bobík", "Dunčo", "Lassie", "Fifi"]
STUDENTS = ["Eva", "Ján", "Ola", "Peter", "Zuzka", "Tomáš", "Mia", "Karol"]


def main():
    b = Batch(f"{DATE}_classes", "classes", DATE)

    # =================================================================== EASY
    TERMS = {
        "trieda": (("predpis, podľa ktorého sa vytvárajú objekty", "a blueprint used to create objects"), "class"),
        "objekt": (("konkrétna inštancia vytvorená podľa triedy", "a concrete instance created from a class"), "object"),
        "`new`": (("vytvorí nový objekt", "creates a new object"), "`new`"),
        "atribút": (("premenná, ktorá patrí objektu", "a variable that belongs to an object"), "field"),
        "metóda": (("funkcia, ktorá patrí triede", "a function that belongs to a class"), "method"),
        "`public`": (("člen je prístupný aj mimo triedy", "the member can be used outside the class too"), "`public`"),
        "`private`": (("člen je prístupný iba vnútri triedy", "the member can be used only inside the class"), "`private`"),
    }
    FAKE = [("jeden konkrétny pes", "one specific dog"), ("vymaže objekt z pamäte", "deletes an object from memory"),
            ("príkaz, ktorý vypíše objekt", "a statement that prints an object")]
    TQ = [("Čo je {t}?", "What is {t_en}?"), ("Čo v C# znamená {t}?", "What does {t_en} mean in C#?")]
    def term_purpose():
        t = R.choice(list(TERMS)); (mean, ten) = TERMS[t]; q = R.choice(TQ)
        others = [TERMS[o][0] for o in TERMS if o != t]
        pool = others + FAKE
        R.shuffle(pool)
        sk, en = text_answers([mean] + pool[:3])
        return b.add("cl-term-purpose", 1, code=None, sk_body=q[0].format(t=t), en_body=q[1].format(t_en=ten), answers=sk, en_answers=en,
                     sk_expl=f"{t}: {mean[0]}.", en_expl=f"{ten}: {mean[1]}.", verify={"type": "none"})
    fill(b, "cl-term-purpose", 25, term_purpose)

    PQ = [("Ako sa volá {d}?", "What do we call {d}?"), ("Čo je {d}?", "What is {d}?")]
    SK_NAMES = {"trieda": ("trieda", "class"), "objekt": ("objekt", "object"), "`new`": ("`new`", "`new`"), "atribút": ("atribút", "field"),
                "metóda": ("metóda", "method"), "`public`": ("`public`", "`public`"), "`private`": ("`private`", "`private`")}
    LOOK = {"trieda": ["objekt", "metóda", "atribút"], "objekt": ["trieda", "atribút", "metóda"], "`new`": ["trieda", "metóda", "`public`"],
            "atribút": ["metóda", "objekt", "trieda"], "metóda": ["atribút", "trieda", "objekt"], "`public`": ["`private`", "`new`", "metóda"],
            "`private`": ["`public`", "`new`", "atribút"]}
    DESCR = {"trieda": [("predpis, podľa ktorého sa vytvárajú objekty", "a blueprint used to create objects"), ("šablóna, ktorá opisuje, aké atribúty a metódy budú mať objekty", "a template describing which fields and methods objects will have")],
             "objekt": [("konkrétna inštancia vytvorená pomocou `new`", "a concrete instance created with `new`"), ("jeden konkrétny pes vytvorený podľa triedy `Pes`", "one concrete dog created from the class `Pes`")],
             "`new`": [("kľúčové slovo, ktorým vytvoríme objekt", "the keyword that creates an object"), ("slovo pred názvom triedy v zápise `Pes p = … Pes();`", "the word before the class name in `Pes p = … Pes();`")],
             "atribút": [("premenná vo vnútri triedy, ktorú má každý objekt", "a variable inside a class that every object has"), ("napríklad `Meno` alebo `Vek` v triede `Pes`", "for example `Meno` or `Vek` in the class `Pes`")],
             "metóda": [("funkcia napísaná vo vnútri triedy", "a function written inside a class"), ("napríklad `Stekaj()` v triede `Pes`", "for example `Stekaj()` in the class `Pes`")],
             "`public`": [("modifikátor, vďaka ktorému je člen dostupný aj mimo triedy", "the modifier that makes a member available outside the class"), ("modifikátor, ktorý umožní volať metódu z hlavného programu", "the modifier that lets the main program call a method")],
             "`private`": [("modifikátor, vďaka ktorému je člen dostupný iba v metódach triedy", "the modifier that makes a member available only in the class's methods"), ("modifikátor pre atribút, ktorý sa smie meniť iba cez metódy triedy", "the modifier for a field that may change only through the class's methods")]}
    def purpose_term():
        t = R.choice(list(DESCR)); d = R.choice(DESCR[t]); q = R.choice(PQ)
        ans = [SK_NAMES[t]] + [SK_NAMES[o] for o in LOOK[t]]
        sk, en = text_answers(ans)
        return b.add("cl-purpose-term", 1, code=None, sk_body=q[0].format(d=d[0]), en_body=q[1].format(d=d[1]), answers=sk, en_answers=en,
                     sk_expl=f"{d[0][0].upper() + d[0][1:]} – to je {SK_NAMES[t][0]}.", en_expl=f"{d[1][0].upper() + d[1][1:]} – that's {SK_NAMES[t][1]}.",
                     verify={"type": "none"})
    fill(b, "cl-purpose-term", 25, purpose_term, tries=5000)

    CLASSES = [("Pes", ["public string Meno;"], "p"), ("Auto", ["public int Rychlost;"], "a"), ("Ziak", ["public string Meno;", "public int Body;"], "z"),
               ("Bod", ["public int X;", "public int Y;"], "b"), ("Kniha", ["public string Nazov;"], "k"), ("Ucet", ["public int Zostatok;"], "u"),
               ("Hrac", ["public int Zivoty;"], "h"), ("Lopta", ["public int Velkost;"], "l")]
    def create_object():
        name, fields, v = R.choice(CLASSES)
        good = f"{name} {v} = new {name}();"
        bads = [f"{name} {v} = {name}();", f"{name} {v} = new {name};", f"{v} {name} = new {name}();", f"{name} {v} = new {v}();", f"new {name} {v};", f"{name} = new {name}();",
                f"{name} {v} = {name}.new();"]
        wrong = R.sample(bads, 3)
        code = cls(name, fields)
        return b.add("cl-create-object", 1, code=code,
                     sk_body=f"{{code}}\nKtorý riadok správne vytvorí objekt triedy `{name}`?", en_body=f"{{code}}\nWhich line correctly creates an object of the class `{name}`?",
                     answers=[code_ans(good)] + [code_ans(w) for w in wrong],
                     sk_expl="Objekt sa vytvára ako `Trieda premenná = new Trieda();`.", en_expl="An object is created as `Class variable = new Class();`.",
                     verify={"type": "which-line", "expect": "compile-error", "invert": True})
    fill(b, "cl-create-object", 25, create_object)

    def read_field():
        form = R.choice(["pes", "ziak", "bod"])
        if form == "pes":
            m, vek = R.choice(NAMES), R.randint(1, 12)
            setl = [f'p.Meno = "{m}";', f"p.Vek = {vek};"]; ask = R.choice(["Meno", "Vek"]); obj = "p"; cname = "Pes"
            fields = ["public string Meno;", "public int Vek;"]; vals = {"Meno": f'"{m}"', "Vek": str(vek)}; types = {"Meno": "string", "Vek": "int"}
        elif form == "ziak":
            m, bd = R.choice(STUDENTS), R.randint(10, 100)
            setl = [f'z.Meno = "{m}";', f"z.Body = {bd};"]; ask = R.choice(["Meno", "Body"]); obj = "z"; cname = "Ziak"
            fields = ["public string Meno;", "public int Body;"]; vals = {"Meno": f'"{m}"', "Body": str(bd)}; types = {"Meno": "string", "Body": "int"}
        else:
            x, y = R.randint(-9, 9), R.randint(-9, 9)
            if x == y:
                return False
            setl = [f"b.X = {x};", f"b.Y = {y};"]; ask = R.choice(["X", "Y"]); obj = "b"; cname = "Bod"
            fields = ["public int X;", "public int Y;"]; vals = {"X": str(x), "Y": str(y)}; types = {"X": "int", "Y": "int"}
        other = [k for k in vals if k != ask][0]
        v = vals[ask]
        ans = [v, vals[other], ask, "null" if types[ask] == "string" else "0"]
        if len(set(ans)) < 4:
            ans[3] = cname
        code = prog([f"{cname} {obj} = new {cname}();"] + setl + [f"{types[ask]} v = {obj}.{ask};"], cls(cname, fields))
        return b.add("cl-read-field", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1], answers=[code_ans(a) for a in ans],
                     sk_expl=f"Do atribútu `{ask}` objektu `{obj}` sme priradili `{v}`.", en_expl=f"We assigned `{v}` to the field `{ask}` of `{obj}`.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-read-field", 25, read_field)

    RET = [("Obdlznik", "o", ["A", "B"], "Obsah", "A * B", lambda a, c: a * c), ("Obdlznik", "o", ["A", "B"], "Obvod", "2 * (A + B)", lambda a, c: 2 * (a + c)),
           ("Bod", "b", ["X", "Y"], "Sucet", "X + Y", lambda a, c: a + c), ("Ziak", "z", ["Body", "Bonus"], "Spolu", "Body + Bonus", lambda a, c: a + c),
           ("Kvader", "k", ["A", "B"], "Rozdiel", "A - B", lambda a, c: a - c)]
    def method_return():
        cname, obj, (f1, f2), mname, expr, f = R.choice(RET)
        x, y = R.randint(2, 12), R.randint(2, 12)
        if x == y:
            return False
        v = f(x, y)
        wrong = pick_wrong(v, [x + y, x * y, x, 2 * x + y, 0])
        code = prog([f"{cname} {obj} = new {cname}();", f"{obj}.{f1} = {x};", f"{obj}.{f2} = {y};", f"int v = {obj}.{mname}();"],
                    cls(cname, [f"public int {f1};", f"public int {f2};"], [method(f"public int {mname}()", [f"return {expr};"])]))
        e = expr.replace(f1, str(x)).replace(f2, str(y))
        return b.add("cl-method-return", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Metóda `{mname}` použije atribúty objektu: `{e}` = {v}.", en_expl=f"The method `{mname}` uses the object's fields: `{e}` = {v}.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-method-return", 25, method_return)

    def fields_then_method():
        form = R.choice(["popis", "sucet3", "meno"])
        if form == "popis":
            m, vek = R.choice(NAMES), R.randint(1, 15)
            code = prog(["Pes p = new Pes();", f'p.Meno = "{m}";', f"p.Vek = {vek};", "string s = p.Popis();"],
                        cls("Pes", ["public string Meno;", "public int Vek;"], [method("public string Popis()", ['return Meno + " má " + Vek + " rokov";'])]))
            v = f'"{m} má {vek} rokov"'; ans = [v, f'"Meno má Vek rokov"', f'"{m}"', f'"{vek} má {m} rokov"']; name = "s"
        elif form == "sucet3":
            a, c, d = R.randint(1, 9), R.randint(1, 9), R.randint(1, 9)
            code = prog(["Trojuholnik t = new Trojuholnik();", f"t.A = {a};", f"t.B = {c};", f"t.C = {d};", "int s = t.Obvod();"],
                        cls("Trojuholnik", ["public int A;", "public int B;", "public int C;"], [method("public int Obvod()", ["return A + B + C;"])]))
            v = a + c + d; ans = [str(v), str(a + c), str(a * c * d), str(d)]; name = "s"
            if len(set(ans)) < 4:
                return False
        else:
            m, p = R.choice(STUDENTS), R.choice(["Nová", "Malá", "Kováč", "Horák", "Varga"])
            code = prog(["Osoba o = new Osoba();", f'o.Meno = "{m}";', f'o.Priezvisko = "{p}";', "string s = o.CeleMeno();"],
                        cls("Osoba", ["public string Meno;", "public string Priezvisko;"], [method("public string CeleMeno()", ['return Meno + " " + Priezvisko;'])]))
            v = f'"{m} {p}"'; ans = [v, f'"{m}{p}"', f'"{p} {m}"', '"Meno Priezvisko"']; name = "s"
        return b.add("cl-fields-then-method", 1, code=code, sk_body=val_q(name)[0], en_body=val_q(name)[1], answers=[code_ans(a) for a in ans],
                     sk_expl=f"Metóda pracuje s hodnotami, ktoré sme nastavili do atribútov – vráti `{v}`.",
                     en_expl=f"The method works with the values we set into the fields – it returns `{v}`.",
                     verify={"type": "value", "expr": name})
    fill(b, "cl-fields-then-method", 25, fields_then_method)

    DV = [("int", "0", ["`1`", "Chyba pri preklade"]), ("bool", "false", ["`true`", "Chyba pri preklade"]), ("string", "null", ['`""`', "Chyba pri preklade"]),
          ("double", "0", ["`1`", "Chyba pri preklade"])]
    FNAMES = {"int": ["Body", "Vek", "Pocet", "Skore"], "bool": ["JeAktivny", "Hotovo", "Platne"], "string": ["Meno", "Nazov", "Mesto"], "double": ["Cena", "Vaha", "Priemer"]}
    def default_values():
        t, d, extra = R.choice(DV); fname = R.choice(FNAMES[t]); other_t = R.choice([x for x in FNAMES if x != t]); other = R.choice(FNAMES[other_t])
        cname = R.choice(["Ziak", "Produkt", "Hrac", "Zaznam"])
        code = prog([f"{cname} o = new {cname}();", f"{t} v = o.{fname};"], cls(cname, [f"public {t} {fname};", f"public {other_t} {other};"]))
        ans = [f"`{d}`", extra[0], f"`{fname}`", COMPILE]
        sk, en = text_answers(ans)
        return b.add("cl-default-values", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1], answers=sk, en_answers=en,
                     sk_expl=f"Nenastavený atribút má predvolenú hodnotu – pre `{t}` je to `{d}`.", en_expl=f"An unset field has the default value – for `{t}` it's `{d}`.",
                     verify={"type": "value", "expr": "v", "expected": d})
    fill(b, "cl-default-values", 25, default_values)

    VM = [("Pes", "p", "Stekaj", "H"), ("Auto", "a", "Trubi", "T"), ("Macka", "m", "Mnaukaj", "M"), ("Robot", "r", "Pipni", "P"), ("Zvoncek", "z", "Zazvon", "Z")]
    def void_method():
        cname, obj, mname, letter = R.choice(VM); n = R.randint(1, 3)
        two = R.random() < 0.35
        if two:
            l2 = R.choice([x for x in "ABCXY" if x != letter])
            calls = [R.choice([mname, "Spi"]) for _ in range(R.randint(2, 4))]
            if len(set(calls)) < 2:
                return False
            out = "".join(letter if c == mname else l2 for c in calls)
            methods = [method(f"public void {mname}()", [W(letter)]), method("public void Spi()", [W(l2)])]
            wrong = pick_wrong(out, [out[::-1], letter * len(calls), out[:-1], out + out[-1]])
        else:
            calls = [mname] * n; out = letter * n
            methods = [method(f"public void {mname}()", [W(letter)])]
            wrong = pick_wrong(out, [letter * (n + 1), letter * (n - 1) if n > 1 else letter * 2, letter * (n + 2)], n=2)
            if wrong:
                wrong = wrong + [NOTHING]
        if not wrong:
            return False
        code = prog([f"{cname} {obj} = new {cname}();"] + [f"{obj}.{c}();" for c in calls], cls(cname, [], methods))
        sk, en = text_answers([code_ans(out)] + [w if isinstance(w, tuple) else code_ans(w) for w in wrong])
        return b.add("cl-void-method", 1, code=code.replace("class " + cname + "\n{\n\n", "class " + cname + "\n{\n"), sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl="Telo metódy sa vykoná pri každom volaní – samotné vytvorenie objektu nič nevypíše.",
                     en_expl="The method body runs on every call – creating the object prints nothing.",
                     verify={"type": "output"})
    fill(b, "cl-void-method", 25, void_method)

    def independent():
        cname, f = R.choice([("Bod", "X"), ("Ziak", "Body"), ("Ucet", "Zostatok"), ("Hrac", "Zivoty"), ("Auto", "Rychlost")])
        x, y = R.randint(1, 50), R.randint(1, 50)
        if x == y:
            return False
        ask = R.choice(["a", "b"])
        v = x if ask == "a" else y
        code = prog([f"{cname} a = new {cname}();", f"{cname} b = new {cname}();", f"a.{f} = {x};", f"b.{f} = {y};", f"int v = {ask}.{f};"], cls(cname, [f"public int {f};"]))
        wrong = pick_wrong(v, [y if ask == "a" else x, x + y, 0])
        return b.add("cl-independent-objects", 1, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl="Každý objekt má vlastné atribúty – zmena jedného objektu neovplyvní druhý.",
                     en_expl="Each object has its own fields – changing one object doesn't affect the other.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-independent-objects", 25, independent)

    CVO = [("Auto", "a", "Rychlost", "Trubi"), ("Pes", "p", "Vek", "Stekaj"), ("Ziak", "z", "Body", "Pozdrav"), ("Lopta", "l", "Velkost", "Odraz"), ("Hrac", "h", "Zivoty", "Skoc")]
    WHAT = [("deklaruje trieda", "a class declared", 0), ("vytvára objekt", "an object created", 1), ("nastavuje atribút", "a field set", 2), ("volá metóda", "a method called", 3)]
    def class_vs_object():
        cname, v, f, m = R.choice(CVO); n = R.randint(10, 90)
        lines = [f"class {cname}", f"{cname} {v} = new {cname}();", f"{v}.{f} = {n};", f"{v}.{m}();"]
        wsk, wen, k = R.choice(WHAT)
        code = prog(lines[1:], cls(cname, [f"public int {f};"], [method(f"public void {m}()", [W("!")])]))
        return b.add("cl-class-vs-object", 1, code=code,
                     sk_body=f"{{code}}\nV ktorom riadku sa **{wsk}**?", en_body=f"{{code}}\nIn which line is **{wen}**?",
                     answers=[code_ans(lines[k])] + [code_ans(l) for i, l in enumerate(lines) if i != k],
                     sk_expl=["`class …` deklaruje triedu (predpis).", "`new` vytvorí objekt.", "Zápis `objekt.Atribut = …` nastaví atribút.", "Zápis `objekt.Metoda()` zavolá metódu."][k],
                     en_expl=["`class …` declares a class (the blueprint).", "`new` creates an object.", "`object.Field = …` sets a field.", "`object.Method()` calls a method."][k],
                     verify={"type": "none"})
    fill(b, "cl-class-vs-object", 25, class_vs_object)

    FOM = [("Pes", [("public string Meno;", "Meno", "f"), ("private int vek;", "vek", "f")], [("public void Stekaj()", "Stekaj", ['Console.Write("Haf");']), ("public int Vek()", "Vek", ["return vek;"])]),
           ("Ucet", [("private int zostatok;", "zostatok", "f"), ("public string Majitel;", "Majitel", "f")], [("public void Vloz(int suma)", "Vloz", ["zostatok = zostatok + suma;"]), ("public int Stav()", "Stav", ["return zostatok;"])]),
           ("Auto", [("public int Rychlost;", "Rychlost", "f"), ("private string farba;", "farba", "f")], [("public void Zrychli()", "Zrychli", ["Rychlost = Rychlost + 10;"]), ("public string Farba()", "Farba", ["return farba;"])]),
           ("Hrac", [("public string Meno;", "Meno", "f"), ("private int zivoty;", "zivoty", "f")], [("public void Zasah()", "Zasah", ["zivoty = zivoty - 1;"]), ("public bool JeZivy()", "JeZivy", ["return zivoty > 0;"])]),
           ("Ziak", [("private int body;", "body", "f"), ("public string Trieda;", "Trieda", "f")], [("public void Pridaj(int b)", "Pridaj", ["body = body + b;"]), ("public int Body()", "Body", ["return body;"])]),
           ("Lampa", [("public bool Svieti;", "Svieti", "f"), ("private int pocetZapnuti;", "pocetZapnuti", "f")], [("public void Zapni()", "Zapni", ["Svieti = true;", "pocetZapnuti = pocetZapnuti + 1;"]), ("public int Zapnuti()", "Zapnuti", ["return pocetZapnuti;"])]),
           ("Kniha", [("public string Nazov;", "Nazov", "f"), ("private int strana;", "strana", "f")], [("public void Listuj()", "Listuj", ["strana = strana + 1;"]), ("public int AktualnaStrana()", "AktualnaStrana", ["return strana;"])]),
           ("Termostat", [("private int teplota;", "teplota", "f"), ("public string Miestnost;", "Miestnost", "f")], [("public void Zvys()", "Zvys", ["teplota = teplota + 1;"]), ("public int Teplota()", "Teplota", ["return teplota;"])])]
    def field_or_method():
        cname, fields, methods = R.choice(FOM)
        items = [(n, "f") for _, n, _ in fields] + [(n, "m") for _, n, _ in methods]
        member, kind = R.choice(items)
        ms = [method(h, body) for h, _, body in methods]
        code = cls(cname, [d for d, _, _ in fields], ms)
        if kind == "f":
            ans = [("atribút", "field"), ("metóda", "method"), ("trieda", "class"), ("objekt", "object")]
            esk, een = "Je to premenná deklarovaná v triede – atribút.", "It's a variable declared in the class – a field."
        else:
            ans = [("metóda", "method"), ("atribút", "field"), ("trieda", "class"), ("objekt", "object")]
            esk, een = "Má zátvorky a telo – je to metóda.", "It has brackets and a body – it's a method."
        sk, en = text_answers(ans)
        return b.add("cl-field-or-method", 1, code=code, sk_body=f"{{code}}\nČo je `{member}` v tejto triede?", en_body=f"{{code}}\nWhat is `{member}` in this class?",
                     answers=sk, en_answers=en, sk_expl=esk, en_expl=een, verify={"type": "none"})
    fill(b, "cl-field-or-method", 25, field_or_method, tries=5000)

    def private_meaning():
        cname, fields, methods = R.choice(FOM)
        f_decl, f_name, _ = R.choice(fields)
        ms = [method(h, body) for h, _, body in methods]
        code = cls(cname, [d for d, _, _ in fields], ms)
        priv = f_decl.startswith("private")
        if priv:
            ans = [("iba z metód tej istej triedy", "only from the class's own methods"), ("odkiaľkoľvek, aj z hlavného programu", "from anywhere, including the main program"),
                   ("iba z hlavného programu", "only from the main program"), ("odnikiaľ – nedá sa použiť", "from nowhere – it can't be used")]
            esk, een = "`private` znamená, že atribút môžu používať iba metódy tej istej triedy.", "`private` means only the class's own methods can use the field."
        else:
            ans = [("odkiaľkoľvek, aj z hlavného programu", "from anywhere, including the main program"), ("iba z metód tej istej triedy", "only from the class's own methods"),
                   ("iba z hlavného programu", "only from the main program"), ("odnikiaľ – nedá sa použiť", "from nowhere – it can't be used")]
            esk, een = "`public` znamená, že atribút je prístupný aj mimo triedy.", "`public` means the field can be used outside the class too."
        sk, en = text_answers(ans)
        q = R.choice([("Odkiaľ je prístupný atribút `{f}`?", "Where can the field `{f}` be accessed from?"), ("Kde môžeme použiť atribút `{f}`?", "Where can we use the field `{f}`?")])
        return b.add("cl-private-meaning", 1, code=code, sk_body="{code}\n" + q[0].format(f=f_name), en_body="{code}\n" + q[1].format(f=f_name),
                     answers=sk, en_answers=en, sk_expl=esk, en_expl=een, verify={"type": "none"})
    fill(b, "cl-private-meaning", 25, private_meaning, tries=5000)

    # =================================================================== MEDIUM
    UCET = cls("Ucet", ["public int Zostatok;"], [method("public void Vloz(int suma)", ["Zostatok = Zostatok + suma;"]),
                                                   method("public void Vyber(int suma)", ["Zostatok = Zostatok - suma;"])])
    def method_changes_field():
        start = R.choice([0, 0, R.randint(10, 50)])
        cur, calls, steps = start, [], []
        for _ in range(R.randint(2, 4)):
            op, x = R.choice(["Vloz", "Vloz", "Vyber"]), R.choice([10, 20, 30, 40, 50, 5, 15])
            cur = cur + x if op == "Vloz" else cur - x
            calls.append(f"u.{op}({x});"); steps.append(str(cur))
        main = ["Ucet u = new Ucet();"] + ([f"u.Zostatok = {start};"] if start else []) + calls + ["int v = u.Zostatok;"]
        last = int(calls[-1][calls[-1].index("(") + 1:-2])
        wrong = pick_wrong(cur, [int(steps[-2]) if len(steps) > 1 else start, last, start, cur + 2 * last])
        return b.add("cl-method-changes-field", 2, code=prog(main, UCET), sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(cur)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Metódy menia atribút `Zostatok` toho istého objektu: {start} → {' → '.join(steps)}.",
                     en_expl=f"The methods change the field `Zostatok` of the same object: {start} → {' → '.join(steps)}.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-method-changes-field", 25, method_changes_field)

    VAL = [("Osoba", "vek", "NastavVek", "Vek", "novy >= 0", lambda v: v >= 0, [15, -3, 40, 0, 7, -10, 18]),
           ("Znamka", "hodnota", "Nastav", "Hodnota", "novy >= 1 && novy <= 5", lambda v: 1 <= v <= 5, [1, 3, 5, 6, 0, -1, 2, 7]),
           ("Teplota", "stupne", "Nastav", "Stupne", "novy >= -50 && novy <= 50", lambda v: -50 <= v <= 50, [20, -5, 60, -70, 35, 100])]
    def validating():
        cname, field, setter, getter, cond, f, pool = R.choice(VAL)
        vals = R.sample(pool, R.randint(2, 3))
        if all(f(v) for v in vals) and R.random() < 0.7:
            return False
        cur = 0
        for v in vals:
            if f(v):
                cur = v
        bad = [v for v in vals if not f(v)]
        wrong = pick_wrong(cur, [vals[-1], vals[0], 0, -1])
        code = prog([f"{cname} o = new {cname}();"] + [f"o.{setter}({v});" for v in vals] + [f"int v = o.{getter}();"],
                    cls(cname, [f"private int {field};"], [method(f"public void {setter}(int novy)", [f"if ({cond})", f"    {field} = novy;"]),
                                                           method(f"public int {getter}()", [f"return {field};"])]))
        return b.add("cl-validating-method", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(cur)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Metóda uloží hodnotu iba vtedy, keď platí `{cond}`" + (f"; {', '.join(map(str, bad))} sa ignoruje." if bad else "."),
                     en_expl=f"The method stores the value only when `{cond}` holds" + (f"; {', '.join(map(str, bad))} is ignored." if bad else "."),
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-validating-method", 25, validating)

    def list_of_objects():
        n = R.randint(2, 4); names = R.sample(STUDENTS, n); pts = [R.randint(5, 50) for _ in range(n)]
        kind = R.choice(["sum", "max", "count"])
        main = ["List<Ziak> ziaci = new List<Ziak>();"]
        for k, (nm, p) in enumerate(zip(names, pts), start=1):
            var = f"z{k}"
            main += [f"Ziak {var} = new Ziak();", f'{var}.Meno = "{nm}";', f"{var}.Body = {p};", f"ziaci.Add({var});"]
        if kind == "sum":
            main += ["int v = 0;", "for (int i = 0; i < ziaci.Count; i++)", "    v = v + ziaci[i].Body;"]; v = sum(pts); wrong = [sum(pts) - pts[-1], n, max(pts)]
        elif kind == "max":
            main += ["int v = ziaci[0].Body;", "for (int i = 1; i < ziaci.Count; i++)", "{", "    if (ziaci[i].Body > v)", "        v = ziaci[i].Body;", "}"]; v = max(pts); wrong = [pts[0], min(pts), sum(pts)]
        else:
            t = R.randint(15, 40)
            main += ["int v = 0;", "for (int i = 0; i < ziaci.Count; i++)", "{", f"    if (ziaci[i].Body > {t})", "        v = v + 1;", "}"]; v = sum(1 for p in pts if p > t); wrong = [n, v + 1, v - 1 if v else n - 1]
        wrong = pick_wrong(v, wrong)
        if not wrong:
            return False
        code = prog(main, cls("Ziak", ["public string Meno;", "public int Body;"]))
        return b.add("cl-list-of-objects", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Cyklus prejde všetky objekty v zozname a pracuje s ich atribútom `Body` ({', '.join(map(str, pts))}).",
                     en_expl=f"The loop goes through all objects in the list and works with their `Body` field ({', '.join(map(str, pts))}).",
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-list-of-objects", 25, list_of_objects)

    def method_calls_method():
        form = R.choice(["stvorec", "popis", "obdlznik"])
        if form == "stvorec":
            a = R.randint(2, 9)
            code = prog(["Stvorec s = new Stvorec();", f"s.Strana = {a};", "int v = s.Obvod();"],
                        cls("Stvorec", ["public int Strana;"], [method("public int Obsah()", ["return Strana * Strana;"]), method("public int Obvod()", ["return 4 * Strana;"]),
                                                               method("public int Spolu()", ["return Obsah() + Obvod();"])]))
            if R.random() < 0.7:
                code = code.replace("int v = s.Obvod();", "int v = s.Spolu();"); v = a * a + 4 * a; inner = f"Obsah() = {a * a}, Obvod() = {4 * a}"; wrong = [a * a, 4 * a, 2 * a * a]
            else:
                v = 4 * a; inner = f"Obvod() = 4 · {a}"; wrong = [a * a, a + 4, a * a + 4 * a]
        elif form == "popis":
            m, vek = R.choice(NAMES), R.randint(1, 15)
            code = prog(["Pes p = new Pes();", f'p.Meno = "{m}";', f"p.Vek = {vek};", "int v = p.VekVLudskychRokoch();"],
                        cls("Pes", ["public string Meno;", "public int Vek;"], [method("public int VekVLudskychRokoch()", ["return Nasob(Vek);"]), method("public int Nasob(int x)", ["return x * 7;"])]))
            v = vek * 7; inner = f"Nasob({vek}) = {v}"; wrong = [vek, 7, vek + 7]
        else:
            a, c = R.randint(2, 9), R.randint(2, 9)
            code = prog(["Obdlznik o = new Obdlznik();", f"o.A = {a};", f"o.B = {c};", "int v = o.DvojnasobnyObsah();"],
                        cls("Obdlznik", ["public int A;", "public int B;"], [method("public int Obsah()", ["return A * B;"]), method("public int DvojnasobnyObsah()", ["return 2 * Obsah();"])]))
            v = 2 * a * c; inner = f"Obsah() = {a * c}"; wrong = [a * c, 2 * (a + c), a * c + 2]
        wrong = pick_wrong(v, wrong)
        if not wrong:
            return False
        return b.add("cl-method-calls-method", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Metóda volá inú metódu toho istého objektu: {inner}, výsledok {v}.",
                     en_expl=f"The method calls another method of the same object: {inner}, result {v}.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-method-calls-method", 25, method_calls_method)

    PRIV = [("Ucet", "u", ["private int zostatok;", "public string Majitel;"], [("public void Vloz(int suma)", ["zostatok = zostatok + suma;"]), ("public int Stav()", ["return zostatok;"])],
             ["u.zostatok = 100;", "int x = u.zostatok;", "u.zostatok++;"], ['u.Majitel = "Eva";', "u.Vloz(100);", "int s = u.Stav();", "string m = u.Majitel;"], "zostatok"),
            ("Hrac", "h", ["private int zivoty;", "public string Meno;"], [("public void Zasah()", ["zivoty = zivoty - 1;"]), ("public int Zivoty()", ["return zivoty;"])],
             ["h.zivoty = 3;", "int z = h.zivoty;", "h.zivoty = h.zivoty - 1;"], ['h.Meno = "Max";', "h.Zasah();", "int z = h.Zivoty();", "string m = h.Meno;"], "zivoty"),
            ("Trezor", "t", ["private string heslo;", "public int Pocet;"], [("public void NastavHeslo(string h)", ["heslo = h;"]), ("private void Skontroluj()", ['Console.Write("ok");'])],
             ['t.heslo = "1234";', "string h = t.heslo;", "t.Skontroluj();"], ['t.NastavHeslo("1234");', "t.Pocet = 5;", "int p = t.Pocet;"], "heslo")]
    def private_compile():
        cname, v, fields, methods, bads, goods, _ = R.choice(PRIV)
        bad = R.choice(bads); valid = R.sample(goods, 3)
        member = bad.split(".")[1].split(" ")[0].split("(")[0].rstrip(";").rstrip("+")
        code = prog([f"{cname} {v} = new {cname}();"], cls(cname, fields, [method(h, bd) for h, bd in methods]))
        return b.add("cl-private-compile", 2, code=code,
                     sk_body="{code}\nKtorý riadok v hlavnom programe spôsobí chybu pri preklade?", en_body="{code}\nWhich line in the main program causes a compile error?",
                     answers=[code_ans(bad)] + [code_ans(x) for x in valid],
                     sk_expl=f"`{member}` je `private` – je prístupný iba v metódach triedy `{cname}`, nie z hlavného programu.",
                     en_expl=f"`{member}` is `private` – it can only be used in the methods of `{cname}`, not from the main program.",
                     verify={"type": "which-line", "expect": "compile-error"})
    fill(b, "cl-private-compile", 25, private_compile, tries=5000)

    def private_via_method():
        cur, calls, steps = 0, [], []
        for _ in range(R.randint(2, 4)):
            x = R.randint(1, 20); cur += x; calls.append(f"s.Pridaj({x});"); steps.append(str(cur))
        loop = R.random() < 0.3
        if loop:
            n, x = R.randint(2, 5), R.randint(2, 10); calls = [f"for (int i = 0; i < {n}; i++)", f"    s.Pridaj({x});"]; cur = n * x; steps = [str(x * (i + 1)) for i in range(n)]
        code = prog(["Skore s = new Skore();"] + calls + ["int v = s.Hodnota();"],
                    cls("Skore", ["private int body;"], [method("public void Pridaj(int b)", ["body = body + b;"]), method("public int Hodnota()", ["return body;"])]))
        wrong = pick_wrong(cur, [int(steps[-2]) if len(steps) > 1 else 0, int(steps[0]), 0, cur + int(steps[0])])
        return b.add("cl-private-via-method", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(cur)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Súkromný atribút `body` sa mení iba cez metódy: {' → '.join(steps)}.",
                     en_expl=f"The private field `body` changes only through methods: {' → '.join(steps)}.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-private-via-method", 25, private_via_method)

    def object_to_function():
        cname, f = R.choice([("Bod", "X"), ("Ziak", "Body"), ("Hrac", "Zivoty"), ("Auto", "Rychlost")])
        x, k = R.randint(1, 20), R.randint(2, 15)
        op = R.choice([("+", lambda v: v + k), ("*", lambda v: v * 2)])
        body = f"o.{f} = o.{f} + {k};" if op[0] == "+" else f"o.{f} = o.{f} * 2;"
        v = op[1](x)
        code = (f"{cname} obj = new {cname}();\nobj.{f} = {x};\nZmen(obj);\nint v = obj.{f};\n\nvoid Zmen({cname} o)\n{{\n    {body}\n}}\n\n" + cls(cname, [f"public int {f};"]))
        wrong = pick_wrong(v, [x, k if op[0] == "+" else 2, op[1](v)])
        return b.add("cl-object-to-function", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl="Funkcia dostane ten istý objekt, nie kópiu – zmena atribútu je viditeľná aj mimo nej.",
                     en_expl="The function gets the same object, not a copy – the field change is visible outside it.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-object-to-function", 25, object_to_function)

    BM = [("Ucet", "u", "Zostatok", "MozeVybrat(int suma)", "suma <= Zostatok", "MozeVybrat({a})", lambda f, a: a <= f),
          ("Osoba", "o", "Vek", "JePlnolety()", "Vek >= 18", "JePlnolety()", lambda f, a: f >= 18),
          ("Teplomer", "t", "Stupne", "JeMraz()", "Stupne < 0", "JeMraz()", lambda f, a: f < 0),
          ("Ziak", "z", "Body", "Presiel(int hranica)", "Body >= hranica", "Presiel({a})", lambda f, a: f >= a)]
    def bool_method():
        cname, v, f, header, cond, call, fn = R.choice(BM)
        if f == "Vek":
            fv = R.choice([17, 18, 19, R.randint(5, 40)]); a = None
        elif f == "Stupne":
            fv = R.choice([-1, 0, 1, R.randint(-10, 10)]); a = None
        else:
            fv = R.randint(20, 100); a = R.choice([fv, fv + 1, fv - 1, R.randint(10, 100)])
        res = fn(fv, a)
        l1, l2 = R.sample("ANYB", 2)
        c = call.format(a=a)
        code = prog([f"{cname} {v} = new {cname}();", f"{v}.{f} = {fv};", f"if ({v}.{c})", f"    {W(l1)}", "else", f"    {W(l2)}"],
                    cls(cname, [f"public int {f};"], [method(f"public bool {header}", [f"return {cond};"])]))
        correct = l1 if res else l2
        sk, en = text_answers([code_ans(correct), code_ans(l2 if res else l1), code_ans(l1 + l2), NOTHING])
        return b.add("cl-bool-method", 2, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en,
                     sk_expl=f"`{v}.{c}` vráti `{bstr(res)}` (`{cond}` pre {f} = {fv}), preto sa vypíše `{correct}`.",
                     en_expl=f"`{v}.{c}` returns `{bstr(res)}` (`{cond}` for {f} = {fv}), so `{correct}` is printed.",
                     verify={"type": "output"})
    fill(b, "cl-bool-method", 25, bool_method)

    def counter_loop():
        n1, n2 = R.randint(2, 6), R.randint(0, 4); k = R.choice([1, 1, 2, 5])
        two = n2 > 0
        body = "Pocet = Pocet + 1;" if k == 1 else f"Pocet = Pocet + {k};"
        main = ["Pocitadlo a = new Pocitadlo();"] + (["Pocitadlo b = new Pocitadlo();"] if two else []) + [f"for (int i = 0; i < {n1}; i++)", "    a.Klik();"]
        if two:
            main += [f"for (int i = 0; i < {n2}; i++)", "    b.Klik();"]
        ask = R.choice(["a", "b"]) if two else "a"
        main.append(f"int v = {ask}.Pocet;")
        v = (n1 if ask == "a" else n2) * k
        wrong = pick_wrong(v, [(n1 + n2) * k, v + k, v - k if v else 1, n1 if k != 1 else n1 + 1])
        code = prog(main, cls("Pocitadlo", ["public int Pocet;"], [method("public void Klik()", [body])]))
        return b.add("cl-counter-loop", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"`{ask}.Klik()` sa zavolá {n1 if ask == 'a' else n2}-krát" + (" – druhý objekt má vlastné počítadlo." if two else "."),
                     en_expl=f"`{ask}.Klik()` is called {n1 if ask == 'a' else n2} times" + (" – the other object has its own counter." if two else "."),
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-counter-loop", 25, counter_loop)

    def param_and_field():
        form = R.choice(["zvacsi", "posun"])
        if form == "zvacsi":
            s0 = R.randint(1, 6); ks = [R.randint(2, 3) for _ in range(R.randint(1, 3))]
            cur = s0; steps = []
            for k in ks:
                cur *= k; steps.append(str(cur))
            code = prog(["Stvorec s = new Stvorec();", f"s.Strana = {s0};"] + [f"s.Zvacsi({k});" for k in ks] + ["int v = s.Strana;"],
                        cls("Stvorec", ["public int Strana;"], [method("public void Zvacsi(int k)", ["Strana = Strana * k;"])]))
            wrong = [s0 + sum(ks), ks[-1], int(steps[-2]) if len(steps) > 1 else s0]
        else:
            x0 = R.randint(0, 10); ds = [R.randint(-5, 8) for _ in range(R.randint(2, 3))]
            cur = x0; steps = []
            for d in ds:
                cur += d; steps.append(str(cur))
            code = prog(["Bod b = new Bod();", f"b.X = {x0};"] + [f"b.Posun({d});" for d in ds] + ["int v = b.X;"],
                        cls("Bod", ["public int X;"], [method("public void Posun(int dx)", ["X = X + dx;"])]))
            wrong = [ds[-1], x0, int(steps[-2]) if len(steps) > 1 else x0 - 1]
        wrong = pick_wrong(cur, wrong)
        return b.add("cl-param-and-field", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(cur)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Metóda kombinuje parameter s atribútom: {' → '.join(steps)}.", en_expl=f"The method combines the parameter with the field: {' → '.join(steps)}.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-param-and-field", 25, param_and_field)

    def text_method():
        m, vek = R.choice(NAMES), R.randint(1, 15)
        form = R.choice([('Meno + " (" + Vek + ")"', f'"{m} ({vek})"', [f'"{m}({vek})"', '"Meno (Vek)"', f'"{vek} ({m})"']),
                         ('Meno + ": " + Vek + " r."', f'"{m}: {vek} r."', [f'"{m}:{vek} r."', '"Meno: Vek r."', f'"{m}: {vek}"']),
                         ('"Pes " + Meno', f'"Pes {m}"', [f'"Pes{m}"', '"Pes Meno"', f'"{m}"'])])
        expr, v, wrong = form
        code = prog(["Pes p = new Pes();", f'p.Meno = "{m}";', f"p.Vek = {vek};", "string s = p.Popis();"],
                    cls("Pes", ["public string Meno;", "public int Vek;"], [method("public string Popis()", [f"return {expr};"])]))
        return b.add("cl-text-method", 2, code=code, sk_body=val_q("s")[0], en_body=val_q("s")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Metóda spojí hodnoty atribútov (nie ich názvy) do textu: `{v}`.", en_expl=f"The method joins the field values (not their names) into text: `{v}`.",
                     verify={"type": "value", "expr": "s"})
    fill(b, "cl-text-method", 25, text_method)

    def list_field():
        grades = [R.randint(1, 5) for _ in range(R.randint(2, 4))]
        kind = R.choice(["pocet", "sucet", "najlepsia"])
        meth = {"pocet": method("public int Pocet()", ["return znamky.Count;"]),
                "sucet": method("public int Sucet()", ["int s = 0;", "for (int i = 0; i < znamky.Count; i++)", "    s = s + znamky[i];", "return s;"]),
                "najlepsia": method("public int Najlepsia()", ["int m = znamky[0];", "for (int i = 1; i < znamky.Count; i++)", "{", "    if (znamky[i] < m)", "        m = znamky[i];", "}", "return m;"])}[kind]
        call = {"pocet": "Pocet", "sucet": "Sucet", "najlepsia": "Najlepsia"}[kind]
        v = {"pocet": len(grades), "sucet": sum(grades), "najlepsia": min(grades)}[kind]
        wrong = pick_wrong(v, [grades[-1], max(grades), len(grades) - 1, sum(grades), 0])
        code = prog(["Ziak z = new Ziak();"] + [f"z.Pridaj({g});" for g in grades] + [f"int v = z.{call}();"],
                    cls("Ziak", ["private List<int> znamky = new List<int>();"], [method("public void Pridaj(int z)", ["znamky.Add(z);"]), meth]))
        return b.add("cl-list-field", 2, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Každé `Pridaj` vloží známku do zoznamu objektu ({', '.join(map(str, grades))}); `{call}()` vráti {v}." + (" Najlepšia známka je najmenšie číslo." if kind == "najlepsia" else ""),
                     en_expl=f"Each `Pridaj` adds a grade to the object's list ({', '.join(map(str, grades))}); `{call}()` returns {v}." + (" The best grade is the smallest number." if kind == "najlepsia" else ""),
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-list-field", 25, list_field)

    # =================================================================== HARD
    def reference_copy():
        cname, f = R.choice([("Bod", "X"), ("Ziak", "Body"), ("Ucet", "Zostatok"), ("Hrac", "Zivoty")])
        x, y = R.randint(1, 20), R.randint(21, 40)
        real = R.random() < 0.33
        if real:
            main = [f"{cname} a = new {cname}();", f"a.{f} = {x};", f"{cname} b = new {cname}();", f"b.{f} = a.{f};", f"b.{f} = {y};", f"int v = a.{f};"]; v = x
            esk, een = "`b` je nový objekt, do ktorého sa skopírovala iba hodnota – zmena `b` objekt `a` nezmení.", "`b` is a new object that only got a copy of the value – changing `b` doesn't change `a`."
        else:
            main = [f"{cname} a = new {cname}();", f"a.{f} = {x};", f"{cname} b = a;", f"b.{f} = {y};", f"int v = a.{f};"]; v = y
            esk, een = "`b = a` nevytvorí nový objekt – obe premenné ukazujú na ten istý, takže zmena cez `b` je viditeľná aj cez `a`.", "`b = a` doesn't create a new object – both variables point to the same one, so the change through `b` shows through `a` too."
        wrong = pick_wrong(v, [x if v == y else y, x + y, 0])
        return b.add("cl-reference-copy", 3, code=prog(main, cls(cname, [f"public int {f};"])), sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-reference-copy", 25, reference_copy)

    def param_shadows():
        cname, f = R.choice([("Bod", "X"), ("Ziak", "Body"), ("Auto", "Rychlost"), ("Hrac", "Skore")])
        x = R.randint(2, 30); start = R.choice([None, R.randint(1, 9)])
        works = R.random() < 0.33
        pname = f"nove{f}" if works else f
        main = [f"{cname} o = new {cname}();"] + ([f"o.{f} = {start};"] if start else []) + [f"o.Nastav{f}({x});", f"int v = o.{f};"]
        code = prog(main, cls(cname, [f"public int {f};"], [method(f"public void Nastav{f}(int {pname})", [f"{f} = {pname};"])]))
        v = x if works else (start or 0)
        sk, en = text_answers([code_ans(v), code_ans(x if not works else (start or 0)), code_ans(2 * x if v != 2 * x else x + 1), COMPILE])
        if len(set(sk)) < 4:
            return False
        return b.add("cl-param-shadows-field", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1], answers=sk, en_answers=en,
                     sk_expl=(f"Parameter sa volá inak ako atribút, takže `{f} = {pname};` uloží hodnotu do atribútu." if works
                              else f"V metóde `{f}` znamená parameter, nie atribút – `{f} = {f};` priradí parameter sám sebe a atribút sa nezmení."),
                     en_expl=(f"The parameter has a different name, so `{f} = {pname};` stores the value in the field." if works
                              else f"Inside the method `{f}` means the parameter, not the field – `{f} = {f};` assigns the parameter to itself and the field doesn't change."),
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-param-shadows-field", 25, param_shadows)

    def null_object():
        cname, f, v, vals = R.choice([("Pes", "Meno", "p", NAMES), ("Macka", "Meno", "m", ["Micka", "Tom", "Luna", "Kitty"]),
                                      ("Auto", "Znacka", "a", ["Škoda", "Kia", "Tesla", "Fiat"]), ("Kniha", "Nazov", "k", ["Hobit", "Dune", "Matilda", "Momo"])])
        m = R.choice(vals); form = R.choice(["null", "null_set", "after", "ok"])
        if form in ("null", "null_set"):
            main = [f"{cname} {v} = null;"] + ([f'{v}.{f} = "{m}";'] if form == "null_set" else []) + [f"Console.Write({v}.{f});"]
            sk, en = text_answers([NULLCRASH, NOTHING, code_ans(m) if form == "null_set" else code_ans("null"), COMPILE])
            esk, een = f"Premenná `{v}` neukazuje na žiadny objekt (`null`), preto prvý prístup k atribútu spôsobí pád.", f"`{v}` doesn't point to any object (`null`), so the first access to a field crashes."
            verify = {"type": "exception", "name": "NullReferenceException", "stdout": ""}
        elif form == "after":
            main = [f"{cname} {v} = new {cname}();", f'{v}.{f} = "{m}";', f"Console.Write({v}.{f});", f"{v} = null;", f"Console.Write({v}.{f});"]
            sk, en = text_answers([(f"`{m}` a potom pád (NullReferenceException)", f"`{m}` then a crash (NullReferenceException)"), code_ans(m + m), code_ans(m), NULLCRASH])
            esk, een = f"Prvý výpis prebehne, potom `{v} = null` – ďalší prístup k `{v}.{f}` spadne.", f"The first print works, then `{v} = null` – the next access to `{v}.{f}` crashes."
            verify = {"type": "exception", "name": "NullReferenceException", "stdout": m}
        else:
            main = [f"{cname} {v} = null;", f"{v} = new {cname}();", f'{v}.{f} = "{m}";', f"Console.Write({v}.{f});"]
            sk, en = text_answers([code_ans(m), NULLCRASH, NOTHING, code_ans("null")])
            esk, een = f"`{v}` najprv nemá objekt, ale pred použitím sa doň priradí `new {cname}()` – nič nespadne.", f"`{v}` has no object at first, but `new {cname}()` is assigned before it's used – nothing crashes."
            verify = {"type": "output"}
        code = prog(main, cls(cname, [f"public string {f};"]))
        return b.add("cl-null-object", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1], answers=sk, en_answers=en, sk_expl=esk, en_expl=een, verify=verify)
    fill(b, "cl-null-object", 25, null_object, tries=5000)

    def compare_objects():
        cname, f = R.choice([("Bod", "X"), ("Ziak", "Body"), ("Kocka", "Strana")]); x = R.randint(1, 9)
        form = R.choice(["sep", "sep", "ref", "field"])
        main = [f"{cname} a = new {cname}();", f"a.{f} = {x};"]
        if form == "sep":
            main += [f"{cname} b = new {cname}();", f"b.{f} = {x};", "bool v = a == b;"]; v = False
            esk, een = "`==` pri objektoch porovnáva, či ide o ten istý objekt – `a` a `b` sú dva rôzne objekty, aj keď majú rovnaké hodnoty.", "`==` on objects checks whether it's the same object – `a` and `b` are two different objects, even with equal values."
        elif form == "ref":
            main += [f"{cname} b = a;", "bool v = a == b;"]; v = True
            esk, een = "`b = a` neskopíruje objekt – obe premenné ukazujú na ten istý, preto `==` vráti `true`.", "`b = a` doesn't copy the object – both point to the same one, so `==` returns `true`."
        else:
            main += [f"{cname} b = new {cname}();", f"b.{f} = {x};", f"bool v = a.{f} == b.{f};"]; v = True
            esk, een = f"Porovnávajú sa hodnoty atribútov ({x} a {x}), nie objekty.", f"The field values ({x} and {x}) are compared, not the objects."
        return b.add("cl-compare-objects", 3, code=prog(main, cls(cname, [f"public int {f};"])), sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=bool_answers(v), sk_expl=esk, en_expl=een, verify={"type": "value", "expr": "v", "expected": bstr(v)})
    fill(b, "cl-compare-objects", 25, compare_objects)

    def list_shared():
        x, y = R.randint(1, 20), R.randint(21, 40); twice = R.random() < 0.3
        main = ["List<Ziak> trieda = new List<Ziak>();", "Ziak z = new Ziak();", f"z.Body = {x};", "trieda.Add(z);"]
        if twice:
            main += ["trieda.Add(z);", f"trieda[0].Body = {y};", "int v = trieda[1].Body;"]; v = y
            esk, een = "Ten istý objekt je v zozname dvakrát – `trieda[0]` a `trieda[1]` je jeden a ten istý žiak.", "The same object is in the list twice – `trieda[0]` and `trieda[1]` are one and the same student."
        else:
            main += [f"z.Body = {y};", "int v = trieda[0].Body;"]; v = y
            esk, een = "Zoznam neobsahuje kópiu, ale ten istý objekt – zmena cez `z` je viditeľná aj v zozname.", "The list doesn't hold a copy but the same object – the change through `z` shows in the list too."
        wrong = pick_wrong(v, [x, x + y, 0])
        return b.add("cl-list-shared-object", 3, code=prog(main, cls("Ziak", ["public int Body;"])), sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-list-shared-object", 25, list_shared)

    def param_reassign():
        m1, m2 = R.sample(NAMES, 2); form = R.choice(["reassign", "reassign", "field", "both"])
        if form == "reassign":
            body = ["p = new Pes();", f'p.Meno = "{m2}";']; v = m1
            esk, een = "`p = new Pes()` presmeruje iba parameter na nový objekt; pôvodný pes sa nezmení.", "`p = new Pes()` only points the parameter to a new object; the original dog doesn't change."
        elif form == "field":
            body = [f'p.Meno = "{m2}";']; v = m2
            esk, een = "Funkcia mení atribút toho istého objektu, ktorý jej poslal hlavný program.", "The function changes a field of the very object the main program passed in."
        else:
            body = [f'p.Meno = "{m2}";', "p = new Pes();", 'p.Meno = "Nikto";']; v = m2
            esk, een = f"Najprv sa zmení pôvodný pes na \"{m2}\"; až potom sa parameter presmeruje na nový objekt, ktorý pôvodného psa neovplyvní.", f"First the original dog becomes \"{m2}\"; only then is the parameter pointed to a new object, which doesn't affect the original."
        bl = "\n".join("    " + l for l in body)
        code = f'Pes pes = new Pes();\npes.Meno = "{m1}";\nZmen(pes);\nstring v = pes.Meno;\n\nvoid Zmen(Pes p)\n{{\n{bl}\n}}\n\n' + cls("Pes", ["public string Meno;"])
        ans = [f'"{v}"', f'"{m2}"' if v == m1 else f'"{m1}"', "null", '"Nikto"' if form == "both" else f'"{m1}{m2}"']
        return b.add("cl-param-reassign", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1], answers=[code_ans(a) for a in ans],
                     sk_expl=esk, en_expl=een, verify={"type": "value", "expr": "v"})
    fill(b, "cl-param-reassign", 25, param_reassign)

    def output_order():
        la, lb = R.sample("ABHMP", 2)
        pat = [R.choice(["a1", "b1", "a2"]) for _ in range(R.randint(3, 4))]
        a_m = method("public void Hraj()", [W(la)]); b_m = method("public void Hraj()", [W(lb)])
        cross = R.random() < 0.4
        main = ["Hrac a = new Hrac();", "Pes b = new Pes();"]
        out = ""
        for p in pat:
            if p.startswith("a"):
                main.append("a.Hraj();"); out += la
            else:
                main.append("b.Hraj();"); out += lb
        classes = [cls("Hrac", [], [a_m]), cls("Pes", [], [b_m])]
        if cross:
            main.append("a.Zavolaj(b);"); out += la + lb
            classes[0] = cls("Hrac", [], [a_m, method("public void Zavolaj(Pes p)", [W(la), "p.Hraj();"])])
        if len(set(out)) < 2:
            return False
        decl_order = la * out.count(la) + lb * out.count(lb)
        wrong = pick_wrong(out, [decl_order, out[::-1], out[:-1], out.replace(la, "#").replace(lb, la).replace("#", lb)])
        if not wrong:
            return False
        code = prog(main, *[c.replace("{\n\n", "{\n") for c in classes])
        return b.add("cl-output-order", 3, code=code, sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=[code_ans(out)] + [code_ans(w) for w in wrong],
                     sk_expl="Kód sa vykonáva podľa poradia volaní v hlavnom programe, nie podľa poradia tried v súbore.",
                     en_expl="Code runs in the order of the calls in the main program, not the order of the classes in the file.",
                     verify={"type": "output"})
    fill(b, "cl-output-order", 25, output_order)

    def object_in_object():
        tn, un = R.sample(["Lambda", "Ró", "Alfa", "Beta"], 1)[0], R.choice(["Novák", "Horváth", "Kováčová", "Szabó"])
        un2 = R.choice([x for x in ["Benko", "Lukáč", "Mráz"]])
        form = R.choice(["plain", "changed", "missing"])
        main = ["Ucitel u = new Ucitel();", f'u.Meno = "{un}";', "Trieda t = new Trieda();", f't.Nazov = "{tn}";']
        if form != "missing":
            main.append("t.Triedny = u;")
        if form == "changed":
            main.append(f'u.Meno = "{un2}";')
        if form == "missing":
            main.append("Console.Write(t.Triedny.Meno);")
            sk, en = text_answers([NULLCRASH, code_ans(un), code_ans(tn), NOTHING])
            esk, een = "`t.Triedny` sa nikdy nenastavil, je `null` – prístup k jeho `Meno` spadne.", "`t.Triedny` was never set, it's `null` – accessing its `Meno` crashes."
            verify = {"type": "exception", "name": "NullReferenceException", "stdout": ""}
            body = OUT_Q
        else:
            main.append("string v = t.Triedny.Meno;")
            v = un2 if form == "changed" else un
            sk, en = text_answers([code_ans(f'"{v}"'), code_ans(f'"{un if v == un2 else un2}"'), code_ans(f'"{tn}"'), NULLCRASH])
            esk, een = ("`t.Triedny` ukazuje na ten istý objekt ako `u`, takže zmena `u.Meno` je viditeľná aj cez `t.Triedny.Meno`." if form == "changed"
                        else "`t.Triedny.Meno` – najprv objekt `t`, z neho učiteľ `Triedny`, z neho atribút `Meno`."), (
                        "`t.Triedny` points to the same object as `u`, so changing `u.Meno` shows through `t.Triedny.Meno`." if form == "changed"
                        else "`t.Triedny.Meno` – first the object `t`, then its teacher `Triedny`, then the field `Meno`.")
            verify = {"type": "value", "expr": "v"}
            body = val_q("v")
        code = prog(main, cls("Ucitel", ["public string Meno;"]), cls("Trieda", ["public string Nazov;", "public Ucitel Triedny;"]))
        return b.add("cl-object-in-object", 3, code=code, sk_body=body[0], en_body=body[1], answers=sk, en_answers=en, sk_expl=esk, en_expl=een, verify=verify)
    fill(b, "cl-object-in-object", 25, object_in_object, tries=5000)

    def array_of_objects():
        n = R.randint(2, 4); m = R.choice(NAMES); i = R.randrange(n)
        if R.random() < 0.5:
            main = [f"Pes[] psy = new Pes[{n}];", f'psy[{i}].Meno = "{m}";', f"Console.Write(psy[{i}].Meno);"]
            sk, en = text_answers([NULLCRASH, code_ans(m), NOTHING, COMPILE])
            esk, een = f"`new Pes[{n}]` vytvorí pole s {n} prázdnymi miestami (`null`), nie {n} psov – `psy[{i}]` ešte nie je objekt.", f"`new Pes[{n}]` creates an array with {n} empty slots (`null`), not {n} dogs – `psy[{i}]` isn't an object yet."
            verify = {"type": "exception", "name": "NullReferenceException", "stdout": ""}
        else:
            main = [f"Pes[] psy = new Pes[{n}];", f"psy[{i}] = new Pes();", f'psy[{i}].Meno = "{m}";', f"Console.Write(psy[{i}].Meno);"]
            sk, en = text_answers([code_ans(m), NULLCRASH, NOTHING, code_ans(m * n)])
            esk, een = f"Najprv sa do `psy[{i}]` vloží nový objekt, až potom sa mu nastaví meno – nič nespadne.", f"First a new object is put into `psy[{i}]`, then its name is set – nothing crashes."
            verify = {"type": "output"}
        return b.add("cl-array-of-objects", 3, code=prog(main, cls("Pes", ["public string Meno;"])), sk_body=OUT_Q[0], en_body=OUT_Q[1],
                     answers=sk, en_answers=en, sk_expl=esk, en_expl=een, verify=verify)
    fill(b, "cl-array-of-objects", 25, array_of_objects)

    def field_initializer():
        init = R.randint(2, 5); ops = R.sample([("Zasah", "Zivoty = Zivoty - 1;", lambda v: v - 1), ("Bonus", "Zivoty = Zivoty * 2;", lambda v: v * 2),
                                                 ("Liecba", "Zivoty = Zivoty + 3;", lambda v: v + 3)], 2)
        calls = [R.choice(ops) for _ in range(R.randint(2, 3))]
        cur = init; steps = [str(init)]
        for c in calls:
            cur = c[2](cur); steps.append(str(cur))
        ask_new = R.random() < 0.35
        main = ["Hrac h = new Hrac();"] + [f"h.{c[0]}();" for c in calls]
        if ask_new:
            main += ["Hrac h2 = new Hrac();", "int v = h2.Zivoty;"]; v = init
            esk, een = f"`h2` je nový objekt – začína s počiatočnou hodnotou {init}; zmeny `h` ho neovplyvnia.", f"`h2` is a new object – it starts with the initial value {init}; changes to `h` don't affect it."
        else:
            main += ["int v = h.Zivoty;"]; v = cur
            esk, een = f"Objekt začína so `Zivoty = {init}`; potom: {' → '.join(steps)}.", f"The object starts with `Zivoty = {init}`; then: {' → '.join(steps)}."
        wrong = pick_wrong(v, [cur if ask_new else init, 0, steps[-2] and int(steps[-2]), cur + 1])
        if not wrong:
            return False
        methods = [method(f"public void {o[0]}()", [o[1]]) for o in ops]
        code = prog(main, cls("Hrac", [f"public int Zivoty = {init};"], methods))
        return b.add("cl-field-initializer", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(v)] + [code_ans(w) for w in wrong], sk_expl=esk, en_expl=een,
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-field-initializer", 25, field_initializer)

    UCET2 = cls("Ucet", ["public int Zostatok;"], [method("public void Vloz(int suma)", ["Zostatok = Zostatok + suma;"]),
                                                    method("public void Vyber(int suma)", ["if (suma <= Zostatok)", "    Zostatok = Zostatok - suma;"])])
    def state_series():
        cur, naive, calls, steps, refused = 0, 0, [], [], []
        for _ in range(R.randint(4, 6)):
            if R.random() < 0.5:
                x = R.choice([10, 20, 30, 50]); cur += x; naive += x; calls.append(f"u.Vloz({x});")
            else:
                x = R.choice([20, 30, 40, 60, 80])
                naive -= x
                if x <= cur:
                    cur -= x
                else:
                    refused.append(x)
                calls.append(f"u.Vyber({x});")
            steps.append(str(cur))
        if not refused or not any("Vloz" in c for c in calls) or cur == 0 and R.random() < 0.7:
            return False
        wrong = pick_wrong(cur, [naive, int(steps[-2]), 0, cur + refused[0]])
        if not wrong:
            return False
        code = prog(["Ucet u = new Ucet();"] + calls + ["int v = u.Zostatok;"], UCET2)
        return b.add("cl-state-series", 3, code=code, sk_body=val_q("v")[0], en_body=val_q("v")[1],
                     answers=[code_ans(cur)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Po volaniach: {' → '.join(steps)} – výber {', '.join(map(str, refused))} sa nevykoná, lebo na účte nie je dosť peňazí.",
                     en_expl=f"After the calls: {' → '.join(steps)} – the withdrawal of {', '.join(map(str, refused))} is refused because there isn't enough money.",
                     verify={"type": "value", "expr": "v"})
    fill(b, "cl-state-series", 25, state_series)

    def two_objects():
        a0, b0 = R.choice([50, 100, 80, 120]), R.choice([0, 20, 50, 30])
        transfers = [(R.choice(["a", "b"]), R.choice([10, 20, 30])) for _ in range(R.randint(1, 3))]
        A, B = a0, b0; steps = []
        for src, x in transfers:
            if src == "a":
                A -= x; B += x
            else:
                B -= x; A += x
            steps.append(f"({A}, {B})")
        c = f"a.Zostatok = {A}, b.Zostatok = {B}"
        firstonly = (a0 - sum(x for s_, x in transfers if s_ == "a") + sum(x for s_, x in transfers if s_ == "b"), b0)
        wrong = pick_wrong(c, [f"a.Zostatok = {B}, b.Zostatok = {A}", f"a.Zostatok = {firstonly[0]}, b.Zostatok = {firstonly[1]}", f"a.Zostatok = {a0}, b.Zostatok = {b0}",
                               f"a.Zostatok = {A}, b.Zostatok = {b0}"])
        if not wrong:
            return False
        main = ["Ucet a = new Ucet();", "Ucet b = new Ucet();", f"a.Zostatok = {a0};", f"b.Zostatok = {b0};"] + [f"{s_}.Prevod({'b' if s_ == 'a' else 'a'}, {x});" for s_, x in transfers]
        code = prog(main, cls("Ucet", ["public int Zostatok;"], [method("public void Prevod(Ucet ciel, int suma)", ["Zostatok = Zostatok - suma;", "ciel.Zostatok = ciel.Zostatok + suma;"])]))
        return b.add("cl-two-objects-interact", 3, code=code,
                     sk_body="{code}\nAké hodnoty budú mať `a.Zostatok` a `b.Zostatok`?", en_body="{code}\nWhat values will `a.Zostatok` and `b.Zostatok` have?",
                     answers=[code_ans(c)] + [code_ans(w) for w in wrong],
                     sk_expl=f"Metóda mení vlastný objekt aj objekt v parametri; (a, b) po prevodoch: {', '.join(steps)}.",
                     en_expl=f"The method changes its own object and the one in the parameter; (a, b) after the transfers: {', '.join(steps)}.",
                     verify={"type": "value", "expr": '$"a.Zostatok = {a.Zostatok}, b.Zostatok = {b.Zostatok}"'})
    fill(b, "cl-two-objects-interact", 25, two_objects)
    return b


if __name__ == "__main__":
    main().write()
