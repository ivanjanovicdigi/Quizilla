// Minimal, safe Markdown subset for question texts and answers:
//   ```csharp fenced code blocks```, `inline code`, **bold**, paragraphs, line breaks.
// Everything is HTML-escaped first; C# is highlighted with Prism (≈ 10 kB gzipped).
import Prism from 'prismjs';
import 'prismjs/components/prism-csharp';

const CS_ALIASES = new Set(['csharp', 'cs', 'c#', '']);

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function highlight(code: string, lang: string): string {
  const l = lang.toLowerCase();
  if (CS_ALIASES.has(l) && Prism.languages.csharp) {
    return Prism.highlight(code, Prism.languages.csharp, 'csharp');
  }
  return escapeHtml(code);
}

function inline(text: string): string {
  // split on `code` spans first so their content is not touched by other rules
  return text
    .split(/(`[^`\n]+`)/g)
    .map((part) => {
      if (part.length > 2 && part.startsWith('`') && part.endsWith('`')) {
        return `<code class="ic">${highlight(part.slice(1, -1), 'csharp')}</code>`;
      }
      return escapeHtml(part)
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    })
    .join('');
}

/** Render a question body (block content). */
export function renderBlock(src: string): string {
  const out: string[] = [];
  const re = /```([\w#+-]*)[^\S\n]*\n([\s\S]*?)\n?```/g;
  let last = 0;
  let m: RegExpExecArray | null;
  const pushText = (text: string) => {
    for (const para of text.split(/\n\s*\n/)) {
      const p = para.trim();
      if (p) out.push(`<p>${inline(p)}</p>`);
    }
  };
  while ((m = re.exec(src))) {
    pushText(src.slice(last, m.index));
    out.push(`<pre class="code"><code>${highlight(m[2], m[1])}</code></pre>`);
    last = re.lastIndex;
  }
  pushText(src.slice(last));
  return out.join('');
}

/** Render a short text (answer option, explanation). Fenced blocks are allowed too. */
export function renderShort(src: string): string {
  return src.includes('```') ? renderBlock(src) : inline(src.trim());
}
