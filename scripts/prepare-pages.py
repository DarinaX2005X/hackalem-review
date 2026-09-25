from pathlib import Path
import shutil,colorsys,re
ROOT=Path(__file__).resolve().parents[1]
style=ROOT/'web'/'style.css'
text=style.read_text(encoding='utf-8')
colors={'#f3f5f1':'#f6f3ef','#253b35':'#40372f','#63736b':'#786c62','#175746':'#a94531','#e7efe0':'#f5e3d9','#dde4dc':'#e8dfd6','#164d42':'#a94531','#f0f5db':'#fff5eb'}
def warm(match):
    value=match.group(0)
    if value in colors:return colors[value]
    hex=value[1:]
    if len(hex) not in (6,8):return value
    rgb=[int(hex[i:i+2],16)/255 for i in (0,2,4)]
    h,l,s=colorsys.rgb_to_hls(*rgb)
    if .17<h<.58 and s>.035:
        new=colorsys.hls_to_rgb(.055,l,s*.83)
        return '#'+''.join(f'{round(v*255):02x}' for v in new)+hex[6:]
    return value
text=re.sub(r'#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b',warm,text)
if '.sr-only{' not in text:text+='\n[hidden]{display:none!important}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}\n'
style.write_text(text,encoding='utf-8')
favicon=ROOT/'web'/'favicon.svg'
favicon.write_text(favicon.read_text(encoding='utf-8').replace('#164d42','#a94531').replace('#f0f5db','#fff5eb'),encoding='utf-8')
index=ROOT/'web'/'index.html'
index.write_text(index.read_text(encoding='utf-8').replace('#f3f5f1','#f6f3ef'),encoding='utf-8')
shutil.copytree(ROOT/'web',ROOT/'docs',dirs_exist_ok=True)
(ROOT/'docs'/'.nojekyll').write_text('',encoding='utf-8')
print('Terracotta theme and GitHub Pages bundle ready')
