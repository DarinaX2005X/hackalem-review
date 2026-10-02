import {test} from 'node:test';
import assert from 'node:assert/strict';
import guard from '../scripts/judge-opencode-guard.mjs';

test('OpenCode guard rejects the exact commands that killed the queue',async()=>{
 let hook;
 await guard.setup({tool:{hook:async(name,fn)=>{assert.equal(name,'execute.before');hook=fn;}}});
 for(const command of ['Get-Process -Name python | Stop-Process -Force',
   'Get-Process -Name python,node | Stop-Process -Force',
   'taskkill /IM node.exe /F','pkill -f python','docker system prune --all --force']){
   assert.throws(()=>hook({tool:'shell',input:{command}}),/HOST_CLEANUP_BLOCKED/);
 }
 assert.doesNotThrow(()=>hook({tool:'shell',input:{command:'docker stop deepseek-12345678-api'}}));
 assert.doesNotThrow(()=>hook({tool:'shell',input:{command:'python scripts/validate-judge-report.py report.json'}}));
});
