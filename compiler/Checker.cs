using System.Reflection;
using System.Runtime.InteropServices.JavaScript;
using System.Runtime.Loader;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

/// <summary>
/// Compiles a student's console app with Roslyn and runs it with redirected console I/O.
/// Called from JavaScript (src/lib/assignments/compiler.worker.ts). All results are JSON strings.
/// </summary>
public static partial class Checker
{
    // Same global usings as a new .NET 10 console app in Visual Studio (ImplicitUsings).
    const string GlobalUsings = """
        global using global::System;
        global using global::System.Collections.Generic;
        global using global::System.IO;
        global using global::System.Linq;
        global using global::System.Net.Http;
        global using global::System.Threading;
        global using global::System.Threading.Tasks;
        """;

    // Replacements for console calls that cannot work in the browser (see Rewriter).
    const string RuntimeHelpers = """
        internal sealed class __QuizillaExit : global::System.Exception
        {
            public __QuizillaExit(int code) : base("exit " + code) { }
        }
        internal static class __QuizillaRuntime
        {
            public static void Exit(int code) => throw new __QuizillaExit(code);
            public static void Clear() { }
            public static global::System.ConsoleKeyInfo ReadKey(bool intercept = false) => default;
        }
        """;

    static readonly CSharpParseOptions ParseOptions = new(LanguageVersion.CSharp14);
    static List<MetadataReference>? references;
    static byte[]? lastAssembly;


    static List<MetadataReference> References()
    {
        if (references != null) return references;
        var asm = typeof(Checker).Assembly;
        references = asm.GetManifestResourceNames()
            .Where(n => n.StartsWith("ref/", StringComparison.Ordinal))
            .Select(n =>
            {
                using var s = asm.GetManifestResourceStream(n)!;
                using var ms = new MemoryStream();
                s.CopyTo(ms);
                return (MetadataReference)MetadataReference.CreateFromImage(ms.ToArray());
            })
            .ToList();
        return references;
    }

    /// <summary>Warms up Roslyn (first compile is slow). Returns the Roslyn version.</summary>
    [JSExport]
    public static string Warmup()
    {
        Compile("Console.WriteLine(1);");
        return typeof(CSharpCompilation).Assembly.GetName().Version?.ToString() ?? "?";
    }

    /// <summary>
    /// Compiles the code. Returns JSON { ok, diagnostics: [{ line, column, id, severity, message }] }.
    /// On success the assembly is kept for <see cref="TakeAssembly"/>.
    /// </summary>
    [JSExport]
    public static string Compile(string code)
    {
        lastAssembly = null;
        var tree = CSharpSyntaxTree.ParseText(code, ParseOptions, path: "Program.cs");
        var compilation = CreateCompilation(tree);

        var diagnostics = compilation.GetDiagnostics()
            .Where(d => d.Severity is DiagnosticSeverity.Error or DiagnosticSeverity.Warning && !d.IsSuppressed)
            .Where(d => d.Location.SourceTree == tree || d.Severity == DiagnosticSeverity.Error)
            .OrderBy(d => d.Severity == DiagnosticSeverity.Error ? 0 : 1)
            .ThenBy(d => d.Location.SourceSpan.Start)
            .Take(100)
            .Select(ToDiag)
            .ToList();
        bool ok = !diagnostics.Any(d => d.Severity == "error");

        if (ok)
        {
            // swap browser-hostile calls (Environment.Exit, Console.Clear/ReadKey) for safe helpers
            var model = compilation.GetSemanticModel(tree);
            var root = new Rewriter(model).Visit(tree.GetRoot());
            if (root != tree.GetRoot())
            {
                tree = tree.WithRootAndOptions(root, ParseOptions);
                compilation = CreateCompilation(tree);
            }
            using var ms = new MemoryStream();
            var emit = compilation.Emit(ms);
            if (emit.Success) lastAssembly = ms.ToArray();
            else
            {
                ok = false;
                diagnostics = emit.Diagnostics.Where(d => d.Severity == DiagnosticSeverity.Error).Select(ToDiag).ToList();
            }
        }

        return JsonSerializer.Serialize(new CompileResult(ok, diagnostics), CheckerJson.Default.CompileResult);
    }

    /// <summary>The assembly of the last successful compile (so a new worker can run it without compiling).</summary>
    [JSExport]
    public static byte[] TakeAssembly() => lastAssembly ?? [];

