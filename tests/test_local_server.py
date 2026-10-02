"""Windows integration regression: catalog outlives a killed launcher tree."""

import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('local_server', ROOT/'scripts/ensure-local-server.py')
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


@unittest.skipUnless(os.name == 'nt' and os.environ.get('HACKALEM_SERVER_INTEGRATION') == '1',
                     'Opt in to the Windows Task Scheduler lifecycle test')
class IndependentServerTest(unittest.TestCase):
    def test_survives_launcher_tree_and_recovers_node_crash(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        launcher = subprocess.Popen([
            sys.executable, '-c',
            'import subprocess,sys,time; '
            'subprocess.run([sys.executable,"-X","utf8",sys.argv[1],"--port",sys.argv[2]],check=True); '
            'time.sleep(90)', str(ROOT/'scripts/ensure-local-server.py'), str(port)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            self.wait_for(lambda: server.healthy(port), 30)
            killed = subprocess.run(['taskkill', '/PID', str(launcher.pid), '/T', '/F'],
                                    capture_output=True)
            self.assertEqual(killed.returncode, 0)
            launcher.wait(timeout=5)
            self.assertTrue(server.healthy(port), 'Server died with its launcher')
            # Resolve only our test port's listener; never kill all node processes.
            ps = f'(Get-NetTCPConnection -LocalPort {port} -State Listen).OwningProcess'
            pid = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command', ps], text=True).strip()
            self.assertTrue(pid.isdigit())
            subprocess.run(['taskkill', '/PID', pid, '/F'], check=True, capture_output=True)
            self.wait_for(lambda: server.healthy(port), 15)
            new_pid = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command', ps], text=True).strip()
            self.assertNotEqual(pid, new_pid, 'Supervisor did not replace the crashed server')
        finally:
            if launcher.poll() is None:
                subprocess.run(['taskkill', '/PID', str(launcher.pid), '/T', '/F'], capture_output=True)
                launcher.wait(timeout=5)
            task = server.task_name(port)
            subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                            f'Stop-ScheduledTask -TaskName "{task}" -ErrorAction SilentlyContinue; '
                            f'Unregister-ScheduledTask -TaskName "{task}" -Confirm:$false -ErrorAction SilentlyContinue'],
                           capture_output=True, check=True)

    def wait_for(self, predicate, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.25)
        self.fail('Timed out waiting for the catalog HTTP response')
