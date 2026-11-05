// Dev-only self-test for the in-browser compiler – see compiler-test.html.
import { checkCode, loadCompiler, compilerVersion, type Scenario } from '../src/lib/assignments/runner';

const out = document.getElementById('out')!;
const status = document.getElementById('status')!;
const results: { name: string; ok: boolean; detail: string }[] = [];
const log = (name: string, ok: boolean, detail = '') => {
  results.push({ name, ok, detail });
  out.innerHTML += `<span class="${ok ? 'ok' : 'fail'}">${ok ? 'OK  ' : 'FAIL'}</span> ${name}${detail ? ' – ' + detail.replace(/</g, '&lt;') : ''}\n`;
};

const jsons = import.meta.glob('/assignments/*/assignment.json', { eager: true, import: 'default' }) as Record<string, any>;
const solutions = import.meta.glob('/assignments/*/Solution.cs', { eager: true, query: '?raw', import: 'default' }) as Record<string, string>;
const text = (lines: string[]) => lines.map((l) => l + '\n').join('');
const toScenarios = (a: any): Scenario[] => a.scenarios.map((s: any, index: number) => ({
  index, name_sk: s.sk, name_en: s.en, input: text(s.input), expected: text(s.expected), points: s.points,
}));

async function main() {
  const t0 = performance.now();
  status.textContent = 'loading compiler…';
  await loadCompiler();
  const loadMs = Math.round(performance.now() - t0);
  log(`compiler loaded (Roslyn ${compilerVersion()})`, true, `${loadMs} ms`);

  // 1. every reference solution scores 100
  for (const [path, a] of Object.entries(jsons)) {
    const code = solutions[path.replace('assignment.json', 'Solution.cs')];
    const t = performance.now();
    const r = await checkCode(code, toScenarios(a), a.time_limit_ms);
    const fails = r.results.filter((x) => !x.passed).map((x) => `#${x.index}: ${JSON.stringify(x.actual)}`);
    log(`${a.slug}: reference solution`, r.compiled && r.score === 100,
      `${r.score}/${r.max_points}, ${Math.round(performance.now() - t)} ms ${r.compiled ? '' : JSON.stringify(r.diagnostics[0])} ${fails.join(' ')}`);
  }

  const hotel = Object.values(jsons).find((a) => a.slug === 'hotel');
  const hotelCode = solutions['/assignments/hotel/Solution.cs'];
  const sc = toScenarios(hotel);

  // 2. compile error with a line number
  let r = await checkCode(hotelCode.replace('class Guest\r\n{', 'class Guest\r\n{ int x = ;').replace('class Guest\n{', 'class Guest\n{ int x = ;'), sc, 3000);
  const err = r.diagnostics.find((d) => d.severity === 'error');
  log('compile error is reported with line and id', !r.compiled && !!err && err.line > 1 && /^CS\d+$/.test(err.id), JSON.stringify(err));

  // 3. endless loop → timeout, then the next scenarios still run (fresh worker)
  const loopCode = `int n = 0;\nwhile (true) { string? l = Console.ReadLine(); if (l == "free") { while (true) { n++; } } if (l == null || l == "exit") break; Console.WriteLine("Room 101 added."); }`;
  const t = performance.now();
  r = await checkCode(loopCode, sc, 1500);
  const loopRes = r.results.map((x) => (x.timed_out ? 'T' : x.passed ? 'P' : 'F')).join('');
  // scenarios 1, 3, 4 use "free" (→ loop); 0 and 2 must still run normally after a restart
  log('endless loop times out; other scenarios still run', loopRes === 'FTFTT',
    `${loopRes} in ${Math.round(performance.now() - t)} ms`);

  // 4. Environment.Exit on "exit" works like a normal end
  r = await checkCode(hotelCode.replace('if (command == "exit") break;', 'if (command == "exit") Environment.Exit(0);'), sc, 3000);
  log('Environment.Exit(0) ends the program normally', r.score === 100 && r.results[0].exit_code === 0, `${r.score}`);

  // 5. Console.Clear / Console.ReadKey do not break anything
  r = await checkCode('Console.Clear();\n' + hotelCode.replace('if (command == "exit") break;', 'if (command == "exit") { Console.ReadKey(); break; }'), sc, 3000);
  log('Console.Clear and Console.ReadKey are harmless', r.score === 100, `${r.score}`);

  // 6. crash: exception is reported, output so far is kept
  r = await checkCode(hotelCode.replace('rooms.Add(new Room(number, type));', 'rooms.Add(new Room(number, type)); if (number == 102) throw new InvalidOperationException("boom");'), sc, 3000);
  log('crash is reported with the exception and partial output', r.results[0].exception === 'System.InvalidOperationException' && r.results[0].actual.includes('Room 101 added.') && !r.results[0].passed,
    `${r.results[0].exception}: ${r.results[0].exception_message}`);

  // 7. flooding output stops at the limit
  r = await checkCode('while (true) Console.WriteLine("spam spam spam");', sc, 3000);
  log('too much output is stopped', r.results.every((x) => x.output_limit && !x.passed && !x.timed_out), `${r.results[0].actual.length} chars`);

  // 8. each scenario starts with fresh static state
  const staticCode = `Counter.N++;\nConsole.WriteLine("run " + Counter.N);\nstatic class Counter { public static int N; }`;
  r = await checkCode(staticCode, sc.slice(0, 3), 3000);
  log('static fields reset between scenarios', r.results.every((x) => x.actual.trim() === 'run 1'), r.results.map((x) => x.actual.trim()).join(', '));

  // 9. a program with Main instead of top-level statements
  r = await checkCode('class Program { static void Main(string[] args) { Console.WriteLine("Room 101 added."); Console.WriteLine("Room 102 added."); } }', sc.slice(0, 1), 3000);
  log('classic static Main works', r.score === 15, `${r.score}`);

  // 10. case / spacing differences are accepted
  r = await checkCode('Console.WriteLine("ROOM   101 added.  ");\nConsole.WriteLine();\nConsole.WriteLine("room 102 ADDED.");', sc.slice(0, 1), 3000);
  log('output compare ignores case and extra whitespace', r.score === 15, `${r.score}`);

  const failed = results.filter((x) => !x.ok).length;
  status.textContent = failed ? `${failed} FAILED` : `all ${results.length} passed`;
  (window as any).__compilerTest = { done: true, failed, results };
}

main().catch((e) => {
  status.textContent = 'ERROR: ' + (e?.message ?? e);
  (window as any).__compilerTest = { done: true, failed: -1, error: String(e?.message ?? e) };
});
