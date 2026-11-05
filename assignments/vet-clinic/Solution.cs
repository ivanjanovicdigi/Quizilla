// Reference solution – Labka Vet Clinic. Hidden from students; used to validate the scenarios.
var clinic = new Clinic("Labka");

while (true)
{
    string? line = Console.ReadLine();
    if (line == null) break;
    string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length == 0) continue;

    string command = parts[0].ToLower();
    if (command == "exit") break;

    if (command == "addslot")
    {
        Console.WriteLine(clinic.AddSlot(parts[1], parts[2]));
    }
    else if (command == "book")
    {
        Console.WriteLine(clinic.Book(parts[1], new Owner(parts[2], parts[3])));
    }
    else if (command == "schedule")
    {
        List<Slot> slots = clinic.Schedule();
        if (slots.Count == 0) Console.WriteLine("No slots.");
        foreach (Slot slot in slots)
        {
            if (slot.IsFree) Console.WriteLine($"{slot.Time} {slot.Vet} free");
            else Console.WriteLine($"{slot.Time} {slot.Vet} {slot.Owner!.Name} {slot.Owner.PetName}");
        }
    }
}

class Slot
{
    public string Time { get; }
    public string Vet { get; }
    public Owner? Owner { get; set; }
    public bool IsFree => Owner == null;

    public Slot(string time, string vet)
    {
        Time = time;
        Vet = vet;
    }
}

class Owner
{
    public string Name { get; }
    public string PetName { get; }

    public Owner(string name, string petName)
    {
        Name = name;
        PetName = petName;
    }
}

class Clinic
{
    public string Name { get; }
    private readonly List<Slot> slots = new List<Slot>();

    public Clinic(string name)
    {
        Name = name;
    }

    public string AddSlot(string time, string vet)
    {
        slots.Add(new Slot(time, vet));
        return $"Slot {time} added.";
    }

    public string Book(string time, Owner owner)
    {
        Slot? slot = slots.Find(s => s.Time == time);
        if (slot == null) return $"Slot {time} does not exist.";
        if (!slot.IsFree) return $"Slot {time} is already booked.";
        slot.Owner = owner;
        return $"Slot {time} booked for {owner.Name} with {owner.PetName}.";
    }

    public List<Slot> Schedule()
    {
        return slots;
    }
}
