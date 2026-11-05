// Reference solution – Hotel Tatra. Hidden from students; used to validate the scenarios.
var hotel = new Hotel("Tatra");

while (true)
{
    string? line = Console.ReadLine();
    if (line == null) break;
    string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length == 0) continue;

    string command = parts[0].ToLower();
    if (command == "exit") break;

    if (command == "addroom")
    {
        Console.WriteLine(hotel.AddRoom(int.Parse(parts[1]), parts[2]));
    }
    else if (command == "book")
    {
        Console.WriteLine(hotel.Book(int.Parse(parts[1]), new Guest(parts[2], parts[3])));
    }
    else if (command == "free")
    {
        List<Room> free = hotel.FreeRooms();
        if (free.Count == 0) Console.WriteLine("No free rooms.");
        foreach (Room room in free) Console.WriteLine($"{room.Number} {room.Type}");
    }
}

class Room
{
    public int Number { get; }
    public string Type { get; }
    public Guest? Guest { get; set; }
    public bool IsFree => Guest == null;

    public Room(int number, string type)
    {
        Number = number;
        Type = type;
    }
}

class Guest
{
    public string Name { get; }
    public string Email { get; }

    public Guest(string name, string email)
    {
        Name = name;
        Email = email;
    }
}

class Hotel
{
    public string Name { get; }
    private readonly List<Room> rooms = new List<Room>();

    public Hotel(string name)
    {
        Name = name;
    }

    public string AddRoom(int number, string type)
    {
        rooms.Add(new Room(number, type));
        return $"Room {number} added.";
    }

    public string Book(int number, Guest guest)
    {
        Room? room = rooms.Find(r => r.Number == number);
        if (room == null) return $"Room {number} does not exist.";
        if (!room.IsFree) return $"Room {number} is not available.";
        room.Guest = guest;
        return $"Room {number} booked for {guest.Name}.";
    }

    public List<Room> FreeRooms()
    {
        return rooms.FindAll(r => r.IsFree);
    }
}
