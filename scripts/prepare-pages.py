"""Copy the locally tested static site to the future GitHub Pages directory."""

from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
shutil.copytree(ROOT/'web',ROOT/'docs',dirs_exist_ok=True)
(ROOT/'docs'/'.nojekyll').write_text('',encoding='utf-8')
print('Static GitHub Pages bundle ready')
