// Reference solution – Hviezda Cinema. Hidden from students; used to validate the scenarios.
var cinema = new Cinema("Hviezda");

while (true)
{
    string? line = Console.ReadLine();
    if (line == null) break;
    string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length == 0) continue;

    string command = parts[0].ToLower();
    if (command == "exit") break;

    if (command == "addseat")
    {
        Console.WriteLine(cinema.AddSeat(parts[1], parts[2]));
    }
    else if (command == "reserve")
    {
        Console.WriteLine(cinema.Reserve(parts[1], new Viewer(parts[2], parts[3])));
    }
    else if (command == "seat")
    {
        Seat? seat = cinema.FindSeat(parts[1]);
        if (seat == null) Console.WriteLine($"Seat {parts[1]} does not exist.");
        else if (seat.IsFree) Console.WriteLine($"{seat.Code} {seat.Category} free");
        else Console.WriteLine($"{seat.Code} {seat.Category} reserved for {seat.Viewer!.Name}");
    }
}

class Seat
{
    public string Code { get; }
    public string Category { get; }
    public Viewer? Viewer { get; set; }
    public bool IsFree => Viewer == null;

    public Seat(string code, string category)
    {
        Code = code;
        Category = category;
    }
}

class Viewer
{
    public string Name { get; }
    public string Email { get; }

    public Viewer(string name, string email)
    {
        Name = name;
        Email = email;
    }
}

class Cinema
{
    public string Name { get; }
    private readonly List<Seat> seats = new List<Seat>();

    public Cinema(string name)
    {
        Name = name;
    }

    public string AddSeat(string code, string category)
    {
        seats.Add(new Seat(code, category));
        return $"Seat {code} added.";
    }

    public string Reserve(string code, Viewer viewer)
    {
        Seat? seat = FindSeat(code);
        if (seat == null) return $"Seat {code} does not exist.";
        if (!seat.IsFree) return $"Seat {code} is already reserved.";
        seat.Viewer = viewer;
        return $"Seat {code} reserved for {viewer.Name}.";
    }

    public Seat? FindSeat(string code)
    {
        return seats.Find(s => s.Code == code);
    }
}
