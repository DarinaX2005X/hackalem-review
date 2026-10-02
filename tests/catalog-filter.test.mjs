import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../web/app.js',import.meta.url),'utf8');
const filter=source.slice(source.indexOf('function filtered(){'),source.indexOf('function select('));
const projects=[
 {id:'a',name:'A',readmeStatus:'found',readmeTemplate:true},
 {id:'b',name:'B',readmeStatus:'found',readmeTemplate:false},
 {id:'c',name:'C',readmeStatus:'found',readmeTemplate:false},
];
function ids(query){
 const context={data:{projects},params:new URLSearchParams(query),reviewById:id=>({b:{score:90},c:{score:0}}[id])};
 return Array.from(vm.runInNewContext(filter+'; filtered().map(p=>p.id)',context));
}
test('Default score order includes zero scores before unreviewed projects',()=>{
 assert.deepEqual(ids(''),['b','c','a']);
 assert.deepEqual(ids('sort=name'),['a','b','c']);
 assert.deepEqual(ids('sort=name-desc'),['c','b','a']);
 assert.deepEqual(ids('sort=score-asc'),['c','b','a']);
 assert.deepEqual(ids('review=pending'),['b','c','a']);
});
test('Substantive README filter excludes starter templates',()=>{
 assert.deepEqual(ids('readme=yes'),['b','c']);
 assert.deepEqual(ids('readme=template'),['a']);
});

test('Evaluated counts include disqualifications once, including decisions without a judge report',()=>{
 const counters=source.slice(source.indexOf('const reviewedCount='),source.indexOf('const eligibleReviews='));
 const context={data:{projects:[
  {id:'scored',caseId:1},{id:'late',caseId:1},{id:'empty',caseId:2},
  {id:'pending',caseId:2},{id:'partial',caseId:2},
 ]},reviewIndex:{reviews:[{repoId:'scored',score:50},{repoId:'late',score:0}],
  partialReviews:[{repoId:'partial',score:null}],
  eligibility:{late:{status:'late_submission'},empty:{status:'no_commits'},unknown:{status:'no_commits'}}}};
 assert.deepEqual(Array.from(vm.runInNewContext(counters+'; [reviewedCount(),reviewedCount(1),reviewedCount(2)]',context)),[3,2,1]);
});
