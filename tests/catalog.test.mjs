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
 for(const p of catalog.projects){assert.equal(p.reviewStatus,'not_started');assert.equal(p.allMembersCommitted,null);assert.ok(!('score' in p));assert.ok(p.teamSize===null||[1,2,3].includes(p.teamSize));if(p.teamSizeSource==='git_author_signatures')assert.ok(p.anonymousMembers?.length===p.teamSize);}
});
test('Static asset paths work on GitHub project Pages',async()=>{
 const html=await readFile(new URL('../docs/index.html',import.meta.url),'utf8');
 const app=await readFile(new URL('../docs/app.js',import.meta.url),'utf8');
 assert.ok(!/(?:href|src)="\/(?!\/)/.test(html));
 assert.ok(app.includes("fetch('./data/catalog.json')"));
 const publicData=JSON.parse(await readFile(new URL('../docs/data/catalog.json',import.meta.url),'utf8'));
 assert.deepEqual(publicData,catalog);
});
test('Every included project has a full local README and no excerpt panel',async()=>{
 const app=await readFile(new URL('../web/app.js',import.meta.url),'utf8');
 assert.ok(!app.includes('Фрагменты README'));
 for(const project of catalog.projects){const file=await readFile(new URL('../web/data/readmes/'+project.id+'.md',import.meta.url),'utf8');assert.ok(file.length>0,project.id);}
});
test('Only complete judge panels enter the public rating index',async()=>{
 const index=JSON.parse(await readFile(new URL('../web/data/reviews/index.json',import.meta.url),'utf8'));
 for(const row of index.reviews){
  assert.ok([3,4].includes(row.methodVersion));
  const project=catalog.projects.find(p=>p.id===row.repoId);assert.ok(project);
  if(row.status==='late_submission'){
   assert.equal(row.score,0);assert.equal(row.expectedJudges,0);assert.deepEqual(row.judgeScores,[]);
   const decision=JSON.parse(await readFile(new URL('../web/data/reviews/'+row.repoId+'.json',import.meta.url),'utf8'));
   assert.ok(Date.parse(decision.firstSolutionCommitAt)>Date.parse(decision.deadlineUtc));
   continue;
  }
  const scores=row.methodVersion===4?row.judgeScores.map(j=>j.score):[row.sol,row.luna];
  assert.equal(scores.length,row.expectedJudges??2);
  assert.ok(scores.every(Number.isFinite));
  assert.equal(row.score,Math.round(scores.reduce((a,b)=>a+b,0)/scores.length*100)/100);
  const detail=JSON.parse(await readFile(new URL('../web/data/reviews/'+row.repoId+'.json',import.meta.url),'utf8'));
  assert.equal(detail.repoUrl,project.url);
  assert.equal(detail.snapshot,detail.judges[0].snapshot);
  assert.ok(detail.judges.every(j=>j.snapshot===detail.snapshot));
  assert.equal(detail.judges.length,row.expectedJudges??2);
  for(const judge of detail.judges){
   assert.equal(judge.global.criteria.length,5);
   assert.equal(judge.global.total,judge.global.criteria.reduce((sum,item)=>sum+item.score,0));
   assert.ok(judge.testData.checks.length>0);
   assert.ok(!judge.gaps.length||judge.futureAdvice.length>0);
  }
 }
});
