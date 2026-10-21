-- =====================================================================
-- Quizilla – sample data (safe to run once on an empty database)
-- Classes are examples – rename/add your real classes.
-- Sample topics use a lighter unlock rule (4 answers, 75 %) because they
-- only contain 4 questions per level.
-- =====================================================================

insert into quiz.classes (name, sort_order) values
  ('I.A', 1), ('I.B', 2), ('II.A', 3), ('II.B', 4)
on conflict (name) do nothing;

insert into quiz.subjects (slug, name_sk, name_en, sort_order) values
  ('programming-1', 'Programovanie 1 (C#)', 'Programming 1 (C#)', 1)
on conflict (slug) do nothing;

insert into quiz.topics (subject_id, slug, name_sk, name_en, description_sk, description_en, sort_order,
                         unlock_min_answers, unlock_window, unlock_accuracy)
select s.id, v.slug, v.name_sk, v.name_en, v.dsk, v.den, v.ord, 4, 4, 0.75
  from quiz.subjects s,
       (values
         ('variables',  'Premenné a dátové typy', 'Variables and data types',
          'Deklarácia, typy, operátory a pretypovanie.', 'Declarations, types, operators and casting.', 1),
         ('conditions', 'Podmienky', 'Conditions',
          'if / else, logické operátory, switch.', 'if / else, logical operators, switch.', 2),
         ('loops',      'Cykly', 'Loops',
          'for, while, do-while, break a continue.', 'for, while, do-while, break and continue.', 3)
       ) as v(slug, name_sk, name_en, dsk, den, ord)
 where s.slug = 'programming-1'
on conflict (subject_id, slug) do nothing;

-- helper for readable inserts
create or replace function pg_temp.q(p_topic text, p_diff int, p_body text, p_answers text[],
                                     p_correct int, p_expl text default null)
returns void language sql as $$
  insert into quiz.questions (topic_id, difficulty, body, answers, correct_index, explanation)
  select t.id, p_diff, p_body, p_answers, p_correct, p_expl
    from quiz.topics t join quiz.subjects s on s.id = t.subject_id
   where s.slug = 'programming-1' and t.slug = p_topic;
$$;

-- ---------------------------------------------------------------- variables
select pg_temp.q('variables', 1, $b$Ktorý dátový typ je vhodný na uloženie celého čísla?$b$,
  array['`int`', '`string`', '`bool`', '`char`'], 0);

select pg_temp.q('variables', 1, $b$Čo vypíše tento kód?

```csharp
int a = 5;
a = a + 3;
Console.WriteLine(a);
```$b$,
  array['8', '5', '53', '3'], 0);

select pg_temp.q('variables', 1, $b$Ktorá deklarácia je správna?$b$,
  array['`string meno = "Eva";`', $a$`string meno = 'Eva';`$a$, '`meno string = "Eva";`', '`string = "Eva";`'], 0,
  $e$Text (string) sa píše v dvojitých úvodzovkách. Jednoduché úvodzovky sú pre jeden znak (char).$e$);

select pg_temp.q('variables', 1, $b$Akú hodnotu môže mať premenná typu `bool`?$b$,
  array['`true` alebo `false`', 'Ľubovoľné celé číslo', 'Ľubovoľný text', 'Iba `0`'], 0);

select pg_temp.q('variables', 2, $b$Čo vypíše tento kód?

```csharp
int x = 7;
int y = 2;
Console.WriteLine(x / y);
```$b$,
  array['3', '3.5', '4', '3,5'], 0,
  $e$Delenie dvoch celých čísel (int / int) je celočíselné – desatinná časť sa zahodí.$e$);

select pg_temp.q('variables', 2, $b$Čo vypíše tento kód?

```csharp
string a = "5";
string b = "3";
Console.WriteLine(a + b);
```$b$,
  array['53', '8', '5 + 3', 'Chyba pri preklade'], 0,
  $e$Operátor + pri reťazcoch ich spája za seba.$e$);

select pg_temp.q('variables', 2, $b$Čo vypíše `Console.WriteLine(7 % 3);`?$b$,
  array['1', '2', '2.33', '0'], 0,
  $e$Operátor % vracia zvyšok po delení: 7 = 2 · 3 + 1.$e$);

select pg_temp.q('variables', 2, $b$Ktorý riadok spôsobí chybu pri preklade?

```csharp
int a = 10;      // riadok 1
double b = a;    // riadok 2
int c = b;       // riadok 3
string d = "x";  // riadok 4
```$b$,
  array['Riadok 3', 'Riadok 1', 'Riadok 2', 'Riadok 4'], 0,
  $e$double → int môže stratiť informáciu, preto vyžaduje explicitné pretypovanie: `int c = (int)b;`$e$);

