"""Check public navigation and session boundaries with small public fixtures.

Run: python -B verification/navigation_smoke.py
Uses an isolated HTTP test server; no scientific calculations or external calls.
"""
import asyncio
import json
from pathlib import Path
import re
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aiohttp import DummyCookieJar
from aiohttp.test_utils import TestClient, TestServer
from web_app import server


async def main():
    checks = []
    origin = 'https://rmo.example'
    navigation = {'Sec-Fetch-Site': 'cross-site',
                  'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Dest': 'document'}

    def check(name, passed):
        checks.append({'name': name, 'pass': bool(passed)})
        assert passed, name

    with tempfile.TemporaryDirectory(prefix='rmo-navigation-') as folder:
        public = Path(folder)
        (public / 'index.html').write_text(
            '<html><script id="local-config" type="application/json">'
            '{"enabled":false}</script></html>')
        (public / 'assets').mkdir()
        asset_name = '0' * 64 + '.txt'
        (public / 'assets' / asset_name).write_text('public fixture')
        with patch.object(server, 'PUBLIC', public):
            app = server.create_app([origin])
        async with TestClient(TestServer(app), cookie_jar=DummyCookieJar()) as client:
            async def request(method, path, extra=None):
                return await client.request(
                    method, path, headers={'Host': 'rmo.example', **(extra or {})})

            async with await request('GET', '/', navigation) as response:
                text = await response.text()
                check('external link opens application', response.status == 200)
                config = json.loads(re.search(
                    r'<script id="local-config" type="application/json">(.*?)</script>',
                    text).group(1))
                cookie = response.headers['Set-Cookie']
                check('navigation retains protected cookie', all(
                    value in cookie for value in ('Secure', 'HttpOnly', 'SameSite=Strict')))
                check('navigation retains response isolation',
                      response.headers['X-Frame-Options'] == 'DENY'
                      and response.headers['Cross-Origin-Opener-Policy'] == 'same-origin'
                      and response.headers['Cache-Control'] == 'no-store')
                check('navigation uses configured origin', config['origin'] == origin)
                session_headers = {'Cookie': cookie.split(';', 1)[0],
                                   'X-RMO-Token': config['token'], 'Origin': origin,
                                   'Sec-Fetch-Site': 'same-origin'}

            for site in ('cross-site', 'same-site'):
                for method in ('GET', 'HEAD'):
                    async with await request(method, '/', {**navigation, 'Sec-Fetch-Site': site}) as response:
                        check(f'{site} {method} document navigation', response.status == 200)
                for mode, dest in (('cors', 'empty'), ('no-cors', 'image'),
                                   ('navigate', 'iframe'), ('navigate', 'frame'),
                                   ('navigate', 'empty'), ('cors', 'document')):
                    async with await request('GET', '/', {
                        'Sec-Fetch-Site': site, 'Sec-Fetch-Mode': mode,
                        'Sec-Fetch-Dest': dest}) as response:
                        check(f'{site} {mode}/{dest} blocked', response.status == 403)
                async with await request('GET', '/', {'Sec-Fetch-Site': site}) as response:
                    check(f'{site} without navigation metadata blocked', response.status == 403)
                for method, path in (('GET', '/api/status'), ('POST', '/api/run'),
                                     ('POST', '/api/diagnose'), ('POST', '/api/cancel'),
                                     ('GET', '/assets/' + asset_name)):
                    async with await request(method, path, {
                        **session_headers, **navigation, 'Sec-Fetch-Site': site}) as response:
                        check(f'{site} cannot extend navigation exception to {path}', response.status == 403)

            for site in (None, 'none', 'same-origin'):
                extra = {} if site is None else {'Sec-Fetch-Site': site}
                async with await request('GET', '/', extra) as response:
                    check(f'existing direct/same-origin access: {site}', response.status == 200)
            async with await request('POST', '/', navigation) as response:
                check('navigation does not enable POST on root', response.status == 405)
            async with await request('GET', '/', {**navigation, 'Host': 'foreign.example',
                                                  'X-Forwarded-Host': 'rmo.example'}) as response:
                check('navigation does not bypass Host allowlist', response.status == 403)
            async with await request('GET', '/api/status', session_headers) as response:
                check('same-origin session still works', response.status == 200)
            for extra, label in (({'X-RMO-Token': 'invalid'}, 'wrong token'),
                                 ({'Cookie': ''}, 'missing session'),
                                 ({'Origin': 'https://foreign.example'}, 'foreign Origin')):
                async with await request('GET', '/api/status', {**session_headers, **extra}) as response:
                    check(f'API rejects {label}', response.status == 403)
            async with await request('GET', '/', navigation) as response:
                text = await response.text()
                other = json.loads(re.search(
                    r'<script id="local-config" type="application/json">(.*?)</script>', text).group(1))
                other_cookie = response.headers['Set-Cookie'].split(';', 1)[0]
                check('separate navigation sessions have distinct tokens', other['token'] != config['token'])
            async with await request('GET', '/api/status', {
                **session_headers, 'Cookie': other_cookie}) as response:
                check('another session cannot reuse first token', response.status == 403)
            check('navigation never starts a calculation', not app[server.STATE].busy
                  and not app[server.STATE].tasks and app[server.STATE].output is None)

    print(json.dumps({'checks': checks, 'all_recorded_checks_pass': True}, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
