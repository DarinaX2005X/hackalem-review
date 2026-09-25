import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const catalog=JSON.parse(await readFile(new URL('../web/data/catalog.json',import.meta.url),'utf8'));
const exclusions=JSON.parse(await readFile(new URL('../data/exclusions.json',import.meta.url),'utf8'));
test('Every included project belongs to exactly one real case',()=>{
 assert.equal(new Set(catalog.projects.map(p=>p.id)).size,catalog.projects.length);
 for(const p of catalog.projects){assert.ok(Number.isInteger(p.caseId)&&p.caseId>=1&&p.caseId<=12,p.id);assert.ok(!exclusions[p.id],p.id);assert.equal(p.classification.caseId,p.caseId);assert.ok(!('scores' in p.classification));}
});
test('Case counts and exclusion counts reconcile with the original list',()=>{
 assert.equal(catalog.cases.reduce((n,c)=>n+c.count,0),catalog.projects.length);
 assert.equal(catalog.initialListCount-catalog.excludedCount,catalog.projects.length);
 for(const c of catalog.cases)assert.equal(c.count,catalog.projects.filter(p=>p.caseId===c.id).length);
 assert.equal(catalog.coverage.unresolved,0);
});
test('Unperformed reviews and missing team data are never fabricated',()=>{
 for(const p of catalog.projects){assert.equal(p.reviewStatus,'not_started');assert.equal(p.allMembersCommitted,null);assert.ok(!('score' in p));if(p.teamSize!==null)assert.equal(p.teamSize,p.members.length);}
});
test('Static asset paths work on GitHub project Pages',async()=>{
 const html=await readFile(new URL('../docs/index.html',import.meta.url),'utf8');
 const app=await readFile(new URL('../docs/app.js',import.meta.url),'utf8');
 assert.ok(!/(?:href|src)="\/(?!\/)/.test(html));
 assert.ok(app.includes("fetch('./data/catalog.json')"));
 const publicData=JSON.parse(await readFile(new URL('../docs/data/catalog.json',import.meta.url),'utf8'));
 assert.deepEqual(publicData,catalog);
});
