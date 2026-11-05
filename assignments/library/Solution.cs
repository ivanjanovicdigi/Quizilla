// Reference solution – Village Library. Hidden from students; used to validate the scenarios.
var library = new Library("Lucky");

while (true)
{
    string? line = Console.ReadLine();
    if (line == null) break;
    string[] parts = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    if (parts.Length == 0) continue;

    string command = parts[0].ToLower();
    if (command == "exit") break;

    if (command == "addbook")
    {
        Console.WriteLine(library.AddBook(parts[1], parts[2]));
    }
    else if (command == "borrow")
    {
        Console.WriteLine(library.Borrow(parts[1], new Reader(parts[2], parts[3])));
    }
    else if (command == "borrowed")
    {
        List<Book> borrowed = library.BorrowedBooks();
        if (borrowed.Count == 0) Console.WriteLine("No borrowed books.");
        foreach (Book book in borrowed) Console.WriteLine($"{book.Code} {book.Title} - {book.Reader!.Name}");
    }
}

class Book
{
    public string Code { get; }
    public string Title { get; }
    public Reader? Reader { get; set; }
    public bool IsBorrowed => Reader != null;

    public Book(string code, string title)
    {
        Code = code;
        Title = title;
    }
}

class Reader
{
    public string Name { get; }
    public string CardNumber { get; }

    public Reader(string name, string cardNumber)
    {
        Name = name;
        CardNumber = cardNumber;
    }
}

class Library
{
    public string Name { get; }
    private readonly List<Book> books = new List<Book>();

    public Library(string name)
    {
        Name = name;
    }

    public string AddBook(string code, string title)
    {
        books.Add(new Book(code, title));
        return $"Book {code} added.";
    }

    public string Borrow(string code, Reader reader)
    {
        Book? book = books.Find(b => b.Code == code);
        if (book == null) return $"Book {code} does not exist.";
        if (book.IsBorrowed) return $"Book {code} is already borrowed.";
        book.Reader = reader;
        return $"Book {code} borrowed by {reader.Name}.";
    }

    public List<Book> BorrowedBooks()
    {
        return books.FindAll(b => b.IsBorrowed);
    }
}
