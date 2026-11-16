using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

/// <summary>
/// Design review of a student's program: looks at HOW the code is built (classes, links between
/// them, where the data and the logic live), not at what it prints. Feedback only – it never
/// changes the score. The rules do not depend on names, because the brief never names classes.
/// Pure Roslyn (no browser APIs), so it can be tested outside WebAssembly.
/// Check ids are translated in src/lib/i18n.svelte.ts ('design.&lt;id&gt;.ok' / '.fail').
/// </summary>
public static class DesignAnalyzer
{
    const int MinClasses = 3;
    const int MinMembers = 2;
    const int MinOperations = 3;
    const int MaxItems = 8;

    static readonly SymbolEqualityComparer Eq = SymbolEqualityComparer.Default;
    static readonly HashSet<string> Mutators = ["Add", "AddRange", "Insert", "Remove", "RemoveAt", "RemoveAll", "Clear"];

    public static DesignReview Analyze(CSharpCompilation compilation, SyntaxTree tree)
    {
        var model = compilation.GetSemanticModel(tree);
        var root = tree.GetRoot();
        // the class with Main (or the hidden Program of top-level statements) = "the main program"
        var entry = compilation.GetEntryPoint(default)?.ContainingType;

        var own = new List<INamedTypeSymbol>();      // the student's classes (objects can be created)
        var statics = new List<INamedTypeSymbol>();  // static classes other than the main program
        var seen = new HashSet<INamedTypeSymbol>(Eq);
        foreach (var decl in root.DescendantNodes().OfType<TypeDeclarationSyntax>())
        {
            if (decl is InterfaceDeclarationSyntax) continue;
            if (model.GetDeclaredSymbol(decl) is not INamedTypeSymbol t || !seen.Add(t)) continue;
            if (Eq.Equals(t, entry)) continue;
            (t.IsStatic ? statics : own).Add(t);
        }
        var ownSet = new HashSet<INamedTypeSymbol>(own, Eq);

        bool InEntry(SyntaxNode node)
        {
            var td = node.Ancestors().OfType<TypeDeclarationSyntax>().FirstOrDefault();
            if (td == null) return true; // top-level statement
            return entry != null && Eq.Equals(model.GetDeclaredSymbol(td), entry);
        }

        // classes that only hold static methods are reported once, by the "static" check
        var staticLike = new HashSet<INamedTypeSymbol>(Eq);
        foreach (var t in own)
        {
            var methods = t.GetMembers().OfType<IMethodSymbol>()
                .Where(m => m.MethodKind == MethodKind.Ordinary && !m.IsImplicitlyDeclared).ToList();
            if (methods.Count > 0 && methods.All(m => m.IsStatic)) staticLike.Add(t);
        }

        var checks = new List<DesignCheck>();
        void Add(string id, bool ok, int? n = null, IEnumerable<DesignItem>? items = null)
        {
            var list = items?.OrderBy(i => i.Line).Take(MaxItems).ToList();
            checks.Add(new DesignCheck(id, ok, n, list is { Count: > 0 } ? list : null));
        }

        // 1. enough classes
        Add("classes", own.Count >= MinClasses, own.Count);

        // 2. every class holds some data
        if (own.Count > 0)
        {
            var thin = own.Where(t => !staticLike.Contains(t) && Data(t).Count < MinMembers).Select(Item).ToList();
            Add("members", thin.Count == 0, items: thin);
        }

        // 3. link: an object knows another object (Room.Guest → Guest)
        bool link = own.Any(t => Data(t).Any(m => Direct(m.Type, ownSet) is { } other && !Eq.Equals(other, t)));
        Add("link", link);

        // 4. storage: a class keeps the collection of objects (not the main program)
        var managers = own.Where(t => Data(t).Any(m => Holds(m.Type, ownSet))).ToList();
        var looseLists = new List<DesignItem>();
        foreach (var v in root.DescendantNodes().OfType<VariableDeclaratorSyntax>())
        {
            var type = model.GetDeclaredSymbol(v) switch
            {
                // a local that only holds a result (var free = hotel.FreeRooms()) is fine
                ILocalSymbol l when InEntry(v) && CreatesCollection(v.Initializer?.Value) => l.Type,
                IFieldSymbol f when f.IsStatic || InEntry(v) => f.Type,
                _ => null,
            };
            if (type != null && Holds(type, ownSet)) looseLists.Add(new DesignItem(v.Identifier.Text, Line(v)));
        }
        Add("storage", managers.Count > 0 && looseLists.Count == 0, items: looseLists);

        // 5. operations: the class that keeps the collection (else the busiest class) has methods
        var candidates = managers.Count > 0 ? managers : own;
        int operations = candidates.Select(t => Methods(t).Count).DefaultIfEmpty(0).Max();
        Add("operations", operations >= MinOperations, operations);

        // 6. the main program does not change objects itself (it should ask the classes to do it)
        var meddling = new List<DesignItem>();
        foreach (var node in root.DescendantNodes())
        {
            ExpressionSyntax? target = node switch
            {
                AssignmentExpressionSyntax a when a.Parent is not InitializerExpressionSyntax => a.Left,
                PrefixUnaryExpressionSyntax p when p.IsKind(SyntaxKind.PreIncrementExpression) || p.IsKind(SyntaxKind.PreDecrementExpression) => p.Operand,
                PostfixUnaryExpressionSyntax p when p.IsKind(SyntaxKind.PostIncrementExpression) || p.IsKind(SyntaxKind.PostDecrementExpression) => p.Operand,
                InvocationExpressionSyntax { Expression: MemberAccessExpressionSyntax m } when Mutators.Contains(m.Name.Identifier.Text) => m.Expression,
                _ => null,
            };
            if (target == null || !InEntry(node)) continue;
            var symbol = model.GetSymbolInfo(target).Symbol;
            if (symbol is not (IPropertySymbol or IFieldSymbol) || symbol.ContainingType is not { } owner || !ownSet.Contains(owner)) continue;
            meddling.Add(new DesignItem(target.ToString(), Line(node)));
        }
        Add("main_state", meddling.Count == 0, items: meddling);

        // 7. every class is really used to create objects
        if (own.Count > 0)
        {
            var created = new HashSet<INamedTypeSymbol>(Eq);
            foreach (var node in root.DescendantNodes().OfType<BaseObjectCreationExpressionSyntax>())
                for (var t = model.GetTypeInfo(node).Type as INamedTypeSymbol; t != null; t = t.BaseType)
                    created.Add(t.OriginalDefinition);
            var never = own.Where(t => t.TypeKind == TypeKind.Class && !t.IsAbstract && !staticLike.Contains(t) && !created.Contains(t)).Select(Item).ToList();
            Add("instantiated", never.Count == 0, items: never);
        }

        // 8. objects instead of static code
        var staticItems = statics.Concat(staticLike).Select(Item).ToList();
        Add("static", staticItems.Count == 0, items: staticItems);

        // 9. no public fields (use properties)
        var publicFields = own.SelectMany(Fields)
            .Where(f => f.DeclaredAccessibility == Accessibility.Public)
            .Select(f => new DesignItem($"{f.ContainingType.Name}.{f.Name}", Line(f))).ToList();
        Add("public_fields", publicFields.Count == 0, items: publicFields);

        // 10. nothing is left unused
        var used = new HashSet<ISymbol>(Eq);
        foreach (var name in root.DescendantNodes().OfType<SimpleNameSyntax>())
        {
            var info = model.GetSymbolInfo(name);
            var s = info.Symbol ?? info.CandidateSymbols.FirstOrDefault();
            if (s != null) used.Add(s.OriginalDefinition);
        }
        var unused = new List<DesignItem>();
        foreach (var t in own.Concat(statics))
        {
            if (t.AllInterfaces.Length > 0) continue; // members may be called through the interface
            IEnumerable<ISymbol> members = t.GetMembers().Where(m => !m.IsImplicitlyDeclared && !m.IsOverride && m switch
            {
                IMethodSymbol { MethodKind: MethodKind.Ordinary } => true,
                IPropertySymbol { IsIndexer: false } p => p.Name != "EqualityContract",
                _ => false,
            });
            unused.AddRange(members.Where(m => !used.Contains(m)).Select(m => new DesignItem($"{t.Name}.{m.Name}", Line(m))));
        }
        Add("unused", unused.Count == 0, items: unused);

        var classes = own
            .Select(t => new DesignClass(t.Name, Line(t), Properties(t).Count, Fields(t).Count, Methods(t).Count))
            .OrderBy(c => c.Line).ToList();
        return new DesignReview(classes, checks);
    }

