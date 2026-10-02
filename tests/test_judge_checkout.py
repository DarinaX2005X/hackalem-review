import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('judge_checkout',ROOT/'scripts/judge_checkout.py')
checkout=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkout)


class CheckoutTest(unittest.TestCase):
    def test_host_mapping_is_unambiguous_and_stays_relative(self):
        self.assertEqual(checkout.windows_path('folder /file.py'),'folder%20/file.py')
        self.assertEqual(checkout.windows_path('folder%20/file.py'),'folder%2520/file.py')
        self.assertEqual(checkout.windows_path('NUL.txt'),'%4EUL.txt')
        for name in ('../escape','/absolute','a/../../escape'):
            with self.assertRaises(ValueError):checkout.windows_path(name)

    def test_git_tree_with_trailing_space_preserves_every_blob(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); clone=root/'repo'; clone.mkdir()
            def git(*args,cwd=clone,input=None,timeout=30):
                p=subprocess.run(['git','-c','safe.directory=*',*args],cwd=cwd,
                    input=input.encode() if input is not None else None,capture_output=True,timeout=timeout)
                if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
                return p.stdout.decode().strip()
            git('init','--quiet')
            git('config','user.name','Test');git('config','user.email','test@example.invalid')
            blob=git('hash-object','-w','--stdin',input='unchanged source\n')
            tree=git('mktree',input=f'100644 blob {blob}\tANALYSIS.md\n')
            outer=git('mktree',input=f'040000 tree {tree}\tbeeline_case_participants \n')
            snapshot=git('commit-tree',outer,input='fixture\n')
            target=root/'review'
            checkout.create_checkout(clone,target,snapshot,git)
            self.assertEqual((target/'beeline_case_participants%20/ANALYSIS.md').read_bytes(),b'unchanged source\n')
            mapping=json.loads((root/'review-paths.json').read_text())
            self.assertEqual(mapping['paths'][0]['original'],'beeline_case_participants /ANALYSIS.md')
            import tarfile
            with tarfile.open(root/'review-source.tar') as archive:
                self.assertEqual(archive.extractfile('beeline_case_participants /ANALYSIS.md').read(),b'unchanged source\n')

    def test_snapshot_blobs_are_fetched_together_and_retry_transient_failure(self):
        calls=[]; fetches=0
        def git(*args,**kwargs):
            nonlocal fetches
            calls.append((args,kwargs))
            if args[0]=='rev-list':return '?'+('a'*40)+'\n?'+('b'*40) if fetches<2 else ''
            fetches+=1
            if fetches==1:raise RuntimeError('network timeout')
            return ''
        checkout.hydrate_snapshot(Path('fixture'),'snapshot',git)
        self.assertEqual(fetches,2)
        self.assertEqual(calls[1][1]['input'],'a'*40+'\n'+'b'*40+'\n')


if __name__=='__main__':unittest.main()
