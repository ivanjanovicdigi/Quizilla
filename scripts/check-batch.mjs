#!/usr/bin/env node
// Checks the format of question batches.
//   node scripts/check-batch.mjs                 → all files in questions/batches
//   node scripts/check-batch.mjs file.json …     → only these files
//   --quiet                                       → hide warnings
import { basename } from 'node:path';
import { batchFiles, readJson, validateBatch, flag } from './lib/batch.mjs';

const args = process.argv.slice(2);
const files = batchFiles(args);
if (!files.length) {
  console.log('No batch files found (questions/batches/*.json).');
  process.exit(0);
}

const allIds = new Map(); // id → file (ids must be unique across all batches)
let errorCount = 0;
let warningCount = 0;

for (const file of files) {
  let batch;
  try {
    batch = readJson(file);
  } catch (e) {
    console.log(`\n✖ ${basename(file)}: invalid JSON – ${e.message}`);
    errorCount++;
    continue;
  }
  const { errors, warnings } = validateBatch(batch, file);
  for (const q of batch.questions ?? []) {
    if (!q.id) continue;
    if (allIds.has(q.id) && allIds.get(q.id) !== file) {
      errors.push(`${q.id}: id also used in ${basename(allIds.get(q.id))}`);
    }
    allIds.set(q.id, file);
  }

  const qs = batch.questions ?? [];
  const count = (s) => qs.filter((q) => q.status === s).length;
  const verified = qs.filter((q) => q.check?.status === 'ok').length;
  const failed = qs.filter((q) => q.check?.status === 'fail').length;
  console.log(
    `\n${errors.length ? '✖' : '✔'} ${basename(file)} – ${qs.length} questions ` +
      `(pending ${count('pending')}, approved ${count('approved')}, rejected ${count('rejected')}; ` +
      `dotnet ok ${verified}, failed ${failed})`,
  );
  for (const e of errors) console.log(`   error   ${e}`);
  if (!flag(args, 'quiet')) for (const w of warnings) console.log(`   warning ${w}`);
  errorCount += errors.length;
  warningCount += warnings.length;
}

console.log(`\n${errorCount} error(s), ${warningCount} warning(s).`);
process.exit(errorCount ? 1 : 0);
