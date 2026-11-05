// Entry point of the WebAssembly module. Nothing runs at start-up: the Web Worker calls the
// [JSExport] methods in Checker.cs (compile, then run once per scenario).
[assembly: System.Runtime.Versioning.SupportedOSPlatform("browser")]

return;
