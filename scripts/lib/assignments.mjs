// Shared helpers for coding assignments (assignments/<slug>/assignment.json + Solution.cs).
// Format: see assignments/README.md
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, resolve, basename, dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { ROOT, readJson } from './batch.mjs';
import { normalizeOutput } from '../../src/lib/assignments/compare.js';

export const ASSIGNMENT_DIR = join(ROOT, 'assignments');
export const STATUSES = ['pending', 'approved', 'rejected'];
export const ROLES = ['item', 'person', 'manager'];
// bump when the comparison rule or the way scenarios run changes → every check is redone
export const CHECK_VERSION = 1;

/** Assignment folders given on the command line (folder or assignment.json), or all of them. */
export function assignmentDirs(args) {
  const given = args.filter((a) => !a.startsWith('--'));
  if (given.length) {
    return given.map((a) => {
      const p = resolve(a);
      return basename(p) === 'assignment.json' ? dirname(p) : p;
    });
  }
  if (!existsSync(ASSIGNMENT_DIR)) return [];
  return readdirSync(ASSIGNMENT_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory() && existsSync(join(ASSIGNMENT_DIR, d.name, 'assignment.json')))
    .map((d) => join(ASSIGNMENT_DIR, d.name))
    .sort();
}

/** { dir, file, data, solution } – solution is null when Solution.cs is missing. */
export function loadAssignment(dir) {
  const file = join(dir, 'assignment.json');
  const sol = join(dir, 'Solution.cs');
  return {
    dir,
    file,
    data: readJson(file),
    solution: existsSync(sol) ? readFileSync(sol, 'utf8').replace(/^﻿/, '').replace(/\r/g, '') : null,
  };
}

/** Lines → the text fed to / expected from the program (\n line ends, final newline). */
export const linesToText = (lines) => lines.map((l) => l + '\n').join('');

/** Brief paragraphs → stored Markdown text. */
export const briefText = (brief) => brief.map((p) => p.trim()).join('\n\n');

/** Hash of everything the reference check depends on. */
export function checkHash(a) {
  const scen = a.data.scenarios.map((s) => [s.input, s.expected]);
  return createHash('sha256')
    .update(JSON.stringify({ v: CHECK_VERSION, solution: a.solution, scen, limit: a.data.time_limit_ms }))
    .digest('hex')
    .slice(0, 16);
}

const isStr = (v) => typeof v === 'string' && v.trim() !== '';
const isStrArray = (v) => Array.isArray(v) && v.length > 0 && v.every((x) => typeof x === 'string');
const isInt = (v) => Number.isInteger(v);

/** Validates the format. Returns { errors: string[], warnings: string[] }. */
export function validateAssignment(a) {
  const errors = [];
  const warnings = [];
  const d = a.data;
  const err = (m) => errors.push(m);

  if (!/^[a-z0-9][a-z0-9-]{1,60}$/.test(d.slug ?? '')) err('slug must be lower-case letters, digits and dashes');
  else if (d.slug !== basename(a.dir)) err(`slug "${d.slug}" must equal the folder name "${basename(a.dir)}"`);
  if (!STATUSES.includes(d.status)) err(`status must be one of ${STATUSES.join(', ')}`);
  if (!isInt(d.sort_order)) err('sort_order must be an integer');
  if (!isInt(d.max_points) || d.max_points <= 0) err('max_points must be a positive integer');
  if (!isInt(d.time_limit_ms) || d.time_limit_ms < 100 || d.time_limit_ms > 30000) err('time_limit_ms must be 100–30000');

  for (const lang of ['sk', 'en']) {
    const t = d[lang];
    if (!t || !isStr(t.title)) err(`${lang}.title is missing`);
    if (!t || !isStrArray(t.brief)) err(`${lang}.brief must be a non-empty array of paragraphs`);
  }

  // hidden design: ≥ 3 classes with ≥ 2 properties; one item, one person, one manager with 3 operations
  const classes = d.design?.classes;
  if (!Array.isArray(classes) || classes.length < 3) err('design.classes needs at least 3 classes');
  else {
    for (const c of classes) {
      if (!isStr(c.name)) err('design class without a name');
      if (!ROLES.includes(c.role) && c.role !== 'other') err(`design class ${c.name}: role must be ${ROLES.join('/')}/other`);
      if (!isStrArray(c.properties) || c.properties.length < 2) err(`design class ${c.name}: needs at least 2 properties`);
    }
    for (const r of ROLES) if (!classes.some((c) => c.role === r)) err(`design needs a class with role "${r}"`);
    const mgr = classes.find((c) => c.role === 'manager');
    if (mgr && (!isStrArray(mgr.operations) || mgr.operations.length !== 3)) err('manager class needs exactly 3 operations');
  }
  if (!isStr(d.design?.link)) err('design.link (the one-way link) is missing');
  if (!isStr(d.design?.storage)) err('design.storage is missing');

  // scenarios
  const sc = d.scenarios;
  if (!Array.isArray(sc) || sc.length < 1 || sc.length > 20) err('scenarios must be an array of 1–20 items');
  else {
    if (sc.length !== 5) warnings.push(`${sc.length} scenarios (the template asks for about 5)`);
    const ids = new Set();
    let sum = 0;
    for (const [i, s] of sc.entries()) {
      const at = `scenario ${s.id ?? i + 1}`;
      if (!/^[a-z0-9-]+$/.test(s.id ?? '')) err(`${at}: id must be lower-case letters, digits and dashes`);
      if (ids.has(s.id)) err(`${at}: duplicate id`);
      ids.add(s.id);
      if (!isStr(s.sk) || !isStr(s.en)) err(`${at}: needs sk and en names`);
      if (!isInt(s.points) || s.points <= 0) err(`${at}: points must be a positive integer`);
      else sum += s.points;
      if (!isStrArray(s.input)) err(`${at}: input must be a non-empty array of lines`);
      else if (s.input[s.input.length - 1].trim() !== 'exit') err(`${at}: input must end with "exit"`);
      if (!isStrArray(s.expected) || normalizeOutput(linesToText(s.expected)).length === 0) err(`${at}: expected output must not be empty`);
      if (Array.isArray(s.input) && s.input.some((l) => /[\r\n]/.test(l))) err(`${at}: input lines must not contain line breaks`);
    }
    if (isInt(d.max_points) && sum !== d.max_points) err(`scenario points add up to ${sum}, not ${d.max_points}`);

    // every command used in a scenario must be named in both briefs as `command`
    const commands = new Set(sc.flatMap((s) => (Array.isArray(s.input) ? s.input : []).map((l) => l.trim().split(/\s+/)[0])));
    for (const lang of ['sk', 'en']) {
      const text = Array.isArray(d[lang]?.brief) ? d[lang].brief.join('\n') : '';
      for (const c of commands) if (c && !text.includes('`' + c)) err(`${lang}.brief never mentions the command \`${c}\``);
    }
  }

  if (a.solution == null) err('Solution.cs is missing');
  return { errors, warnings };
}
