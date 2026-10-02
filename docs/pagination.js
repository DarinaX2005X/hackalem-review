export function paginationPages(page,pages){
  const visible=new Set([1,2,pages-1,pages,page-1,page,page+1]);
  // Keep three consecutive pages at either end.
  if(page<=3)visible.add(3);
  if(page>=pages-2)visible.add(pages-2);
  const numbers=[...visible].filter(n=>n>=1&&n<=pages).sort((a,b)=>a-b);
  const result=[];
  for(const n of numbers){
    const previous=result.at(-1);
    if(n-previous===2)result.push(previous+1);
    else if(n-previous>2)result.push(null);
    result.push(n);
  }
  return result;
}

export function renderPaginationControls(page,pages){
  const chevron=direction=>`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${direction==='back'?'m14 6-6 6 6 6':'m10 6 6 6-6 6'}"/></svg>`;
  return `<nav class="pagination-controls" aria-label="Страницы каталога"><button class="page-button" data-page="${page-1}" aria-label="Предыдущая страница" ${page===1?'disabled':''}>${chevron('back')}</button>${paginationPages(page,pages).map(n=>n===null?'<span class="page-ellipsis" aria-hidden="true">…</span>':`<button class="page-button${n===page?' is-current':''}" data-page="${n}" aria-label="Страница ${n}" ${n===page?'aria-current="page"':''}>${n}</button>`).join('')}<button class="page-button" data-page="${page+1}" aria-label="Следующая страница" ${page===pages?'disabled':''}>${chevron('next')}</button></nav>`;
}
