// Reference solution – Rychlik Car Rental. Hidden from students; used to validate the scenarios.
var company = new RentalCompany("Rychlik");

while (true)
{
    string? line = Console.ReadLine();
    if (line == null) break;
    string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length == 0) continue;

    string command = parts[0].ToLower();
    if (command == "exit") break;

    if (command == "addcar")
    {
        Console.WriteLine(company.AddCar(parts[1], parts[2]));
    }
    else if (command == "rent")
    {
        Console.WriteLine(company.Rent(parts[1], new Customer(parts[2], parts[3])));
    }
    else if (command == "customer")
    {
        string name = parts[1];
        List<Car> cars = company.CarsOf(name);
        if (cars.Count == 0) Console.WriteLine($"{name} has no cars.");
        foreach (Car car in cars) Console.WriteLine($"{car.Plate} {car.Model}");
    }
}

class Car
{
    public string Plate { get; }
    public string Model { get; }
    public Customer? Customer { get; set; }
    public bool IsRented => Customer != null;

    public Car(string plate, string model)
    {
        Plate = plate;
        Model = model;
    }
}

class Customer
{
    public string Name { get; }
    public string Phone { get; }

    public Customer(string name, string phone)
    {
        Name = name;
        Phone = phone;
    }
}

class RentalCompany
{
    public string Name { get; }
    private readonly List<Car> cars = new List<Car>();

    public RentalCompany(string name)
    {
        Name = name;
    }

    public string AddCar(string plate, string model)
    {
        cars.Add(new Car(plate, model));
        return $"Car {plate} added.";
    }

    public string Rent(string plate, Customer customer)
    {
        Car? car = cars.Find(c => c.Plate == plate);
        if (car == null) return $"Car {plate} does not exist.";
        if (car.IsRented) return $"Car {plate} is already rented.";
        car.Customer = customer;
        return $"Car {plate} rented to {customer.Name}.";
    }

    public List<Car> CarsOf(string name)
    {
        return cars.FindAll(c => c.Customer != null && c.Customer.Name == name);
    }
}
