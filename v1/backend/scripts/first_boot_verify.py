from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from typing import Any


def print_step(name: str, payload: object) -> None:
    print(f'\n== {name} ==')
    if isinstance(payload, (dict, list)):
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload)


def request_json(
    base_url: str,
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    files: dict[str, tuple[str, bytes, str]] | None = None,
    timeout: int = 10,
) -> dict[str, Any]:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    elif files is not None:
        boundary = 'mini-ragflow-first-boot-boundary'
        body = bytearray()
        for field_name, (filename, content, content_type) in files.items():
            body.extend(f'--{boundary}\r\n'.encode('utf-8'))
            body.extend(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode('utf-8')
            )
            body.extend(f'Content-Type: {content_type}\r\n\r\n'.encode('utf-8'))
            body.extend(content)
            body.extend(b'\r\n')
        body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
        data = bytes(body)
        headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'

    request = urllib.request.Request(f'{base_url.rstrip("/")}{path}', data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def wait_for_api(base_url: str, timeout_sec: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_sec
    last_error = None
    while time.monotonic() < deadline:
        try:
            data = request_json(base_url, 'GET', '/health')
            if data.get('status') == 'ok':
                return data
        except Exception as exc:
            last_error = str(exc)
        time.sleep(2)
    raise RuntimeError(f'API did not become healthy within {timeout_sec}s: {last_error}')


def wait_for_job(base_url: str, job_id: int, timeout_sec: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        data = request_json(base_url, 'GET', f'/api/jobs/{job_id}')
        if data.get('status') in {'done', 'error'}:
            return data
        time.sleep(1)
    raise RuntimeError(f'job {job_id} did not finish within {timeout_sec}s')


def main() -> int:
    parser = argparse.ArgumentParser(description='Verify first boot of Mini RAGFlow.')
    parser.add_argument('base_url_arg', nargs='?', help='API base URL')
    parser.add_argument('--base-url', default=None)
    parser.add_argument('--timeout-sec', type=int, default=90)
    args = parser.parse_args()
    base_url = args.base_url or args.base_url_arg or 'http://127.0.0.1:8010'

    sample_text = (
        'RAG Knowledge Assistant is a FastAPI and Postgres pgvector RAG system. '
        'It supports async ingestion jobs, hybrid retrieval, citations, and stored eval runs.'
    )

    health = wait_for_api(base_url, args.timeout_sec)
    print_step('health', health)

    frontend_html = urllib.request.urlopen(f'{base_url.rstrip("/")}/', timeout=10).read().decode('utf-8')
    if 'RAG Knowledge Assistant' not in frontend_html:
        raise RuntimeError('frontend did not render expected RAG Knowledge Assistant page')
    print_step('frontend', 'ok')

    files = {'file': ('first_boot.txt', sample_text.encode('utf-8'), 'text/plain')}
    ingest_data = request_json(base_url, 'POST', '/api/ingest-file-async', files=files)
    print_step('queued_job', ingest_data)

    job_data = wait_for_job(base_url, int(ingest_data['job_id']), args.timeout_sec)
    print_step('job_status', job_data)
    if job_data.get('status') != 'done':
        raise RuntimeError(f'worker failed first-boot ingestion: {job_data}')

    ask_data = request_json(
        base_url,
        'POST',
        '/api/ask',
        payload={'question': 'What does RAG Knowledge Assistant support?', 'top_k': 3},
    )
    print_step('ask', ask_data)
    if not ask_data.get('citations'):
        raise RuntimeError('ask response did not include citations')

    eval_data = request_json(base_url, 'POST', '/api/eval/run', payload={'eval_set': 'default', 'top_k': 3})
    print_step('eval_run', eval_data)

    summary_data = request_json(base_url, 'GET', f"/api/eval/runs/{int(eval_data['run_id'])}")
    print_step('eval_summary', summary_data)

    print('\nFirst-boot verification passed.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'\nFirst-boot verification failed: {exc}', file=sys.stderr)
        raise SystemExit(1)
