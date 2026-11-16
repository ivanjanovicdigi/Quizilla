// The design guide: turns the design review of compiler/Design.cs into a learning path –
// ONE next step, the remaining tips and what is already done. Pure logic (unit-testable).
// The order follows how a design grows: classes → their data → the link → the manager and its
// list → the operations → clean-up.
import type { DesignCheck, DesignReview } from './protocol';

/** Design rules the app has texts for ('design.<id>.ok' / '.fail' / '.why'), in learning order. */
export const DESIGN_CHECKS = ['classes', 'members', 'link', 'storage', 'operations', 'main_state',
  'instantiated', 'static', 'public_fields', 'unused'] as const;

export type DesignCheckId = (typeof DESIGN_CHECKS)[number];

export interface Guide {
  next: DesignCheck | null;    // the one thing to do now (null = nothing left)
  more: DesignCheck[];         // other open tips, in order
  done: DesignCheck[];         // rules the code already follows
  total: number;
}

/** The design rules to show, in learning order (rules the app does not know are dropped). */
export function designChecks(design: DesignReview | null | undefined): DesignCheck[] {
  const byId = new Map((design?.checks ?? []).map((c) => [c.id, c]));
  return DESIGN_CHECKS.flatMap((id) => byId.get(id) ?? []);
}

export function buildGuide(design: DesignReview | null | undefined): Guide {
  const checks = designChecks(design);
  const open = checks.filter((c) => !c.ok);
  return { next: open[0] ?? null, more: open.slice(1), done: checks.filter((c) => c.ok), total: checks.length };
}

// Small generic examples (Item / Person / Shop – on purpose not a domain of any assignment, so
// they show the idea without giving a solution away). Code only, so they are not translated.
export const DESIGN_EXAMPLES: Partial<Record<DesignCheckId, string>> = {
  classes: `class Item { }
class Person { }
class Shop { }`,
  members: `class Person
{
    public string Name { get; set; }
    public int Age { get; set; }
}`,
  link: `class Item
{
    public string Title { get; set; }
    public Person? Holder { get; set; }
}`,
  storage: `class Shop
{
    private List<Item> items = new List<Item>();
}`,
  operations: `class Shop
{
    public void AddItem(Item item) { /* ... */ }
    public bool Give(string title, Person person) { /* ... */ }
    public List<Item> FreeItems() { /* ... */ }
}`,
  main_state: `// not in the main program:  item.Holder = person;
shop.Give(title, person);`,
  instantiated: `Person person = new Person();`,
  static: `Shop shop = new Shop();
shop.AddItem(item);        // not: Shop.AddItem(item)`,
  public_fields: `public string Name { get; set; }   // not: public string Name;`,
};
