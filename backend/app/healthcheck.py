from __future__ import annotations

import asyncio
import sys
import urllib.request

from sqlalchemy import text

from app.db import SessionLocal


async def check_db() -> int:
    async with SessionLocal() as session:
        await session.execute(text('SELECT 1'))
    return 0


def check_api() -> int:
    with urllib.request.urlopen('http://127.0.0.1:8010/health', timeout=3) as response:
        return 0 if response.status == 200 else 1


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else 'db'
    if target == 'api':
        return check_api()
    if target in {'db', 'worker'}:
        return asyncio.run(check_db())
    print(f'unknown healthcheck target: {target}', file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
