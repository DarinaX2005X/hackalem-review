import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../web/app.js',import.meta.url),'utf8');
const bindings=source.match(/^\s*(?:document|results)\.querySelectorAll\('[^']*(?:data-filter|data-page)[^']*'\).*$/gm).join('\n');
const updateParam=source.match(/^function updateParam\(.*$/m)[0];

// Event-only test doubles: no browser, layout engine or native picker simulation.
class Control {
  constructor(dataset={},parent=null){this.dataset=dataset;this.parent=parent;this.listeners={};this.value='';}
  addEventListener(type,listener){(this.listeners[type]??=[]).push(listener);}
  dispatch(type){
    // A click keeps bubbling along the original path after a results redraw.
    const path=[];
    for(let node=this;node;node=node.parent)path.push(node);
    for(const node of path)for(const listener of [...(node.listeners[type]||[])])listener();
  }
}

function catalog(){
  const params=new URLSearchParams('language=Python&page=2');
  const main=new Control({page:'catalog',route:'catalog'});
  const results=new Control({},main);
  let filters,buttons,redraws=0,scrolls=0;
  const urls=[];
  const query=(selector,includeMain=false)=>{
    if(selector.includes('[data-filter]'))return filters;
    if(selector.includes('[data-page]'))return includeMain&&selector==='[data-page]'?[main,...buttons]:buttons;
    throw Error('Unexpected selector: '+selector);
  };
  results.querySelectorAll=selector=>query(selector);
  results.scrollIntoView=()=>scrolls++;
  const context=vm.createContext({
    params,results,
    document:{querySelectorAll:selector=>query(selector,true),querySelector:()=>results},
    history:{replaceState:(_state,_title,url)=>urls.push(url)},
    renderCatalogResults:()=>{redraws++;bind();},
  });
  function bind(){
    filters=['case','language','readme','size','sort'].map(filter=>new Control({filter},results));
    buttons=[1,2,3,36].map(page=>new Control({page:String(page)},results));
    vm.runInContext(updateParam+'\n'+bindings,context);
  }
  bind();
  return {params,urls,get filters(){return filters;},get buttons(){return buttons;},get redraws(){return redraws;},get scrolls(){return scrolls;}};
}

test('Opening all five catalog filters leaves their controls attached and the URL unchanged',()=>{
  const state=catalog(),original=state.filters;
  for(const filter of original)filter.dispatch('click');
  assert.equal(state.redraws,0);
  assert.equal(state.filters,original);
  assert.equal(state.params.get('page'),'2');
  assert.deepEqual(state.urls,[]);
});

test('Each filter applies its value once and resets pagination only after a change',()=>{
  const state=catalog();
  for(const [index,value] of ['1','JavaScript','yes','3','score-asc'].entries()){
    state.params.set('page','2');
    const filter=state.filters[index];
    filter.value=value;
    filter.dispatch('change');
    filter.dispatch('click');
    assert.equal(state.params.get(filter.dataset.filter),value);
    assert.equal(state.params.has('page'),false);
    assert.equal(state.redraws,index+1);
  }
  assert.equal(state.scrolls,0);
});

test('Repeated page clicks preserve filters and perform exactly one transition each',()=>{
  const state=catalog();
  for(const [index,page] of [3,36,1,2].entries()){
    state.buttons.find(button=>button.dataset.page===String(page)).dispatch('click');
    assert.equal(state.params.get('page'),String(page));
    assert.equal(state.params.get('language'),'Python');
    assert.equal(state.redraws,index+1);
    assert.equal(state.scrolls,index+1);
    assert.equal(state.urls.length,index+1);
  }
});

test('A review refresh waits for a focused native select even if it opens during the fetch',async()=>{
  const refresh=source.slice(source.indexOf('async function refreshReviews(){'),source.indexOf('async function init(){'));
  const next={reviews:[{repoId:'new',score:70}]};
  const picker={tagName:'SELECT'};
  let renders=0,scrolls=0;
  const context=vm.createContext({
    data:{},route:'catalog',reviewIndex:{reviews:[]},reviewFingerprint:'old',
    document:{hidden:false,activeElement:null},
    main:{contains:element=>element===picker,querySelectorAll:()=>[]},
    window:{scrollY:123,scrollTo:()=>scrolls++},
    renderRoute:()=>renders++,
    fetch:async()=>({ok:true,json:async()=>{context.document.activeElement=picker;return next;}}),
  });
  await vm.runInContext(refresh+'\nrefreshReviews()',context);
  assert.equal(renders,0);
  assert.equal(context.reviewFingerprint,'old');
  context.document.activeElement=null;
  context.fetch=async()=>({ok:true,json:async()=>next});
  await vm.runInContext('refreshReviews()',context);
  assert.equal(renders,1);
  assert.equal(scrolls,1);
  assert.equal(context.reviewIndex,next);
});
