// The assignment brief is free prose, like a real client's request: working out what the
// parts are is the student's job, so the app does NOT split it into sections or lists.
// Only the `code` spans inside the text are marked: they are console text, not C#, so they
// are never syntax-coloured. A span is either something the user TYPES (a command: one
// lowercase word) or something the program PRINTS (a reply). Pure logic.

export type BriefPart =
  | { kind: 'text'; text: string }
  | { kind: 'command'; text: string }   // typed by the user
  | { kind: 'output'; text: string };   // printed by the program

const isCommand = (s: string) => /^[a-z][a-z0-9]*$/.test(s);

/** A paragraph as parts: plain text, commands and outputs. */
export function briefParts(paragraph: string): BriefPart[] {
  return paragraph
    .split(/(`[^`\n]+`)/g)
    .filter((p) => p !== '')
    .map((p): BriefPart => {
      if (p.length > 2 && p.startsWith('`') && p.endsWith('`')) {
        const text = p.slice(1, -1);
        return { kind: isCommand(text) ? 'command' : 'output', text };
      }
      return { kind: 'text', text: p };
    });
}

/** The brief as paragraphs of parts, in the order and wording it was written. */
export function briefParagraphs(text: string): BriefPart[][] {
  return text.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean).map(briefParts);
}