select pg_temp.q('variables', 3, $b$Čo vypíše tento kód?

```csharp
int i = 5;
int j = i++ + ++i;
Console.WriteLine(j);
```$b$,
  array['12', '11', '13', '10'], 0,
  $e$i++ vráti 5 (potom i = 6), ++i zvýši i na 7 a vráti 7 → 5 + 7 = 12.$e$);

select pg_temp.q('variables', 3, $b$Čo vypíše tento kód?

```csharp
double d = 9.99;
int n = (int)d;
Console.WriteLine(n);
```$b$,
  array['9', '10', '9.99', 'Chyba pri preklade'], 0,
  $e$Pretypovanie na int desatinnú časť odreže (nezaokrúhľuje).$e$);

select pg_temp.q('variables', 3, $b$Čo vypíše tento kód?

```csharp
var x = 10 / 4.0;
Console.WriteLine(x.GetType().Name);
```$b$,
  array['Double', 'Int32', 'Single', 'Decimal'], 0,
  $e$4.0 je literál typu double, takže aj výsledok delenia je double.$e$);

select pg_temp.q('variables', 3, $b$Čo vypíše tento kód?

```csharp
int max = int.MaxValue;
max++;
Console.WriteLine(max == int.MinValue);
```$b$,
  array['True', 'False', 'Vyhodí OverflowException', 'Chyba pri preklade'], 0,
  $e$Bez `checked` dôjde k pretečeniu a hodnota „pretočí“ na int.MinValue.$e$);

-- --------------------------------------------------------------- conditions
select pg_temp.q('conditions', 1, $b$Čo vypíše tento kód?

```csharp
int vek = 18;
if (vek >= 18)
    Console.WriteLine("Dospelý");
else
    Console.WriteLine("Neplnoletý");
```$b$,
  array['Dospelý', 'Neplnoletý', 'Nič', 'DospelýNeplnoletý'], 0);

select pg_temp.q('conditions', 1, $b$Ktorý operátor sa používa na porovnanie „rovná sa“?$b$,
  array['`==`', '`=`', '`===`', '`!=`'], 0,
  $e$`=` je priradenie, `==` je porovnanie.$e$);

select pg_temp.q('conditions', 1, $b$Ktorý operátor znamená logické „a zároveň“ (AND)?$b$,
  array['`&&`', '`||`', '`!`', '`<>`'], 0);

select pg_temp.q('conditions', 1, $b$Aký je výsledok výrazu `!(5 > 3)`?$b$,
  array['`false`', '`true`', '`5`', '`3`'], 0);

select pg_temp.q('conditions', 2, $b$Čo vypíše tento kód?

```csharp
int x = 15;
if (x > 10)
    Console.WriteLine("A");
else if (x > 5)
    Console.WriteLine("B");
else
    Console.WriteLine("C");
```$b$,
  array['A', 'B', 'AB', 'C'], 0,
  $e$Vykoná sa iba prvá vetva, ktorej podmienka platí.$e$);

select pg_temp.q('conditions', 2, $b$Čo vypíše tento kód?

```csharp
int body = 72;
string znamka = body >= 90 ? "1" : body >= 70 ? "2" : "3";
Console.WriteLine(znamka);
```$b$,
  array['2', '1', '3', 'Chyba pri preklade'], 0);

select pg_temp.q('conditions', 2, $b$Čo vypíše tento kód?

```csharp
int den = 3;
switch (den)
{
    case 1: Console.WriteLine("Pondelok"); break;
    case 3: Console.WriteLine("Streda"); break;
    default: Console.WriteLine("Iný deň"); break;
}
```$b$,
  array['Streda', 'Pondelok', 'Iný deň', 'StredaIný deň'], 0);

