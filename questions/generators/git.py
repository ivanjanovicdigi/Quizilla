"""Generator for topic git – concept questions only (students use Git from the IDE). All difficulty 1."""
import random
from common import Batch, fill

R = random.Random(20261029)
DATE = "2026-10-22"

TERMS = {
    "repozitár": ("repository", ("priečinok projektu, ktorého históriu zmien Git sleduje", "a project folder whose change history Git tracks")),
    "commit": ("commit", ("uložený stav zmien so správou – zatiaľ iba na mojom počítači", "a saved state of changes with a message – only on my computer so far")),
    "push": ("push", ("pošle moje commity na server (napr. GitHub)", "sends my commits to the server (e.g. GitHub)")),
    "pull": ("pull", ("stiahne nové commity zo servera a zapracuje ich do mojich súborov", "downloads new commits from the server and brings them into my files")),
    "fetch": ("fetch", ("iba zistí a stiahne, čo je nové na serveri – moje súbory nezmení", "only finds out and downloads what's new on the server – my files don't change")),
    "konflikt": ("conflict", ("dvaja zmenili to isté miesto v súbore a Git nevie sám rozhodnúť", "two people changed the same place in a file and Git can't decide by itself")),
    "`.gitignore`": ("`.gitignore`", ("zoznam súborov a priečinkov, ktoré Git nemá sledovať", "a list of files and folders Git should not track")),
}
FAKES = [("pošle zmeny na GitHub hneď po uložení súboru", "sends changes to GitHub as soon as a file is saved"),
         ("vymaže históriu projektu", "deletes the project history"), ("skontroluje, či sa program dá preložiť", "checks whether the program compiles"),
         ("vytvorí zálohu celého disku", "creates a backup of the whole disk")]


def text(ans):
    return [a[0] for a in ans], [a[1] for a in ans]