    static List<IPropertySymbol> Properties(INamedTypeSymbol t) => t.GetMembers().OfType<IPropertySymbol>()
        .Where(p => !p.IsStatic && !p.IsImplicitlyDeclared && !p.IsIndexer && p.Name != "EqualityContract").ToList();

    static List<IFieldSymbol> Fields(INamedTypeSymbol t) => t.GetMembers().OfType<IFieldSymbol>()
        .Where(f => !f.IsStatic && !f.IsConst && !f.IsImplicitlyDeclared).ToList();

    /// <summary>Instance methods the student wrote (no constructors, no overrides like ToString).</summary>
    static List<IMethodSymbol> Methods(INamedTypeSymbol t) => t.GetMembers().OfType<IMethodSymbol>()
        .Where(m => m.MethodKind == MethodKind.Ordinary && !m.IsStatic && !m.IsImplicitlyDeclared && !m.IsOverride).ToList();

    /// <summary>The data of an object: its properties and fields, with their types.</summary>
    static List<(ISymbol Symbol, ITypeSymbol Type)> Data(INamedTypeSymbol t) =>
    [
        .. Properties(t).Select(p => ((ISymbol)p, p.Type)),
        .. Fields(t).Select(f => ((ISymbol)f, f.Type)),
    ];

    /// <summary>The student's class this type is (Guest, Guest?), or null.</summary>
    static INamedTypeSymbol? Direct(ITypeSymbol type, HashSet<INamedTypeSymbol> own)
    {
        if (type is INamedTypeSymbol { OriginalDefinition.SpecialType: SpecialType.System_Nullable_T } n) type = n.TypeArguments[0];
        return type is INamedTypeSymbol x && own.Contains(x) ? x : null;
    }

