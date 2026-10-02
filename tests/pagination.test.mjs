import {test} from 'node:test';
import assert from 'node:assert/strict';
import {paginationPages,renderPaginationControls} from '../web/pagination.js';

test('Pagination exposes both ends and the current neighborhood without false gaps',()=>{
  assert.deepEqual(paginationPages(1,36),[1,2,3,null,35,36]);
  assert.deepEqual(paginationPages(18,36),[1,2,null,17,18,19,null,35,36]);
  assert.deepEqual(paginationPages(36,36),[1,2,null,34,35,36]);
  assert.deepEqual(paginationPages(3,6),[1,2,3,4,5,6]);
  assert.deepEqual(paginationPages(1,1),[1]);
  for(let total=1;total<=36;total++)for(let page=1;page<=total;page++){
    const shown=paginationPages(page,total).filter(Number.isInteger);
    assert.equal(shown[0],1);
    assert.equal(shown.at(-1),total);
    assert.ok(shown.includes(page));
    assert.equal(new Set(shown).size,shown.length);
  }
});

test('Page navigation labels the active page and disables boundary arrows',()=>{
  assert.match(renderPaginationControls(1,36),/aria-label="Предыдущая страница" disabled/);
  assert.match(renderPaginationControls(36,36),/aria-label="Следующая страница" disabled/);
  assert.match(renderPaginationControls(18,36),/data-page="18" aria-label="Страница 18" aria-current="page"/);
});
