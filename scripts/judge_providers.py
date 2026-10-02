"""One GPT-5.6 Luna review per project through ChatGPT-authenticated Codex."""
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

METHOD_VERSION = 4
SERVICE_TIER = 'default'
SCRIPTS = Path(__file__).resolve().parent
JUDGES = (
    {'label': 'luna56', 'name': 'GPT-5.6 Luna', 'provider': 'codex', 'id': 'gpt-5.6-luna'},
)

def check_budget(judge):
    if judge['provider'] != 'codex' or judge['id'] != 'gpt-5.6-luna':
        raise RuntimeError('Only GPT-5.6 Luna is active in this queue.')

def require_subscription():
    cli = executable('codex')
    if not cli:
        raise RuntimeError('Codex CLI not found.')
    result = subprocess.run([cli, 'login', 'status'], capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=30,
                            env=environment(JUDGES[0]))
    if result.returncode or 'logged in using chatgpt' not in (result.stdout + result.stderr).lower():
        raise RuntimeError('Нужен вход Codex через ChatGPT (codex login). API-доступ запрещён для этой очереди.')

def executable(provider):
    if provider == 'codex':
        return shutil.which('codex')
    return None

def command(judge, prompt_file, session):
    check_budget(judge)
    cli = executable(judge['provider'])
    if not cli:
        raise RuntimeError(f"CLI missing: {judge['provider']}")
    if judge['provider'] == 'codex':
        return [cli, 'exec', '--ignore-user-config', '--model', judge['id'],
                '-c', 'model_provider="openai"', '-c', 'forced_login_method="chatgpt"',
                '-c', 'model_reasoning_effort="'+os.environ.get('HACKALEM_JUDGE_REASONING','high')+'"', '-c', f'service_tier="{SERVICE_TIER}"',
                '-c', 'approval_policy="never"', '--sandbox', 'danger-full-access',
                '--skip-git-repo-check', '--cd', str(session), '--json', '--color', 'never',
                f'Read {prompt_file} and follow the instructions. Write the full JSON report to the requested file. Do not use browsers, skills, or subagents.']

def environment(judge, session=None):
    env = {**os.environ, 'NO_COLOR': '1', 'GIT_TERMINAL_PROMPT': '0'}
    # Inherit no provider keys into the agent's tool processes.
    for name in list(env):
        if (name.upper().endswith(('_API_KEY', '_API_TOKEN', '_SECRET_KEY'))
                or name.upper() in ('OPENAI_BASE_URL', 'CODEX_THREAD_ID')):
            env.pop(name)
    if session is not None:
        # Disposable caches belong to the participant workspace on D:, not C:.
        cache = Path(session)/'cache'
        temporary = Path(session)/'tmp'
        temporary.mkdir(parents=True, exist_ok=True)
        for key, folder in {'UV_CACHE_DIR':'uv','PIP_CACHE_DIR':'pip',
                            'npm_config_cache':'npm','HF_HOME':'huggingface',
                            'TORCH_HOME':'torch','XDG_CACHE_HOME':'xdg',
                            'BUN_INSTALL_CACHE_DIR':'bun','NODE_COMPILE_CACHE':'node-compile',
                            'PYTHONPYCACHEPREFIX':'pycache',
                            'HF_HUB_CACHE':'huggingface/hub',
                            'HF_DATASETS_CACHE':'huggingface/datasets'}.items():
            target=cache/folder
            target.mkdir(parents=True, exist_ok=True)
            env[key]=str(target.resolve())
        env.update(TEMP=str(temporary.resolve()),TMP=str(temporary.resolve()))
    return env

def run_process(args, cwd, events, diagnostic, env, timeout=10800, idle_timeout=1200):
    """Allow active work past one hour; stop silent sessions and retain streams."""
    with events.open('w', encoding='utf-8') as out, diagnostic.open('w', encoding='utf-8') as err:
        process = subprocess.Popen(args, cwd=cwd, stdin=subprocess.DEVNULL,
                                   stdout=out, stderr=err, env=env)
        try:
            started = last_activity = time.monotonic()
            sizes = (0, 0)
            while True:
                try:
                    return process.wait(timeout=min(5,timeout))
                except subprocess.TimeoutExpired:
                    now = time.monotonic()
                    current = (events.stat().st_size, diagnostic.stat().st_size)
                    if current != sizes:
                        last_activity, sizes = now, current
                    if now-started >= timeout or now-last_activity >= idle_timeout:
                        error = subprocess.TimeoutExpired(args,timeout)
                        error.reason = 'idle_timeout' if now-last_activity >= idle_timeout else 'time_budget'
                        raise error
        except BaseException:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
            else:
                process.kill()
            process.wait()
            raise

def event_summary(path):
    usage = {'inputTokens': 0, 'cachedInputTokens': 0, 'outputTokens': 0,
             'reasoningTokens': 0, 'reportedTurns': 0, 'reportedCost': 0}
    session = None
    errors = []
    texts = []
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        session = event.get('thread_id', event.get('sessionID', event.get('session_id', session)))
        if event.get('type') in ('turn.completed', 'turn.failed'):
            counts = event.get('usage') or {}
            usage['inputTokens'] += counts.get('input_tokens', 0)
            usage['cachedInputTokens'] += counts.get('cached_input_tokens', counts.get('input_tokens_details', {}).get('cached_tokens', 0))
            usage['outputTokens'] += counts.get('output_tokens', 0)
            usage['reasoningTokens'] += counts.get('output_tokens_details', {}).get('reasoning_tokens', 0)
            usage['reportedTurns'] += bool(counts)
            if event.get('type') == 'turn.failed':
                errors.append(json.dumps(event, ensure_ascii=False)[-2000:])
        if event.get('type') == 'item.completed' and event.get('item', {}).get('type') == 'agent_message':
            texts.append(event['item'].get('text', ''))
        part = event.get('part', {})
        if event.get('type') == 'text':
            texts.append(part.get('text', ''))
        if event.get('type') == 'step_finish':
            tokens = part.get('tokens', {})
            usage['inputTokens'] += tokens.get('input', 0)
            usage['cachedInputTokens'] += tokens.get('cache', {}).get('read', 0)
            usage['outputTokens'] += tokens.get('output', 0)
            usage['reasoningTokens'] += tokens.get('reasoning', 0)
            usage['reportedCost'] += part.get('cost', 0)
            usage['reportedTurns'] += 1
        if event.get('type') == 'result':
            texts.append(event.get('result', ''))
            usage['reportedCost'] += event.get('total_cost_usd',0)
            usage['reportedCredits'] = usage.get('reportedCredits',0) + event.get('total_credits',0)
            counts = event.get('usage') or {}
            usage['inputTokens'] += counts.get('input_tokens', counts.get('inputTokens', 0))
            usage['cachedInputTokens'] += counts.get('cache_read_input_tokens', counts.get('cacheReadInputTokens', 0))
            usage['outputTokens'] += counts.get('output_tokens', counts.get('outputTokens', 0))
            usage['reportedTurns'] += bool(counts)
        if event.get('type') == 'error' or event.get('is_error'):
            errors.append(json.dumps(event, ensure_ascii=False)[-2000:])
    return session, usage, '\n'.join(errors), texts
