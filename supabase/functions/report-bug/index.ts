// Supabase Edge Function entry point. Logic: handler.ts. Setup: docs/BUG_REPORTS.md
import { handle } from './handler.ts';

Deno.serve((req) => handle(req, Deno.env));
