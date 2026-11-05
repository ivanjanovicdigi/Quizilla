// Reference solution – Sila Fitness. Hidden from students; used to validate the scenarios.
var gym = new Gym("Sila");

while (true)
{
    string? line = Console.ReadLine();
    if (line == null) break;
    string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length == 0) continue;

    string command = parts[0].ToLower();
    if (command == "exit") break;

    if (command == "addlocker")
    {
        Console.WriteLine(gym.AddLocker(int.Parse(parts[1]), parts[2]));
    }
    else if (command == "assign")
    {
        Console.WriteLine(gym.Assign(int.Parse(parts[1]), new Member(parts[2], parts[3])));
    }
    else if (command == "count")
    {
        Console.WriteLine($"Free lockers: {gym.CountFree()}, taken lockers: {gym.CountTaken()}.");
    }
}

class Locker
{
    public int Number { get; }
    public string Size { get; }
    public Member? Member { get; set; }
    public bool IsFree => Member == null;

    public Locker(int number, string size)
    {
        Number = number;
        Size = size;
    }
}

class Member
{
    public string Name { get; }
    public string CardId { get; }

    public Member(string name, string cardId)
    {
        Name = name;
        CardId = cardId;
    }
}

class Gym
{
    public string Name { get; }
    private readonly List<Locker> lockers = new List<Locker>();

    public Gym(string name)
    {
        Name = name;
    }

    public string AddLocker(int number, string size)
    {
        lockers.Add(new Locker(number, size));
        return $"Locker {number} added.";
    }

    public string Assign(int number, Member member)
    {
        Locker? locker = lockers.Find(l => l.Number == number);
        if (locker == null) return $"Locker {number} does not exist.";
        if (!locker.IsFree) return $"Locker {number} is taken.";
        locker.Member = member;
        return $"Locker {number} assigned to {member.Name}.";
    }

    public int CountFree()
    {
        return lockers.FindAll(l => l.IsFree).Count;
    }

    public int CountTaken()
    {
        return lockers.Count - CountFree();
    }
}
