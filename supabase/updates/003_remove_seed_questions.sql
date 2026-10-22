-- Quizilla – remove the old sample questions from seed.sql
-- Deletes the 36 sample questions (matched by their exact text). Answers that
-- students gave to them (quiz.attempts) are deleted too, together with the
-- points they earned. Questions imported from templates are not touched.
-- Run once in Supabase → SQL Editor. Safe to re-run.
begin;

delete from quiz.questions
 where replace(body, E'\r', '') in (
   select replace(b, E'\r', '') from unnest(array[
  $b$Ktorý dátový typ je vhodný na uloženie celého čísla?$b$,
  $b$Čo vypíše tento kód?

```csharp
int a = 5;
a = a + 3;
Console.WriteLine(a);
```$b$,
  $b$Ktorá deklarácia je správna?$b$,
  $b$Akú hodnotu môže mať premenná typu `bool`?$b$,
  $b$Čo vypíše tento kód?

```csharp
int x = 7;
int y = 2;
Console.WriteLine(x / y);
```$b$,
  $b$Čo vypíše tento kód?

```csharp
string a = "5";
string b = "3";
Console.WriteLine(a + b);
```$b$,
  $b$Čo vypíše `Console.WriteLine(7 % 3);`?$b$,
  $b$Ktorý riadok spôsobí chybu pri preklade?

```csharp
int a = 10;      // riadok 1
double b = a;    // riadok 2
int c = b;       // riadok 3
string d = "x";  // riadok 4
```$b$,
  $b$Čo vypíše tento kód?

```csharp
int i = 5;
int j = i++ + ++i;
Console.WriteLine(j);
```$b$,
  $b$Čo vypíše tento kód?

```csharp
double d = 9.99;
int n = (int)d;
Console.WriteLine(n);
```$b$,
  $b$Čo vypíše tento kód?

```csharp
var x = 10 / 4.0;
Console.WriteLine(x.GetType().Name);
```$b$,
  $b$Čo vypíše tento kód?

```csharp
int max = int.MaxValue;
max++;
Console.WriteLine(max == int.MinValue);
```$b$,
  $b$Čo vypíše tento kód?

```csharp
int vek = 18;
if (vek >= 18)
    Console.WriteLine("Dospelý");
else
    Console.WriteLine("Neplnoletý");
```$b$,
  $b$Ktorý operátor sa používa na porovnanie „rovná sa“?$b$,
  $b$Ktorý operátor znamená logické „a zároveň“ (AND)?$b$,
  $b$Aký je výsledok výrazu `!(5 > 3)`?$b$,
  $b$Čo vypíše tento kód?

```csharp
int x = 15;
if (x > 10)
    Console.WriteLine("A");
else if (x > 5)
    Console.WriteLine("B");
else
    Console.WriteLine("C");
```$b$,
  $b$Čo vypíše tento kód?

```csharp
int body = 72;
string znamka = body >= 90 ? "1" : body >= 70 ? "2" : "3";
Console.WriteLine(znamka);
```$b$,
  $b$Čo vypíše tento kód?

```csharp
int den = 3;
switch (den)
{
    case 1: Console.WriteLine("Pondelok"); break;
    case 3: Console.WriteLine("Streda"); break;
    default: Console.WriteLine("Iný deň"); break;
}
```$b$,
  $b$Ktorá podmienka platí práve vtedy, keď je `x` od 1 do 10 (vrátane)?$b$,
  $b$Čo vypíše tento kód?

```csharp
int a = 0;
if (a != 0 && 10 / a > 1)
    Console.WriteLine("Áno");
else
    Console.WriteLine("Nie");
```$b$,
  $b$Čo vypíše tento kód?

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
  $b$Čo vypíše tento kód? (Pozor na odsadenie.)

```csharp
int x = 5;
if (x > 3)
    if (x > 10)
        Console.WriteLine("A");
else
    Console.WriteLine("B");
```$b$,
  $b$Čo vypíše tento kód?

```csharp
string s = null;
if (s?.Length > 0)
    Console.WriteLine("Neprázdny");
else
    Console.WriteLine("Prázdny alebo null");
```$b$,
  $b$Koľkokrát sa vypíše „Ahoj“?

```csharp
for (int i = 0; i < 3; i++)
    Console.WriteLine("Ahoj");
```$b$,
  $b$Čo vypíše tento kód?

```csharp
for (int i = 1; i <= 3; i++)
    Console.Write(i);
```$b$,
  $b$Ktorý cyklus sa vykoná vždy aspoň raz?$b$,
  $b$Čo vypíše tento kód?

```csharp
int i = 10;
while (i < 5)
{
    Console.Write(i);
    i++;
}
Console.Write("Koniec");
```$b$,
  $b$Čo vypíše tento kód?

```csharp
int sucet = 0;
for (int i = 1; i <= 4; i++)
    sucet += i;
Console.WriteLine(sucet);
```$b$,
  $b$Čo vypíše tento kód?

```csharp
for (int i = 0; i < 10; i += 3)
    Console.Write(i + " ");
```$b$,
  $b$Čo vypíše tento kód?

```csharp
for (int i = 1; i <= 5; i++)
{
    if (i == 3) break;
    Console.Write(i);
}
```$b$,
  $b$Čo vypíše tento kód?

```csharp
for (int i = 1; i <= 5; i++)
{
    if (i % 2 == 0) continue;
    Console.Write(i);
}
```$b$,
  $b$Čo vypíše tento kód?

```csharp
int pocet = 0;
for (int i = 0; i < 3; i++)
    for (int j = i; j < 3; j++)
        pocet++;
Console.WriteLine(pocet);
```$b$,
  $b$Čo vypíše tento kód?

```csharp
int n = 5;
int f = 1;
while (n > 1)
    f *= n--;
Console.WriteLine(f);
```$b$,
  $b$Čo vypíše tento kód?

```csharp
int i = 0;
do
{
    i += 2;
} while (i < 7);
Console.WriteLine(i);
```$b$,
  $b$Čo vypíše tento kód?

```csharp
string s = "";
for (int i = 3; i > 0; i--)
    s = i + s;
Console.WriteLine(s);
```$b$
   ]) as b
 );

commit;

-- check: questions left per topic
select t.sort_order, t.slug,
       (select count(*) from quiz.questions q where q.topic_id = t.id) as questions
  from quiz.topics t join quiz.subjects s on s.id = t.subject_id
 where s.slug = 'prog-1-digi' order by t.sort_order;
