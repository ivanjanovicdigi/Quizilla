<script lang="ts">
  // Lightweight C# editor: a transparent <textarea> over a Prism-highlighted copy of the same
  // text, with line numbers. Tab inserts 4 spaces, Enter keeps the indentation (+4 after "{").
  import Prism from 'prismjs';
  import 'prismjs/components/prism-csharp';

  let {
    value = $bindable(''),
    errorLines = new Set<number>(),
    placeholder = '',
    label = '',
  }: { value?: string; errorLines?: Set<number>; placeholder?: string; label?: string } = $props();

  let ta: HTMLTextAreaElement;
  let pre: HTMLPreElement;
  let gutter: HTMLDivElement;

  const lineCount = $derived(Math.max(1, value.split('\n').length));
  // Safe: Prism escapes the code; the extra newline keeps the last empty line visible.
  const html = $derived(Prism.highlight(value + '\n', Prism.languages.csharp, 'csharp'));

  function sync() {
    pre.scrollTop = ta.scrollTop;
    pre.scrollLeft = ta.scrollLeft;
    gutter.scrollTop = ta.scrollTop;
  }

  /** Inserts text at the cursor, keeping the browser's undo history where possible. */
  function insert(text: string) {
    ta.focus();
    if (!document.execCommand?.('insertText', false, text)) {
      ta.setRangeText(text, ta.selectionStart, ta.selectionEnd, 'end');
    }
    value = ta.value;
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Tab' && !e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault();
      insert('    ');
    } else if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
      const before = value.slice(0, ta.selectionStart);
      const line = before.slice(before.lastIndexOf('\n') + 1);
      let indent = /^[ \t]*/.exec(line)![0];
      if (/\{\s*$/.test(line)) indent += '    ';
      e.preventDefault();
      insert('\n' + indent);
    }
  }

  /** Puts the cursor at the start of a line (1-based) and scrolls it into view. */
  export function focusLine(line: number, column = 1) {
    const lines = value.split('\n');
    const l = Math.min(Math.max(1, line), lines.length);
    let pos = 0;
    for (let i = 0; i < l - 1; i++) pos += lines[i].length + 1;
    pos += Math.min(Math.max(0, column - 1), lines[l - 1].length);
    ta.focus();
    ta.setSelectionRange(pos, pos);
    const lh = parseFloat(getComputedStyle(ta).lineHeight) || 21;
    ta.scrollTop = Math.max(0, (l - 3) * lh);
    ta.scrollIntoView({ block: 'center', behavior: 'smooth' });
    sync();
  }
</script>

<div class="editor">
  <div class="gutter" bind:this={gutter} aria-hidden="true">
    {#each { length: lineCount } as _, i (i)}
      <div class:err={errorLines.has(i + 1)}>{i + 1}</div>
    {/each}
  </div>
  <div class="area">
    <pre class="hl" bind:this={pre} aria-hidden="true"><code>{@html html}</code></pre>
    <textarea
      bind:this={ta}
      bind:value
      onscroll={sync}
      oninput={sync}
      onkeydown={onKeydown}
      {placeholder}
      aria-label={label}
      spellcheck="false"
      autocomplete="off"
      autocapitalize="off"
      wrap="off"></textarea>
  </div>
</div>

<style>
  .editor {
    --pad: 12px;
    --lh: 21px;
    display: flex;
    height: 460px;
    min-height: 200px;
    resize: vertical;
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--code-bg);
    font: 14px/var(--lh) ui-monospace, "Cascadia Code", "JetBrains Mono", Consolas, monospace;
  }
  .editor:focus-within { outline: 2px solid var(--accent); outline-offset: 1px; }
  .gutter {
    flex: none;
    min-width: 44px;
    padding: var(--pad) 8px var(--pad) 0;
    overflow: hidden;
    text-align: right;
    color: var(--muted);
    background: var(--surface-2);
    border-right: 1px solid var(--border);
    user-select: none;
  }
  .gutter div { height: var(--lh); }
  .gutter .err { color: var(--bad); font-weight: 700; background: var(--bad-soft); }
  .area { position: relative; flex: 1; min-width: 0; }
  .hl, textarea {
    position: absolute;
    inset: 0;
    margin: 0;
    padding: var(--pad);
    border: 0;
    font: inherit;
    line-height: var(--lh);
    tab-size: 4;
    white-space: pre;
    overflow: auto;
  }
  .hl { color: var(--code-text); pointer-events: none; scrollbar-width: none; }
  .hl::-webkit-scrollbar { display: none; }
  .hl code { font: inherit; }
  textarea {
    resize: none;
    background: transparent;
    color: transparent;
    caret-color: var(--text);
    outline: none;
  }
  textarea::placeholder { color: var(--muted); }
  textarea::selection { background: color-mix(in srgb, var(--info) 35%, transparent); color: transparent; }
</style>
