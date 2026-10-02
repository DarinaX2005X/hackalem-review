// OpenCode v2 tool hook. This prevents accidental cleanup, not hostile code.
import {readFileSync} from 'node:fs';
const rules=JSON.parse(readFileSync(new URL('./judge-guard-rules.json',import.meta.url),'utf8'));
export default {
  id:'hackalem.host-cleanup-guard',
  async setup(ctx){
    await ctx.tool.hook('execute.before',event=>{
      const input=JSON.stringify(event.input??{});
      if(rules.patterns.some(p=>new RegExp(p,'i').test(input)))throw new Error(rules.reason);
    });
  }
};