    /// <summary>
    /// Runs the compiled program once: <paramref name="input"/> is the console input; output is
    /// captured up to <paramref name="maxOutput"/> characters.
    /// Returns JSON { stdout, stderr, exception?, exception_message?, output_limit, exit_code? }.
    /// </summary>
    [JSExport]
    public static string Run(byte[] assembly, string input, int maxOutput)
    {
        var stdout = new LimitedWriter(maxOutput);
        var stderr = new LimitedWriter(maxOutput);
        var oldOut = Console.Out;
        var oldErr = Console.Error;
        string? exception = null, message = null;
        int? exitCode = null;
        bool limit = false;

        // a fresh load context per run: static fields of the student's classes start clean
        var alc = new AssemblyLoadContext("student", isCollectible: true);
        try
        {
            Console.SetOut(stdout);
            Console.SetError(stderr);
            Console.SetIn(new StringReader(input));

            var asm = alc.LoadFromStream(new MemoryStream(assembly));
            var entry = asm.EntryPoint ?? throw new InvalidOperationException("No entry point.");
            object?[]? args = entry.GetParameters().Length == 0 ? null : [Array.Empty<string>()];
            var result = entry.Invoke(null, args);
            if (result is Task task) task.GetAwaiter().GetResult();
        }
        catch (Exception e)
        {
            var inner = e is TargetInvocationException { InnerException: { } ie } ? ie : e;
            if (inner is AggregateException { InnerExceptions.Count: 1 } ae) inner = ae.InnerExceptions[0];
            switch (inner)
            {
                case OutputLimitException: limit = true; break;
                case Exception ex when ex.GetType().Name == "__QuizillaExit":
                    exitCode = int.TryParse(ex.Message.AsSpan(5), out var c) ? c : 0;
                    break;
                default:
                    exception = inner.GetType().FullName;
                    message = inner.Message;
                    break;
            }
        }
        finally
        {
            Console.SetOut(oldOut);
            Console.SetError(oldErr);
            Console.SetIn(TextReader.Null); // reading Console.In throws in the browser, so it is not saved
            alc.Unload();
        }

        return JsonSerializer.Serialize(new RunResult(stdout.ToString(), stderr.ToString(), exception, message,
            limit || stdout.Overflowed, exitCode), CheckerJson.Default.RunResult);
    }

    static CSharpCompilation CreateCompilation(SyntaxTree tree) => CSharpCompilation.Create(
        "StudentProgram",
        [
            tree,
            CSharpSyntaxTree.ParseText(GlobalUsings, ParseOptions, path: "GlobalUsings.cs"),
            CSharpSyntaxTree.ParseText(RuntimeHelpers, ParseOptions, path: "QuizillaRuntime.cs"),
        ],
        References(),
        new CSharpCompilationOptions(OutputKind.ConsoleApplication,
            nullableContextOptions: NullableContextOptions.Enable,
            optimizationLevel: OptimizationLevel.Debug,
            concurrentBuild: false)); // the browser has one thread

    static Diag ToDiag(Diagnostic d)
    {
        var pos = d.Location.GetLineSpan();
        return new Diag(
            pos.StartLinePosition.Line + 1,
            pos.StartLinePosition.Character + 1,
            d.Id,
            d.Severity == DiagnosticSeverity.Error ? "error" : "warning",
            d.GetMessage(System.Globalization.CultureInfo.InvariantCulture));
    }

    /// <summary>Replaces Environment.Exit / Console.Clear / Console.ReadKey calls with __QuizillaRuntime.</summary>
    sealed class Rewriter(SemanticModel model) : CSharpSyntaxRewriter
    {
        public override SyntaxNode? VisitInvocationExpression(InvocationExpressionSyntax node)
        {
            var visited = (InvocationExpressionSyntax)base.VisitInvocationExpression(node)!;
            if (model.GetSymbolInfo(node).Symbol is not IMethodSymbol m) return visited;
            string type = m.ContainingType.ToDisplayString();
            string? target = (type, m.Name) switch
            {
                ("System.Environment", "Exit") => "Exit",
                ("System.Console", "Clear") => "Clear",
                ("System.Console", "ReadKey") => "ReadKey",
                _ => null,
            };
            if (target == null) return visited;
            return visited.WithExpression(
                SyntaxFactory.ParseExpression("global::__QuizillaRuntime." + target).WithTriviaFrom(visited.Expression));
        }
    }

    sealed class OutputLimitException() : Exception("Too much output.");

    /// <summary>StringWriter that stops the program once it has written too much.</summary>
    sealed class LimitedWriter(int max) : StringWriter
    {
        public bool Overflowed { get; private set; }
        public override Encoding Encoding => Encoding.UTF8;

        void Check(int adding)
        {
            if (GetStringBuilder().Length + adding <= max) return;
            Overflowed = true;
            throw new OutputLimitException();
        }

        public override void Write(char value) { Check(1); base.Write(value); }
        public override void Write(char[] buffer, int index, int count) { Check(count); base.Write(buffer, index, count); }
        public override void Write(string? value) { Check(value?.Length ?? 0); base.Write(value); }
        public override void Write(ReadOnlySpan<char> buffer) { Check(buffer.Length); base.Write(buffer); }
        public override void WriteLine(ReadOnlySpan<char> buffer) { Check(buffer.Length + 1); base.WriteLine(buffer); }
    }
}

record Diag(int Line, int Column, string Id, string Severity, string Message);
record CompileResult(bool Ok, List<Diag> Diagnostics);
record RunResult(string Stdout, string Stderr, string? Exception, string? ExceptionMessage, bool OutputLimit, int? ExitCode);

// JSON without reflection (the published module is trimmed, reflection-based JSON is disabled)
[JsonSourceGenerationOptions(PropertyNamingPolicy = JsonKnownNamingPolicy.SnakeCaseLower,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull)]
[JsonSerializable(typeof(CompileResult))]
[JsonSerializable(typeof(RunResult))]
partial class CheckerJson : JsonSerializerContext;