    /// <summary>True for a collection of the student's objects: Room[], List&lt;Room&gt;, Dictionary&lt;int, Room&gt; …</summary>
    static bool Holds(ITypeSymbol type, HashSet<INamedTypeSymbol> own)
    {
        if (type is IArrayTypeSymbol a) return Direct(a.ElementType, own) != null || Holds(a.ElementType, own);
        if (type is INamedTypeSymbol { IsGenericType: true } n
            && n.OriginalDefinition.SpecialType != SpecialType.System_Nullable_T && !own.Contains(n))
            return n.TypeArguments.Any(x => Direct(x, own) != null || Holds(x, own));
        return false;
    }

    /// <summary>new List&lt;Room&gt;(), new Room[10], [] … – a new, empty collection (not the result of a call).</summary>
    static bool CreatesCollection(ExpressionSyntax? value) => value is BaseObjectCreationExpressionSyntax
        or ArrayCreationExpressionSyntax or ImplicitArrayCreationExpressionSyntax or CollectionExpressionSyntax;

    static DesignItem Item(INamedTypeSymbol t) => new(t.Name, Line(t));

    static int Line(ISymbol s) => s.Locations.FirstOrDefault(l => l.IsInSource) is { } l ? l.GetLineSpan().StartLinePosition.Line + 1 : 0;

    static int Line(SyntaxNode n) => n.GetLocation().GetLineSpan().StartLinePosition.Line + 1;
}

public record DesignItem(string Name, int Line);
public record DesignCheck(string Id, bool Ok, int? N, List<DesignItem>? Items);
public record DesignClass(string Name, int Line, int Properties, int Fields, int Methods);
public record DesignReview(List<DesignClass> Classes, List<DesignCheck> Checks);
