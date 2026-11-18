// Reference solution – Cafe Orders. Hidden from students; used to validate the scenarios.
using System.Globalization;

var menu = new Menu("Kaviaren");
menu.AddProduct(new Product("Espresso", 2.00m));
menu.AddProduct(new Product("Americano", 2.80m));
menu.AddProduct(new Product("Cappuccino", 3.50m));
menu.AddProduct(new Product("Latte", 3.80m));
menu.AddProduct(new Product("Cheesecake", 4.50m));

var order = new Order("");

while (true)
{
    string? line = Console.ReadLine();
    if (line == null) break;
    string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length == 0) continue;

    string command = parts[0].ToLower();
    if (command == "exit") break;

    if (command == "name")
    {
        order = new Order(parts[1]);
        Console.WriteLine($"Hello, {parts[1]}!");
    }
    else if (command == "menu")
    {
        for (int i = 0; i < menu.Products.Count; i++)
        {
            Console.WriteLine($"{i + 1}. {menu.Products[i].Info()}");
        }
    }
    else if (command == "add")
    {
        decimal price = decimal.Parse(parts[2], CultureInfo.InvariantCulture);
        menu.AddProduct(new Product(parts[1], price));
        Console.WriteLine($"{parts[1]} added to the menu.");
    }
    else if (command == "find")
    {
        PrintProducts(menu.FindByName(parts[1]));
    }
    else if (command == "cheaper")
    {
        PrintProducts(menu.FindByMaxPrice(decimal.Parse(parts[1], CultureInfo.InvariantCulture)));
    }
    else if (command == "order")
    {
        Product? product = menu.Find(parts[1]);
        if (product == null)
        {
            Console.WriteLine($"Product {parts[1]} does not exist.");
        }
        else
        {
            order.Add(product);
            Console.WriteLine($"{product.Name} added to the order.");
        }
    }
    else if (command == "myorder")
    {
        order.Print();
    }
}

static void PrintProducts(List<Product> products)
{
    if (products.Count == 0) Console.WriteLine("No products found.");
    foreach (Product product in products) Console.WriteLine(product.Info());
}

class Product
{
    public string Name { get; }
    public decimal Price { get; }

    public Product(string name, decimal price)
    {
        Name = name;
        Price = price;
    }

    public string Info()
    {
        return $"{Name} {Price.ToString("0.00", CultureInfo.InvariantCulture)} EUR";
    }
}

class Order
{
    public string CustomerName { get; }
    public List<Product> Products { get; } = new List<Product>();

    public Order(string customerName)
    {
        CustomerName = customerName;
    }

    public decimal Total()
    {
        decimal total = 0;
        foreach (Product product in Products) total += product.Price;
        return total;
    }

    public void Add(Product product)
    {
        Products.Add(product);
    }

    public void Print()
    {
        if (Products.Count == 0)
        {
            Console.WriteLine("Your order is empty.");
            return;
        }
        Console.WriteLine($"Order for {CustomerName}:");
        foreach (Product product in Products) Console.WriteLine(product.Info());
        Console.WriteLine($"Total: {Total().ToString("0.00", CultureInfo.InvariantCulture)} EUR");
    }
}

class Menu
{
    public string Name { get; }
    public List<Product> Products { get; } = new List<Product>();

    public Menu(string name)
    {
        Name = name;
    }

    public void AddProduct(Product product)
    {
        Products.Add(product);
    }

    public Product? Find(string name)
    {
        return Products.Find(p => p.Name.ToLower() == name.ToLower());
    }

    public List<Product> FindByName(string text)
    {
        return Products.FindAll(p => p.Name.ToLower().Contains(text.ToLower()));
    }

    public List<Product> FindByMaxPrice(decimal maxPrice)
    {
        return Products.FindAll(p => p.Price < maxPrice);
    }
}
