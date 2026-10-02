import {test} from 'node:test';
import assert from 'node:assert/strict';
import {rankingMarks} from '../web/ranking.js';

const rows=scores=>scores.map((score,i)=>({repoId:`team-${i}`,caseId:1,score,status:'complete'}));
test('Only ties beyond the fifth entry become reserves',()=>{
 const result=rankingMarks(rows([100,99,98,90,90,90,90,89]));
 assert.equal([...result.values()].filter(r=>r.kind==='top').length,5);
 assert.equal(result.get('team-5').kind,'reserve');
 assert.equal(result.get('team-6').kind,'reserve');
 assert.equal(result.has('team-7'),false);
 assert.equal(rankingMarks(rows([100,99,98,90,90,89])).has('team-5'),false);
});
test('Case scope, incomplete lists, disqualification and raw scores are respected',()=>{
 assert.equal(rankingMarks(rows([90,90,90,90])).size,4);
 const input=rows([100,99,98,90,90,90]);
 input[0].status='late_submission';
 assert.equal(rankingMarks(input).get('team-5').kind,'top');
 input[0].status='no_commits';
 assert.equal(rankingMarks(input).has('team-0'),false);
 assert.equal(rankingMarks(input,2).size,0);
 assert.equal(rankingMarks(rows([100,99,98,95,90.001,90.0009])).has('team-5'),false);
});
test('All reserves remain marked even beyond the first ten entries',()=>{
 const result=rankingMarks(rows(Array(15).fill(80)));
 assert.equal([...result.values()].filter(r=>r.kind==='reserve').length,10);
});
