<script lang="ts">
  // The assignment brief as plain prose – no sections or lists, because breaking the task down
  // is the student's job. Commands (what the user types) and replies (what the program prints)
  // stay inside the text; they look different from each other and are NOT coloured like C#.
  import { briefParagraphs } from '../lib/assignments/brief';

  let { text }: { text: string } = $props();
  const paragraphs = $derived(briefParagraphs(text));
</script>

<div class="brief">
  {#each paragraphs as parts, i (i)}
    <p>{#each parts as p, j (j)}{#if p.kind === 'command'}<kbd class="cmd">{p.text}</kbd>{:else if p.kind === 'output'}<samp class="out">{p.text}</samp>{:else}{p.text}{/if}{/each}</p>
  {/each}
</div>

<style>
  .brief { line-height: 1.65; }
  p { margin: 0 0 .9em; }
  p:last-child { margin-bottom: 0; }
  /* typed by the user: looks like a key */
  .cmd {
    font: 700 .88em ui-monospace, "Cascadia Code", Consolas, monospace;
    padding: 1px 7px; border-radius: 6px; white-space: nowrap;
    background: var(--surface-2); color: var(--text);
    border: 1px solid var(--border); border-bottom-width: 2px;
  }
  /* printed by the program: looks like a console line */
  .out {
    font: .88em ui-monospace, "Cascadia Code", Consolas, monospace;
    padding: 1px 7px; border-radius: 4px;
    background: var(--code-bg); color: var(--text);
    border-left: 3px solid var(--accent);
    box-decoration-break: clone; -webkit-box-decoration-break: clone;
  }
</style>
