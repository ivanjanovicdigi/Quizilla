// Reference solution – School Cafeteria. Hidden from students; used to validate the scenarios.
var cafeteria = new Cafeteria("Poprad");

while (true)
{
    string? line = Console.ReadLine();
    if (line == null) break;
    string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length == 0) continue;

    string command = parts[0].ToLower();
    if (command == "exit") break;

    if (command == "addportion")
    {
        Console.WriteLine(cafeteria.AddPortion(parts[1], parts[2]));
    }
    else if (command == "reserve")
    {
        Console.WriteLine(cafeteria.Reserve(parts[1], new Student(parts[2], parts[3])));
    }
    else if (command == "class")
    {
        string className = parts[1];
        List<Portion> portions = cafeteria.PortionsOfClass(className);
        if (portions.Count == 0) Console.WriteLine($"No portions for class {className}.");
        foreach (Portion p in portions) Console.WriteLine($"{p.Code} {p.Dish} {p.Student!.Name}");
    }
}

class Portion
{
    public string Code { get; }
    public string Dish { get; }
    public Student? Student { get; set; }
    public bool IsFree => Student == null;

    public Portion(string code, string dish)
    {
        Code = code;
        Dish = dish;
    }
}

class Student
{
    public string Name { get; }
    public string ClassName { get; }

    public Student(string name, string className)
    {
        Name = name;
        ClassName = className;
    }
}

class Cafeteria
{
    public string Name { get; }
    private readonly List<Portion> portions = new List<Portion>();

    public Cafeteria(string name)
    {
        Name = name;
    }

    public string AddPortion(string code, string dish)
    {
        portions.Add(new Portion(code, dish));
        return $"Portion {code} added.";
    }

    public string Reserve(string code, Student student)
    {
        Portion? portion = portions.Find(p => p.Code == code);
        if (portion == null) return $"Portion {code} does not exist.";
        if (!portion.IsFree) return $"Portion {code} is already reserved.";
        portion.Student = student;
        return $"Portion {code} reserved for {student.Name} ({student.ClassName}).";
    }

    public List<Portion> PortionsOfClass(string className)
    {
        return portions.FindAll(p => p.Student != null && p.Student.ClassName == className);
    }
}
