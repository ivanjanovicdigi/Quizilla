// Reference solution – Centrum Parking Garage. Hidden from students; used to validate the scenarios.
var garage = new Garage("Centrum");

while (true)
{
    string? line = Console.ReadLine();
    if (line == null) break;
    string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length == 0) continue;

    string command = parts[0].ToLower();
    if (command == "exit") break;

    if (command == "addspot")
    {
        Console.WriteLine(garage.AddSpot(int.Parse(parts[1]), int.Parse(parts[2])));
    }
    else if (command == "park")
    {
        Console.WriteLine(garage.Park(int.Parse(parts[1]), new Driver(parts[2], parts[3])));
    }
    else if (command == "find")
    {
        string plate = parts[1];
        ParkingSpot? spot = garage.FindCar(plate);
        if (spot == null) Console.WriteLine($"Car {plate} is not in the garage.");
        else Console.WriteLine($"Car {plate} is at spot {spot.Number} on floor {spot.Floor}.");
    }
}

class ParkingSpot
{
    public int Number { get; }
    public int Floor { get; }
    public Driver? Driver { get; set; }
    public bool IsFree => Driver == null;

    public ParkingSpot(int number, int floor)
    {
        Number = number;
        Floor = floor;
    }
}

class Driver
{
    public string Name { get; }
    public string Plate { get; }

    public Driver(string name, string plate)
    {
        Name = name;
        Plate = plate;
    }
}

class Garage
{
    public string Name { get; }
    private readonly List<ParkingSpot> spots = new List<ParkingSpot>();

    public Garage(string name)
    {
        Name = name;
    }

    public string AddSpot(int number, int floor)
    {
        spots.Add(new ParkingSpot(number, floor));
        return $"Spot {number} added.";
    }

    public string Park(int number, Driver driver)
    {
        ParkingSpot? spot = spots.Find(s => s.Number == number);
        if (spot == null) return $"Spot {number} does not exist.";
        if (!spot.IsFree) return $"Spot {number} is occupied.";
        spot.Driver = driver;
        return $"{driver.Name} parked at spot {number}.";
    }

    public ParkingSpot? FindCar(string plate)
    {
        return spots.Find(s => s.Driver != null && s.Driver.Plate == plate);
    }
}