select pg_temp.q('conditions', 2, $b$Ktorá podmienka platí práve vtedy, keď je `x` od 1 do 10 (vrátane)?$b$,
  array['`x >= 1 && x <= 10`', '`x >= 1 || x <= 10`', '`1 <= x <= 10`', '`x > 1 && x < 10`'], 0,
  $e$Zápis `1 <= x <= 10` v C# nefunguje – podmienky treba spojiť operátorom &&.$e$);

select pg_temp.q('conditions', 3, $b$Čo vypíše tento kód?

```csharp
int a = 0;
if (a != 0 && 10 / a > 1)
    Console.WriteLine("Áno");
else
    Console.WriteLine("Nie");
```$b$,
  array['Nie', 'Áno', 'Vyhodí DivideByZeroException', 'Chyba pri preklade'], 0,
  $e$Operátor && je skrátený: ak je ľavá strana false, pravá sa vôbec nevyhodnotí.$e$);

select pg_temp.q('conditions', 3, $b$Čo vypíše tento kód?

```csharp
int x = 5;
string s = x switch
{
    < 0  => "záporné",
    0    => "nula",
    < 10 => "malé",
    _    => "veľké"
};
Console.WriteLine(s);
```$b$,
  array['malé', 'veľké', 'nula', 'záporné'], 0);

select pg_temp.q('conditions', 3, $b$Čo vypíše tento kód? (Pozor na odsadenie.)

```csharp
int x = 5;
if (x > 3)
    if (x > 10)
        Console.WriteLine("A");
else
    Console.WriteLine("B");
```$b$,
  array['B', 'A', 'Nič', 'AB'], 0,
  $e$else patrí k najbližšiemu if – teda k `if (x > 10)`. Odsadenie na tom nič nemení.$e$);

select pg_temp.q('conditions', 3, $b$Čo vypíše tento kód?

```csharp
string s = null;
if (s?.Length > 0)
    Console.WriteLine("Neprázdny");
else
    Console.WriteLine("Prázdny alebo null");
```$b$,
  array['Prázdny alebo null', 'Neprázdny', 'Vyhodí NullReferenceException', 'Chyba pri preklade'], 0,
  $e$`s?.Length` vráti null a porovnanie `null > 0` je false.$e$);

-- -------------------------------------------------------------------- loops
select pg_temp.q('loops', 1, $b$Koľkokrát sa vypíše „Ahoj“?

```csharp
for (int i = 0; i < 3; i++)
    Console.WriteLine("Ahoj");
```$b$,
  array['3', '2', '4', '0'], 0);

select pg_temp.q('loops', 1, $b$Čo vypíše tento kód?

```csharp
for (int i = 1; i <= 3; i++)
    Console.Write(i);
```$b$,
  array['123', '012', '1234', '321'], 0);

select pg_temp.q('loops', 1, $b$Ktorý cyklus sa vykoná vždy aspoň raz?$b$,
  array['`do-while`', '`while`', '`for`', '`foreach`'], 0);

select pg_temp.q('loops', 1, $b$Čo vypíše tento kód?

```csharp
int i = 10;
while (i < 5)
{
    Console.Write(i);
    i++;
}
Console.Write("Koniec");
```$b$,
  array['Koniec', '10Koniec', 'Nekonečný cyklus', 'Nič'], 0,
  $e$Podmienka 10 < 5 neplatí hneď na začiatku, telo cyklu sa nevykoná ani raz.$e$);

select pg_temp.q('loops', 2, $b$Čo vypíše tento kód?

```csharp
int sucet = 0;
for (int i = 1; i <= 4; i++)
    sucet += i;
Console.WriteLine(sucet);
```$b$,
  array['10', '6', '4', '24'], 0);

select pg_temp.q('loops', 2, $b$Čo vypíše tento kód?

```csharp
for (int i = 0; i < 10; i += 3)
    Console.Write(i + " ");
```$b$,
  array['0 3 6 9', '0 3 6', '3 6 9', '0 3 6 9 12'], 0);

select pg_temp.q('loops', 2, $b$Čo vypíše tento kód?

```csharp
for (int i = 1; i <= 5; i++)
{
    if (i == 3) break;
    Console.Write(i);
}
```$b$,
  array['12', '123', '1245', '12345'], 0,
  $e$break okamžite ukončí celý cyklus.$e$);

select pg_temp.q('loops', 2, $b$Čo vypíše tento kód?

```csharp
for (int i = 1; i <= 5; i++)
{
    if (i % 2 == 0) continue;
    Console.Write(i);
}
```$b$,
  array['135', '24', '12345', '1'], 0,
  $e$continue preskočí zvyšok tela a pokračuje ďalšou iteráciou.$e$);

select pg_temp.q('loops', 3, $b$Čo vypíše tento kód?

```csharp
int pocet = 0;
for (int i = 0; i < 3; i++)
    for (int j = i; j < 3; j++)
        pocet++;
Console.WriteLine(pocet);
```$b$,
  array['6', '9', '3', '4'], 0,
  $e$Vnútorný cyklus prebehne 3 + 2 + 1 = 6-krát.$e$);

select pg_temp.q('loops', 3, $b$Čo vypíše tento kód?

```csharp
int n = 5;
int f = 1;
while (n > 1)
    f *= n--;
Console.WriteLine(f);
```$b$,
  array['120', '24', '60', '5'], 0,
  $e$f = 5 · 4 · 3 · 2 = 120 (faktoriál čísla 5).$e$);

select pg_temp.q('loops', 3, $b$Čo vypíše tento kód?

```csharp
int i = 0;
do
{
    i += 2;
} while (i < 7);
Console.WriteLine(i);
```$b$,
  array['8', '6', '7', '10'], 0);

select pg_temp.q('loops', 3, $b$Čo vypíše tento kód?

```csharp
string s = "";
for (int i = 3; i > 0; i--)
    s = i + s;
Console.WriteLine(s);
```$b$,
  array['123', '321', '6', '3'], 0,
  $e$Každé nové číslo sa pridáva na začiatok reťazca: "3" → "23" → "123".$e$);