def main():
    b = Batch(f"{DATE}_git", "git", DATE)

    def add(template, sk_q, en_q, correct, wrong, sk_e, en_e):
        sk, en = text([correct] + wrong)
        return b.add(template, 1, code=None, sk_body=sk_q, en_body=en_q, answers=sk, en_answers=en,
                     sk_expl=sk_e, en_expl=en_e, verify={"type": "none"})

    # ---- git-term-purpose (20)
    TQ = [("Čo je {t}?", "What is {t}?"), ("Čo robí {t}?", "What does {t} do?"), ("Čo v Gite znamená {t}?", "What does {t} mean in Git?")]
    def term_purpose():
        t = R.choice(list(TERMS)); en_t, mean = TERMS[t]; q = R.choice(TQ)
        if t in ("repozitár", "konflikt", "`.gitignore`", "commit") and q[0].startswith("Čo robí"):
            return False
        pool = [TERMS[o][1] for o in TERMS if o != t]
        R.shuffle(pool)
        wrong = pool[:2] + [R.choice(FAKES)] if R.random() < 0.6 else pool[:3]
        return add("git-term-purpose", q[0].format(t=t), q[1].format(t=en_t), mean, wrong, f"{t}: {mean[0]}.", f"{en_t}: {mean[1]}.")
    fill(b, "git-term-purpose", 20, term_purpose, tries=5000)

    # ---- git-purpose-term (15)
    PT = [(("Ako sa volá krok, ktorý pošle moje commity na server?", "What is the step that sends my commits to the server called?"), "push"),
          (("Ako sa volá krok, ktorý stiahne nové commity zo servera a zapracuje ich do mojich súborov?", "What is the step that downloads new commits and brings them into my files called?"), "pull"),
          (("Ako sa volá krok, ktorý iba zistí, čo je nové na serveri, ale moje súbory nezmení?", "What is the step that only checks what's new on the server without changing my files called?"), "fetch"),
          (("Ako sa volá uložený stav zmien so správou?", "What is a saved state of changes with a message called?"), "commit"),
          (("Ako sa volá priečinok projektu, ktorého históriu Git sleduje?", "What is a project folder whose history Git tracks called?"), "repozitár"),
          (("Ako sa volá situácia, keď dvaja zmenili ten istý riadok a Git nevie, ktorú verziu ponechať?", "What is it called when two people changed the same line and Git can't tell which version to keep?"), "konflikt"),
          (("Ako sa volá súbor so zoznamom súborov, ktoré Git nemá sledovať?", "What is the file listing files Git should not track called?"), "`.gitignore`"),
          (("Čo musím urobiť, aby učiteľ videl môj commit na GitHube?", "What do I have to do so the teacher sees my commit on GitHub?"), "push"),
          (("Čo urobím, keď chcem do svojho projektu dostať zmeny, ktoré spolužiak poslal na server?", "What do I do to get the changes a classmate sent to the server into my project?"), "pull"),
          (("Čo urobím, keď chcem uložiť hotový kus práce s popisom, čo som zmenil?", "What do I do to save a finished piece of work with a description of what I changed?"), "commit")]
    ALL = ["push", "pull", "fetch", "commit", "repozitár", "konflikt", "`.gitignore`"]
    EN = {k: TERMS[k][0] for k in TERMS}
    def purpose_term():
        (sq, eq), t = R.choice(PT)
        look = {"push": ["pull", "commit", "fetch"], "pull": ["push", "fetch", "commit"], "fetch": ["pull", "push", "commit"], "commit": ["push", "pull", "repozitár"],
                "repozitár": ["commit", "`.gitignore`", "konflikt"], "konflikt": ["commit", "fetch", "repozitár"], "`.gitignore`": ["repozitár", "commit", "konflikt"]}[t]
        if R.random() < 0.4:
            look = R.sample([x for x in ALL if x != t], 3)
        return add("git-purpose-term", sq, eq, (t, EN[t]), [(x, EN[x]) for x in look], f"To je {t}: {TERMS[t][1][0]}.", f"That's {EN[t]}: {TERMS[t][1][1]}.")
    fill(b, "git-purpose-term", 15, purpose_term, tries=5000)

    def bank(template, items, n=10):
        """items: (sk_q, en_q, correct, [wrong...≥3], sk_expl, en_expl)"""
        SUF = [("", ""), (" Vyber jednu možnosť.", " Pick one option."), (" Vyber správnu odpoveď.", " Choose the correct answer.")]
        def make():
            sq, eq, c, ws, se, ee = R.choice(items)
            ss, es = R.choice(SUF)
            return add(template, sq + ss, eq + es, c, R.sample(ws, 3), se, ee)
        fill(b, template, n, make, tries=5000)

    G = ("Git je nástroj na počítači, ktorý sleduje históriu zmien; GitHub je služba na internete, kam repozitár posielam a kde ho zdieľam.",
         "Git is a tool on the computer that tracks the history of changes; GitHub is an online service where I send and share the repository.")
    bank("git-vs-github", [
        ("Čo je GitHub?", "What is GitHub?", ("služba na internete, kde sú uložené a zdieľané repozitáre", "an online service where repositories are stored and shared"),
         [("nástroj na počítači, ktorý sleduje históriu zmien", "a tool on the computer that tracks the history of changes"), ("iný názov pre Git", "another name for Git"),
          ("programovací jazyk", "a programming language"), ("editor na písanie kódu", "a code editor")], *G),
        ("Čo je Git?", "What is Git?", ("nástroj, ktorý na mojom počítači sleduje históriu zmien v projekte", "a tool that tracks the change history of a project on my computer"),
         [("webová stránka na zdieľanie kódu", "a website for sharing code"), ("programovací jazyk", "a programming language"), ("cloudové úložisko ako Disk Google", "cloud storage like Google Drive"),
          ("iný názov pre GitHub", "another name for GitHub")], *G),
        ("Potrebujem internet na to, aby som urobil commit?", "Do I need the internet to make a commit?", ("nie – commit sa uloží na mojom počítači", "no – a commit is saved on my computer"),
         [("áno – commit sa hneď posiela na GitHub", "yes – a commit is sent to GitHub right away"), ("áno, ale iba pri prvom commite", "yes, but only for the first commit"),
          ("nie, lebo commit sa vôbec neukladá", "no, because a commit isn't saved at all")], *G),
        ("Potrebujem internet na push?", "Do I need the internet for a push?", ("áno – push posiela commity na server", "yes – push sends commits to the server"),
         [("nie – push sa robí iba na mojom počítači", "no – push happens only on my computer"), ("nie, ak som už urobil commit", "no, if I've already committed"),
          ("iba ak mám otvorený prehliadač", "only if a browser is open")], *G),
        ("Ktoré tvrdenie o Gite a GitHube je pravdivé?", "Which statement about Git and GitHub is true?", ("Git sa dá používať aj bez GitHubu", "Git can be used without GitHub too"),
         [("Git a GitHub sú to isté", "Git and GitHub are the same thing"), ("bez GitHubu sa nedá urobiť commit", "you can't commit without GitHub"),
          ("GitHub beží iba na mojom počítači", "GitHub runs only on my computer")], *G),
        ("Kde je uložený môj commit, kým neurobím push?", "Where is my commit stored before I push?", ("iba v repozitári na mojom počítači", "only in the repository on my computer"),
         [("na GitHube", "on GitHub"), ("u učiteľa", "on the teacher's computer"), ("nikde – commit sa uloží až po pushi", "nowhere – a commit is saved only after a push")], *G),
    ])

    C = ("Commit je uložený stav projektu s popisom – zatiaľ iba lokálne.", "A commit is a saved state of the project with a description – only local so far.")
    bank("git-commit-meaning", [
        ("Čo je commit?", "What is a commit?", ("uložený stav (snímka) zmien s popisom", "a saved state (snapshot) of changes with a description"),
         [("odoslanie zmien na GitHub", "sending changes to GitHub"), ("uloženie súboru ako Ctrl+S", "saving a file like Ctrl+S"), ("záloha celého disku", "a backup of the whole disk")], *C),
        ("Na čo slúži správa commitu?", "What is a commit message for?", ("stručne opisuje, čo sa v commite zmenilo", "it briefly describes what changed in the commit"),
         [("je to heslo k repozitáru", "it's the password to the repository"), ("určuje, kam sa commit pošle", "it decides where the commit is sent"), ("nemá žiadny význam", "it has no purpose")], *C),
        ("Čo sa stane, keď urobím commit?", "What happens when I make a commit?", ("zmeny sa uložia do histórie repozitára na mojom počítači", "the changes are saved into the repository history on my computer"),
         [("zmeny sa hneď objavia na GitHube", "the changes appear on GitHub right away"), ("stiahnu sa zmeny spolužiakov", "classmates' changes are downloaded"), ("vymaže sa predchádzajúca verzia", "the previous version is deleted")], *C),
        ("Čo obsahuje commit?", "What does a commit contain?", ("zmeny v súboroch, správu, autora a čas", "changes to files, a message, the author and the time"),
         [("iba správu", "only the message"), ("iba názov projektu", "only the project name"), ("celý počítač", "the whole computer")], *C),
        ("Spravil som commit. Vidí ho už učiteľ na GitHube?", "I made a commit. Can the teacher see it on GitHub yet?", ("nie, najprv musím urobiť push", "no, I have to push first"),
         [("áno, commit sa posiela automaticky", "yes, a commit is sent automatically"), ("áno, ak som pripojený na internet", "yes, if I'm online"), ("nie, učiteľ musí urobiť commit", "no, the teacher must commit")], *C),
        ("Je commit to isté ako uloženie súboru (Ctrl+S)?", "Is a commit the same as saving a file (Ctrl+S)?", ("nie – commit uloží stav do histórie Gitu so správou", "no – a commit saves a state into Git's history with a message"),
         [("áno, je to to isté", "yes, it's the same"), ("áno, ale commit je rýchlejší", "yes, but a commit is faster"), ("nie – commit súbor vymaže", "no – a commit deletes the file")], *C),
    ])

    R_ = ("Na server sa dostane iba to, čo som commitol a potom pushol.", "Only what I committed and then pushed reaches the server.")
    bank("git-whats-on-remote", [
        ("Upravil som súbor, dal som commit A a push. Potom som urobil commit B, ale push som už nedal. Čo je teraz na GitHube?",
         "I edited a file, made commit A and pushed. Then I made commit B but didn't push. What is on GitHub now?",
         ("iba commit A", "only commit A"), [("commity A aj B", "commits A and B"), ("nič", "nothing"), ("iba commit B", "only commit B")], *R_),
        ("Upravil som tri súbory, ale nedal som commit ani push. Čo je na GitHube?", "I edited three files but didn't commit or push. What is on GitHub?",
         ("stará verzia, bez mojich zmien", "the old version, without my changes"), [("všetky tri zmenené súbory", "all three changed files"), ("iba prvý súbor", "only the first file"), ("prázdny repozitár", "an empty repository")], *R_),
        ("Dal som commit A, commit B a potom push. Čo je na GitHube?", "I made commit A, commit B and then pushed. What is on GitHub?",
         ("oba commity A aj B", "both commits A and B"), [("iba commit B", "only commit B"), ("iba commit A", "only commit A"), ("nič, push posiela iba posledný súbor", "nothing, push sends only the last file")], *R_),
        ("Dal som commit a push, potom som ešte upravil súbor bez commitu. Čo je na GitHube?", "I committed and pushed, then edited a file without committing. What is on GitHub?",
         ("verzia z posledného pushnutého commitu", "the version from the last pushed commit"), [("aj posledná úprava", "the last edit too"), ("nič", "nothing"), ("iba posledná úprava", "only the last edit")], *R_),
        ("Dal som push bez toho, aby som predtým urobil commit. Čo sa pošle na GitHub?", "I pushed without committing first. What is sent to GitHub?",
         ("nič nové – push posiela iba commity", "nothing new – push sends only commits"), [("všetky zmenené súbory", "all changed files"), ("iba uložené súbory", "only saved files"), ("prázdny commit", "an empty commit")], *R_),
        ("Spolužiak pushol commit X. Ja som zatiaľ nič nespravil. Je X na GitHube?", "A classmate pushed commit X. I haven't done anything yet. Is X on GitHub?",
         ("áno, ale u mňa na počítači zatiaľ nie je", "yes, but it isn't on my computer yet"), [("nie, kým neurobím pull", "no, not until I pull"), ("nie, push nič neposiela", "no, push doesn't send anything"), ("áno, aj u mňa sa objavil sám", "yes, and it appeared on my computer by itself")], *R_),
    ])

    O = ("Najprv sa zmeny uložia commitom na mojom počítači, až potom ich push pošle na server.", "First the changes are saved with a commit on my computer, then push sends them to the server.")
    bank("git-workflow-order", [
        ("V akom poradí odošlem svoju prácu na GitHub?", "In which order do I send my work to GitHub?", ("commit → push", "commit → push"),
         [("push → commit", "push → commit"), ("iba push", "push only"), ("pull → commit", "pull → commit")], *O),
        ("Čo urobím na začiatku práce, keď spolužiak medzitým niečo zmenil na serveri?", "What do I do when I start working and a classmate has changed something on the server?",
         ("pull", "pull"), [("push", "push"), ("commit", "commit"), ("nič, zmeny sa stiahnu samé", "nothing, the changes download by themselves")],
         "Najprv si pullom stiahnem najnovšie zmeny, až potom pokračujem v práci.", "First I pull the latest changes, then I continue working."),
        ("Ktorý postup je správny pri práci v tíme?", "Which workflow is right when working in a team?", ("pull → úpravy → commit → push", "pull → edits → commit → push"),
         [("push → úpravy → commit → pull", "push → edits → commit → pull"), ("úpravy → push → commit", "edits → push → commit"), ("commit → pull → push → úpravy", "commit → pull → push → edits")],
         "Najprv stiahnem zmeny ostatných, potom pracujem, uložím commit a pošlem ho pushom.", "First I get the others' changes, then work, commit and push."),
        ("Dopísal som úlohu. Čo urobím najprv?", "I finished my assignment. What do I do first?", ("commit", "commit"),
         [("push", "push"), ("fetch", "fetch"), ("vymažem repozitár", "delete the repository")], *O),
        ("Urobil som commit. Čo ďalej, aby to videl učiteľ?", "I made a commit. What next, so the teacher sees it?", ("push", "push"),
         [("ďalší commit", "another commit"), ("fetch", "fetch"), ("nič, učiteľ ho už vidí", "nothing, the teacher already sees it")], *O),
    ])

    PP = ("push = z môjho počítača na server, pull = zo servera k mne.", "push = from my computer to the server, pull = from the server to me.")
    bank("git-push-vs-pull", [
        ("Ktorým smerom ide push?", "Which way does push go?", ("z môjho počítača na server", "from my computer to the server"),
         [("zo servera na môj počítač", "from the server to my computer"), ("z jedného súboru do druhého", "from one file to another"), ("nikam, iba ukladá", "nowhere, it only saves")], *PP),
        ("Ktorým smerom ide pull?", "Which way does pull go?", ("zo servera na môj počítač", "from the server to my computer"),
         [("z môjho počítača na server", "from my computer to the server"), ("od učiteľa k žiakom e-mailom", "from the teacher to students by e-mail"), ("nikam, iba ukladá", "nowhere, it only saves")], *PP),
        ("Učiteľ pridal do repozitára nové zadanie. Ako ho dostanem do svojho projektu?", "The teacher added a new assignment to the repository. How do I get it into my project?",
         ("pull", "pull"), [("push", "push"), ("commit", "commit"), ("fetch – a hotovo", "fetch – and that's it")], *PP),
        ("Chcem, aby učiteľ videl moje riešenie. Čo použijem po commite?", "I want the teacher to see my solution. What do I use after committing?",
         ("push", "push"), [("pull", "pull"), ("fetch", "fetch"), ("ďalší commit", "another commit")], *PP),
        ("Pracujem na dvoch počítačoch. Doma chcem pokračovať v tom, čo som v škole pushol. Čo urobím doma?", "I work on two computers. At home I want to continue what I pushed at school. What do I do at home?",
         ("pull", "pull"), [("push", "push"), ("commit", "commit"), ("nič, zmeny sa objavia samé", "nothing, the changes appear by themselves")], *PP),
    ])

    FP = ("fetch iba zistí, čo je nové; pull to aj zapracuje do mojich súborov.", "fetch only finds out what's new; pull also brings it into my files.")
    bank("git-fetch-vs-pull", [
        ("Aký je rozdiel medzi fetch a pull?", "What is the difference between fetch and pull?", ("fetch iba stiahne informácie o zmenách, pull ich aj zapracuje do mojich súborov", "fetch only downloads information about changes; pull also brings them into my files"),
         [("žiadny, sú to dve mená pre to isté", "none, they're two names for the same thing"), ("fetch posiela zmeny na server, pull ich sťahuje", "fetch sends changes to the server, pull downloads them"),
          ("pull iba zistí zmeny, fetch ich zapracuje", "pull only checks for changes, fetch brings them in")], *FP),
        ("Spravil som fetch. Zmenili sa moje súbory?", "I did a fetch. Did my files change?", ("nie – fetch iba zistí, čo je nové na serveri", "no – fetch only finds out what's new on the server"),
         [("áno, fetch je to isté ako pull", "yes, fetch is the same as pull"), ("áno, ale iba súbory spolužiakov", "yes, but only classmates' files"), ("nie, lebo fetch vymaže zmeny", "no, because fetch deletes changes")], *FP),
        ("Chcem iba zistiť, či spolužiaci niečo pushli, ale zatiaľ nič nemeniť. Čo použijem?", "I only want to find out whether classmates pushed something, without changing anything yet. What do I use?",
         ("fetch", "fetch"), [("pull", "pull"), ("push", "push"), ("commit", "commit")], *FP),
        ("Ktorý krok zmení súbory v mojom projekte podľa servera?", "Which step changes the files in my project according to the server?", ("pull", "pull"),
         [("fetch", "fetch"), ("push", "push"), ("commit", "commit")], *FP),
        ("Pull sa skladá z dvoch krokov. Z ktorých?", "Pull consists of two steps. Which ones?", ("stiahnutie zmien (fetch) a ich zapracovanie do mojich súborov", "downloading the changes (fetch) and bringing them into my files"),
         [("commit a push", "commit and push"), ("push a fetch", "push and fetch"), ("uloženie a vymazanie", "saving and deleting")], *FP),
    ])

    M = ("Dobrá správa stručne a konkrétne povie, čo sa zmenilo – aby sa dala história neskôr čítať.", "A good message briefly and specifically says what changed – so the history can be read later.")
    GOOD = [("Pridaný výpočet priemeru známok", "Add average grade calculation"), ("Opravené delenie nulou vo funkcii Priemer", "Fix division by zero in Priemer"),
            ("Pridaná trieda Ziak s metódou Pozdrav", "Add Ziak class with Pozdrav method"), ("Oprava chyby v cykle pri výpise poľa", "Fix loop bug when printing the array"),
            ("Doplnené testy pre funkciu Max", "Add tests for the Max function"), ("Upravený výpis výsledkov podľa zadania", "Change result output to match the assignment")]
    BAD = [("zmena", "change"), ("asdf", "asdf"), ("oprava", "fix"), ("posledná verzia FINAL2", "final version FINAL2"), ("commit", "commit"), ("hotovo???", "done???"),
           ("aaaa", "aaaa"), ("nefunguje", "doesn't work")]
    def good_message():
        g = R.choice(GOOD); w = R.sample(BAD, 3)
        return add("git-good-message", "Ktorá správa commitu je najlepšia?", "Which commit message is best?", g, w, *M)
    fill(b, "git-good-message", 10, good_message, tries=5000)

    PR = ("Server odmietne push, keď nemám jeho najnovšie commity – najprv ich stiahnem pullom, potom pushnem znova.",
          "The server refuses a push when I don't have its newest commits – I get them with pull first, then push again.")
    bank("git-push-rejected", [
        ("Push sa nepodaril, lebo spolužiak medzitým pushol svoje zmeny. Čo mám urobiť?", "My push failed because a classmate pushed their changes in the meantime. What should I do?",
         ("najprv pull, potom znova push", "pull first, then push again"), [("vymazať repozitár a začať odznova", "delete the repository and start over"), ("dať commit ešte raz", "commit once more"),
                                                                            ("počkať, kým sa to opraví samo", "wait until it fixes itself")], *PR),
        ("Push skončil chybou, lebo na serveri sú novšie commity, ktoré nemám. Ktorý krok chýba?", "The push failed because the server has newer commits I don't have. Which step is missing?",
         ("pull", "pull"), [("commit", "commit"), ("ďalší push", "another push"), ("vymazanie súborov", "deleting files")], *PR),
        ("Pracoval som na dvoch počítačoch a z druhého som už pushol. Na prvom mi push nejde. Prečo?", "I worked on two computers and already pushed from the second one. The push from the first fails. Why?",
         ("server má commity, ktoré tento počítač ešte nemá – treba pull", "the server has commits this computer doesn't have yet – I need to pull"),
         [("na jednom repozitári sa dá pracovať iba z jedného počítača", "a repository can only be used from one computer"), ("treba urobiť nový repozitár", "I need a new repository"), ("push funguje iba raz denne", "push works only once a day")], *PR),
        ("Prečo server niekedy odmietne môj push?", "Why does the server sometimes refuse my push?", ("lebo na ňom sú novšie commity, ktoré ešte nemám", "because it has newer commits I don't have yet"),
         [("lebo som urobil príliš veľa commitov", "because I made too many commits"), ("lebo som nezatvoril editor", "because I didn't close the editor"), ("lebo push sa dá urobiť iba raz", "because you can push only once")], *PR),
    ])

    GI = ("Do `.gitignore` patria súbory, ktoré sa dajú znova vytvoriť (výstup prekladu) alebo sú súkromné – nie zdrojový kód.",
          "`.gitignore` is for files that can be regenerated (build output) or are private – not source code.")
    bank("git-gitignore", [
        ("Ktorý priečinok patrí do `.gitignore` v C# projekte?", "Which folder belongs in `.gitignore` in a C# project?", ("`bin/`", "`bin/`"),
         [("`Program.cs`", "`Program.cs`"), ("`.gitignore`", "`.gitignore`"), ("`README.md`", "`README.md`"), ("priečinok so zdrojovým kódom", "the source code folder")], *GI),
        ("Ktorý priečinok patrí do `.gitignore` v C# projekte?", "Which folder belongs in `.gitignore` in a C# project?", ("`obj/`", "`obj/`"),
         [("`Program.cs`", "`Program.cs`"), ("`Projekt.csproj`", "`Projekt.csproj`"), ("`README.md`", "`README.md`")], *GI),
        ("Ktorý súbor by NEMAL byť v `.gitignore`?", "Which file should NOT be in `.gitignore`?", ("`Program.cs`", "`Program.cs`"),
         [("`bin/`", "`bin/`"), ("`obj/`", "`obj/`"), ("súbor s mojím heslom", "a file with my password")], *GI),
        ("Na čo slúži súbor `.gitignore`?", "What is the `.gitignore` file for?", ("určuje, ktoré súbory Git nemá sledovať", "it says which files Git should not track"),
         [("skryje projekt pred učiteľom", "it hides the project from the teacher"), ("zoznam chýb v programe", "a list of bugs in the program"), ("vymaže súbory z disku", "it deletes files from the disk")], *GI),
        ("Prečo nedávame do repozitára priečinok `bin/`?", "Why don't we put the `bin/` folder into the repository?", ("dá sa kedykoľvek znova vytvoriť prekladom – je to výstup, nie zdrojový kód", "it can be recreated any time by building – it's output, not source code"),
         [("lebo je v ňom zdrojový kód", "because it contains the source code"), ("lebo Git nevie ukladať priečinky", "because Git can't store folders"), ("lebo je to tajný priečinok", "because it's a secret folder")], *GI),
    ])

    K = ("Konflikt vznikne, keď sa zmeny prekrývajú na rovnakom mieste – Git potrebuje, aby človek vybral výslednú verziu.",
         "A conflict happens when changes overlap in the same place – Git needs a person to choose the final version.")
    bank("git-conflict", [
        ("Kedy vznikne konflikt?", "When does a conflict happen?", ("keď dvaja zmenia ten istý riadok toho istého súboru", "when two people change the same line of the same file"),
         [("vždy, keď dvaja pracujú v rovnakom repozitári", "whenever two people work in the same repository"), ("keď niekto zmaže repozitár", "when someone deletes the repository"), ("keď urobím dva commity za sebou", "when I make two commits in a row")], *K),
        ("Ja som zmenil súbor A, spolužiak súbor B. Vznikne pri pulle konflikt?", "I changed file A, a classmate changed file B. Will pulling cause a conflict?",
         ("nie – zmeny sú v rôznych súboroch a Git ich spojí sám", "no – the changes are in different files and Git merges them itself"),
         [("áno, vždy", "yes, always"), ("áno, lebo sme pracovali naraz", "yes, because we worked at the same time"), ("nie, lebo spolužiakove zmeny sa zahodia", "no, because the classmate's changes are thrown away")], *K),
        ("Obaja sme zmenili ten istý riadok v `Program.cs`. Čo sa stane pri pulle?", "We both changed the same line in `Program.cs`. What happens when I pull?",
         ("vznikne konflikt a musím rozhodnúť, ktorá verzia zostane", "a conflict happens and I have to decide which version stays"),
         [("Git ponechá novšiu verziu", "Git keeps the newer version"), ("Git ponechá moju verziu", "Git keeps my version"), ("repozitár sa vymaže", "the repository is deleted")], *K),
        ("Kto vyrieši konflikt?", "Who resolves a conflict?", ("človek – vyberie alebo spojí verzie a urobí commit", "a person – picks or combines the versions and commits"),
         [("Git sám, automaticky", "Git itself, automatically"), ("GitHub po pushi", "GitHub after the push"), ("nikto, konflikt sa nedá vyriešiť", "nobody, a conflict can't be resolved")], *K),
        ("Ako sa dá konfliktom najlepšie predchádzať?", "What is the best way to avoid conflicts?", ("často robiť pull a menšie commity, a nemeniť naraz to isté miesto", "pull often, make smaller commits, and don't edit the same place at once"),
         [("nikdy nerobiť pull", "never pull"), ("robiť jeden veľký commit na konci", "make one big commit at the end"), ("pracovať bez Gitu", "work without Git")], *K),
    ])

    H = ("Každý commit je uložený stav – môžem sa k nemu vrátiť alebo s ním porovnať.", "Every commit is a saved state – I can go back to it or compare with it.")
    bank("git-history", [
        ("Pokazil som program, ktorý včera fungoval. Ako mi pomôže Git?", "I broke a program that worked yesterday. How does Git help?",
         ("môžem sa vrátiť k včerajšiemu commitu alebo s ním porovnať zmeny", "I can go back to yesterday's commit or compare the changes with it"),
         [("Git chybu opraví automaticky", "Git fixes the bug automatically"), ("nijako, história sa po pushi maže", "it doesn't, the history is deleted after a push"), ("pošle chybu učiteľovi", "it sends the bug to the teacher")], *H),
        ("Na čo je dobrá história commitov?", "What is the commit history good for?", ("vidno, kto, kedy a čo zmenil, a dá sa vrátiť k staršej verzii", "you can see who changed what and when, and go back to an older version"),
         [("zrýchli program", "it makes the program faster"), ("nahrádza testy", "it replaces tests"), ("je potrebná iba pre GitHub", "it's needed only for GitHub")], *H),
        ("Môžem zistiť, čo som zmenil od posledného commitu?", "Can I find out what I changed since the last commit?", ("áno, Git ukáže rozdiely oproti poslednému commitu", "yes, Git shows the differences from the last commit"),
         [("nie, Git si pamätá iba posledný súbor", "no, Git remembers only the last file"), ("iba ak urobím push", "only if I push"), ("nie, rozdiely vidí iba učiteľ", "no, only the teacher sees differences")], *H),
        ("Čo sa stane so staršími commitmi, keď urobím nový?", "What happens to older commits when I make a new one?", ("zostanú v histórii", "they stay in the history"),
         [("vymažú sa", "they're deleted"), ("spoja sa do jedného súboru", "they're merged into one file"), ("presunú sa k učiteľovi", "they move to the teacher")], *H),
    ])

    O2 = ("Malé časté commity s jasnou správou robia históriu prehľadnou a návrat jednoduchým.", "Small, frequent commits with clear messages keep the history readable and going back easy.")
    bank("git-commit-often", [
        ("Kedy je vhodné urobiť commit?", "When is a good time to commit?", ("po každom menšom ucelenom kroku, ktorý funguje", "after each small, complete step that works"),
         [("iba raz na konci projektu", "only once at the end of the project"), ("po každom napísanom riadku", "after every line written"), ("iba keď to prikáže učiteľ", "only when the teacher says so")], *O2),
        ("Dopísal som funkciu a funguje. Čo je dobré urobiť?", "I finished a function and it works. What is a good idea now?", ("commit so správou, čo som pridal", "commit with a message saying what I added"),
         [("počkať s commitom do konca roka", "wait with the commit until the end of the year"), ("vymazať repozitár", "delete the repository"), ("nič, Git si to zapamätá sám", "nothing, Git remembers it by itself")], *O2),
        ("Prečo nie je dobré robiť iba jeden veľký commit na konci?", "Why is one big commit at the end a bad idea?", ("ťažko sa v ňom hľadá chyba a nedá sa vrátiť k medzikrokom", "it's hard to find bugs and you can't go back to intermediate steps"),
         [("Git veľké commity nedovolí", "Git doesn't allow big commits"), ("je to v poriadku, nie je s tým problém", "it's fine, there's no problem"), ("veľký commit sa nedá pushnúť", "a big commit can't be pushed")], *O2),
        ("Je dobré commitovať program, ktorý sa nedá preložiť?", "Is it good to commit a program that doesn't compile?", ("radšej nie – commit by mal byť funkčný stav", "better not – a commit should be a working state"),
         [("áno, vždy", "yes, always"), ("áno, Git ho opraví", "yes, Git will fix it"), ("nie, Git to vôbec nedovolí", "no, Git doesn't allow it at all")], *O2),
    ])

    U = ("Na iný počítač alebo k učiteľovi sa dostane iba to, čo som pushol na server.", "Only what I pushed to the server reaches another computer or the teacher.")
    bank("git-uncommitted", [
        ("V škole som dal commit, ale nie push. Doma som otvoril projekt a dal pull. Mám doma svoje zmeny?", "At school I committed but didn't push. At home I opened the project and pulled. Do I have my changes at home?",
         ("nie – na serveri nie sú", "no – they aren't on the server"), [("áno, pull ich stiahol", "yes, pull downloaded them"), ("stratili sa navždy", "they're lost forever"), ("objavia sa až po fetch", "they'll appear only after a fetch")], *U),
        ("Upravil som súbory, ale nedal som commit. Počítač sa pokazil. Sú moje zmeny na GitHube?", "I edited files but didn't commit. The computer broke. Are my changes on GitHub?",
         ("nie – neboli commitnuté ani pushnuté", "no – they were neither committed nor pushed"), [("áno, Git ich poslal sám", "yes, Git sent them by itself"), ("áno, ale iba prvý súbor", "yes, but only the first file"), ("áno, ak som bol na internete", "yes, if I was online")], *U),
        ("Dal som commit aj push v škole. Doma dám pull. Mám zmeny?", "I committed and pushed at school. At home I pull. Do I have the changes?",
         ("áno – sú na serveri a pull ich stiahol", "yes – they're on the server and pull downloaded them"), [("nie, treba ešte commit", "no, I still need to commit"), ("nie, pull funguje iba v škole", "no, pull only works at school"), ("iba polovicu", "only half of them")], *U),
        ("Kde sú zmeny, ktoré som uložil (Ctrl+S), ale necommitol?", "Where are changes I saved (Ctrl+S) but didn't commit?", ("iba v súboroch na mojom počítači – Git ich ešte neuložil do histórie", "only in the files on my computer – Git hasn't stored them in the history yet"),
         [("na GitHube", "on GitHub"), ("v poslednom commite", "in the last commit"), ("nikde, Ctrl+S nič neuloží", "nowhere, Ctrl+S saves nothing")], *U),
    ])

    I = ("Tlačidlá v IDE robia tie isté kroky: Commit uloží stav lokálne, Push ho pošle na server, Pull/Sync stiahne zmeny.", "IDE buttons do the same steps: Commit saves a state locally, Push sends it to the server, Pull/Sync downloads changes.")
    bank("git-ide-buttons", [
        ("Čo spraví tlačidlo **Sync** (Synchronizovať) v IDE?", "What does the **Sync** button in the IDE do?", ("stiahne zmeny zo servera (pull) a pošle moje commity (push)", "downloads changes from the server (pull) and sends my commits (push)"),
         [("iba uloží súbor", "only saves the file"), ("urobí commit bez správy", "makes a commit without a message"), ("vymaže lokálne zmeny", "deletes local changes")], *I),
        ("Čo spraví tlačidlo **Commit** v IDE?", "What does the **Commit** button in the IDE do?", ("uloží zmeny ako commit so správou na mojom počítači", "saves the changes as a commit with a message on my computer"),
         [("pošle zmeny na GitHub", "sends the changes to GitHub"), ("stiahne zmeny spolužiakov", "downloads classmates' changes"), ("spustí program", "runs the program")], *I),
        ("Čo spraví voľba **Commit and Push**?", "What does **Commit and Push** do?", ("urobí commit a hneď ho pošle na server", "makes a commit and sends it to the server right away"),
         [("iba commit", "only a commit"), ("iba push bez commitu", "only a push without a commit"), ("stiahne zmeny zo servera", "downloads changes from the server")], *I),
        ("IDE ukazuje pri tlačidle Sync číslo „↑2“. Čo znamená?", "The IDE shows “↑2” next to the Sync button. What does it mean?", ("mám 2 commity, ktoré ešte nie sú na serveri", "I have 2 commits that aren't on the server yet"),
         [("na serveri sú 2 nové commity", "there are 2 new commits on the server"), ("mám 2 chyby v kóde", "I have 2 errors in the code"), ("2 súbory nie sú uložené", "2 files aren't saved")], *I),
        ("IDE ukazuje pri tlačidle Sync číslo „↓3“. Čo znamená?", "The IDE shows “↓3” next to the Sync button. What does it mean?", ("na serveri sú 3 commity, ktoré ešte nemám", "the server has 3 commits I don't have yet"),
         [("mám 3 commity na odoslanie", "I have 3 commits to send"), ("3 súbory sa vymažú", "3 files will be deleted"), ("mám 3 konflikty", "I have 3 conflicts")], *I),
    ])
    return b


if __name__ == "__main__":
    main().write()
