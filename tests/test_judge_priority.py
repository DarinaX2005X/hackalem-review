import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

spec=importlib.util.spec_from_file_location('judge_priority',Path(__file__).resolve().parents[1]/'scripts/judge_priority.py')
priority=importlib.util.module_from_spec(spec);spec.loader.exec_module(priority)

class PriorityTest(unittest.TestCase):
    def test_multiple_pending_projects_are_processed_in_order(self):
        requests=[{'repoId':name,'status':'pending','afterCase':12,'beforeCase':2} for name in ['aid','havefun','a7']]
        document={'requests':requests};queue=Mock();queue.read.return_value=document
        projects={name:{'caseId':4} for name in ['aid','havefun','a7']}|{'next':{'caseId':2}}
        called=[]
        def execute(root,work,request,queue,save):
            called.append(request['repoId']);request['status']='complete';save();return False
        with patch.object(priority,'run_request',execute):
            self.assertFalse(priority.run(Path('.'),Path('.'),projects,['next'],'all-case-2-wave',queue))
        self.assertEqual(called,['aid','havefun','a7'])
        self.assertTrue(all(r['status']=='complete' for r in document['requests']))

    def test_waits_for_next_case_and_does_not_recurse(self):
        request={'status':'pending','repoId':'aid','afterCase':12,'beforeCase':2}
        projects={'aid':{'caseId':4},'current':{'caseId':12},'next':{'caseId':2}}
        self.assertFalse(priority.due(request,projects,['current'],'all-case-12-wave'))
        self.assertTrue(priority.due(request,projects,['next'],'all-case-2-wave'))
        self.assertFalse(priority.due(request,projects,['next'],'priority-aid'))
        self.assertFalse(priority.due(request|{'status':'running'},projects,['next'],'all-case-2-wave'))

    def test_review_publish_and_cleanup_are_serial_and_saved(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);queue=Mock();events=[];saved=[]
            queue.read.side_effect=[{'status':'pending','repoId':'aid','afterCase':12,'beforeCase':2},[]]
            queue.done.side_effect=[False,True]
            queue.write.side_effect=lambda path,value:saved.append(dict(value))
            queue.finish_wave_cleanup.side_effect=lambda *args:events.append('cleanup') or []
            def execute(command,**kwargs):
                events.append(Path(command[3]).name)
                if len(events)==1:self.assertIn('--skip-priority',command)
                return Mock(returncode=0)
            with patch.object(priority.subprocess,'run',execute):
                self.assertFalse(priority.run(root,root,{'aid':{'caseId':4},'next':{'caseId':2}},['next'],'all-case-2-wave',queue))
            self.assertEqual(events,['judge-wave.py','publish-reviews.py','prepare-pages.py','cleanup'])
            self.assertEqual([r['status'] for r in saved],['running','complete'])
