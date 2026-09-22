"""Serve reviewed public assets and bounded, isolated calculation requests."""
import argparse
import asyncio
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import secrets
import threading
import time
import uuid
from urllib.parse import urlsplit

from aiohttp import web
from synthetic_adapter.input import OUTER_LIMIT, encode, strict_load, unpack
from synthetic_adapter.runner import run, matches_input
from uncertainty_diagnosis.service import validate, run as run_diagnosis

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
VERSION = '1.0.0'
SESSION_SECONDS = 3600
MAX_SESSIONS = 128
MAX_ATTEMPTS = 32
COOKIE = 'rmo_session'
CSP = ("default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'unsafe-inline'; "
       "connect-src 'self'; img-src 'self' data:; media-src 'self' data:; frame-src blob:; "
       "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")

@dataclass
class Session:
    token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    expires: float = field(default_factory=lambda: time.monotonic() + SESSION_SECONDS)
    seen: set = field(default_factory=set)
    early_cancel: dict = field(default_factory=dict)
    active: tuple | None = None

class State:
    def __init__(self, origins, local=False):
        self.origins = set(origins)
        self.local = local
        self.sessions = {}
        self.busy = False
        self.page = (PUBLIC / 'index.html').read_text()
        # The exact file allowlist is frozen at startup. No user output is in this tree.
        self.assets = {p.name: p for p in (PUBLIC/'assets').iterdir() if p.is_file() and not p.is_symlink()}
        self.tasks = set()
        self.output = None
        if local:
            self.output = Path(os.environ.get('RMO_RESULTS_DIR',str(ROOT/'results/local_runs'))) / uuid.uuid4().hex
            self.output.mkdir(parents=True,exist_ok=False)

    def origin(self, request, *, allow_navigation=False):
        hosts = request.headers.getall('Host', [])
        if len(hosts) != 1:
            raise web.HTTPForbidden(text='One valid Host header is required.')
        scheme = 'http' if self.local else 'https'
        origin = scheme + '://' + hosts[0]
        if origin not in self.origins:
            raise web.HTTPForbidden(text='Unrecognized application origin.')
        # Public links may open the landing page, while APIs and assets retain
        # the strict request policy. Only the index handler enables this case.
        navigation = (allow_navigation and request.path == '/'
                      and request.method in ('GET', 'HEAD')
                      and request.headers.get('Sec-Fetch-Site') in ('cross-site', 'same-site')
                      and request.headers.get('Sec-Fetch-Mode') == 'navigate'
                      and request.headers.get('Sec-Fetch-Dest') == 'document')
        if request.headers.get('Sec-Fetch-Site') not in (None, 'none', 'same-origin') and not navigation:
            raise web.HTTPForbidden(text='Cross-site requests are disabled.')
        return origin

    def session(self, request, *, create=False):
        now = time.monotonic()
        self.sessions = {k:s for k,s in self.sessions.items() if s.expires > now or s.active}
        ident = request.cookies.get(COOKIE)
        current = self.sessions.get(ident)
        if current and current.expires > now:
            return ident, current
        if not create:
            raise web.HTTPForbidden(text='Session expired. Reload the application.')
        if len(self.sessions) >= MAX_SESSIONS:
            raise web.HTTPServiceUnavailable(text='Application capacity reached. Try again later.')
        ident = secrets.token_urlsafe(32)
        current = Session()
        self.sessions[ident] = current
        return ident, current

    def api_session(self, request):
        origin = self.origin(request)
        _, session = self.session(request)
        tokens = request.headers.getall('X-RMO-Token', [])
        if len(tokens) != 1 or not secrets.compare_digest(tokens[0], session.token):
            raise web.HTTPForbidden(text='Session token does not match.')
        origins = request.headers.getall('Origin', [])
        if request.method == 'POST' and origins != [origin]:
            raise web.HTTPForbidden(text='An exact same-origin request is required.')
        if origins and origins != [origin]:
            raise web.HTTPForbidden(text='Origin does not match.')
        return session

STATE = web.AppKey('state', State)

@web.middleware
async def headers(request, handler):
    try:
        response = await handler(request)
    except web.HTTPException as exc:
        response = web.json_response({'error': exc.text}, status=exc.status)
    except (ValueError, UnicodeError, TypeError, KeyError, RecursionError):
        response = web.json_response({'error':'Invalid request.'}, status=400)
    except Exception:
        # Do not send local paths, stack traces, tokens or another request's content.
        response = web.json_response({'error':'The request could not be completed.'}, status=500)
    response.headers.update({'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY',
        'Referrer-Policy':'no-referrer','Cross-Origin-Opener-Policy':'same-origin',
        'Content-Security-Policy':CSP})
    # Only the reviewed, content-addressed asset handler opts into caching.
    response.headers.setdefault('Cache-Control', 'no-store')
    if not request.app[STATE].local:
        response.headers['Strict-Transport-Security']='max-age=31536000'
    return response

async def index(request):
    state=request.app[STATE];origin=state.origin(request,allow_navigation=True)
    ident, session=state.session(request,create=True)
    marker='<script id="local-config" type="application/json">{"enabled":false}</script>'
    if state.page.count(marker)!=1:
        raise RuntimeError('Application configuration marker mismatch')
    config=encode({'enabled':True,'origin':origin,'token':session.token,'version':VERSION,'storage':'browser_downloads'})
    page=state.page.replace(marker,'<script id="local-config" type="application/json">'+config+'</script>')
    response=web.Response(text=page,content_type='text/html')
    response.set_cookie(COOKIE,ident,max_age=SESSION_SECONDS,httponly=True,samesite='Strict',secure=not state.local,path='/')
    response.enable_compression()
    return response

async def asset(request):
    state=request.app[STATE];state.origin(request)
    name=request.match_info['name']
    if not re.fullmatch(r'[0-9a-f]{64}\.[a-z0-9]+',name) or name not in state.assets:
        raise web.HTTPNotFound(text='No such public resource.')
    return web.FileResponse(state.assets[name], headers={
        'Cache-Control': 'public, max-age=31536000, immutable'
    })

async def health(request):
    return web.json_response({'ready':True,'version':VERSION})

async def status(request):
    request.app[STATE].api_session(request)
    return web.json_response({'connection_version':VERSION,'ready':True,'scope':'Declared synthetic special cases and bounded local planar diagnosis','attempt_limit':MAX_ATTEMPTS})

async def body(request):
    if request.content_type!='application/json' or request.headers.get('Content-Encoding') or request.headers.get('Transfer-Encoding'):
        raise web.HTTPUnsupportedMediaType(text='Uncompressed application/json with Content-Length is required.')
    if request.content_length is None or not 0 < request.content_length <= OUTER_LIMIT:
        raise web.HTTPRequestEntityTooLarge(max_size=OUTER_LIMIT,actual_size=request.content_length or 0)
    try:
        return await asyncio.wait_for(request.text(),timeout=5)
    except asyncio.TimeoutError:
        raise web.HTTPRequestTimeout(text='Request body timed out.')

def safe_result(value):
    """Remove execution-machine details; retain request identity and scientific output."""
    if isinstance(value,dict):
        return {k:safe_result(v) for k,v in value.items() if k not in {'worker_command','stderr'}}
    if isinstance(value,list):return [safe_result(v) for v in value]
    return value

async def calculate(request):
    state=request.app[STATE];session=state.api_session(request)
    text=await body(request)
    diagnosis=request.path=='/api/diagnose'
    envelope=validate(text) if diagnosis else unpack(text)[0]
    ident=envelope['execution_id']
    if ident in session.seen:
        raise web.HTTPConflict(text='Execution ID already used. Submit a new attempt.')
    if len(session.seen)>=MAX_ATTEMPTS:
        raise web.HTTPTooManyRequests(text='Session calculation limit reached. Save your results and try later.')
    if state.busy:
        return web.json_response({
            'code': 'CALCULATION_BUSY',
            'error': 'The calculation service is busy with another request. Please wait a moment, then click Calculate again. Your input values are unchanged.',
        }, status=409)
    # No await between the capacity check and reservation.
    state.busy=True;session.seen.add(ident)
    cancel=threading.Event();session.active=(envelope,cancel)
    early=session.early_cancel.pop(ident,None)
    if early is not None and all(envelope.get(k)==v for k,v in early.items()):cancel.set()
    job=asyncio.create_task(asyncio.to_thread(run_diagnosis,envelope) if diagnosis else asyncio.to_thread(run,text,cancel=cancel))
    state.tasks.add(job)
    try:
        result=await asyncio.shield(job)
        if diagnosis:
            if result.get('identity')!=envelope:raise RuntimeError('Identity mismatch')
            reply=safe_result(result)
        else:
            if not matches_input(result,ident,envelope['request_body_sha256'],envelope['input_revision']):raise RuntimeError('Identity mismatch')
            reply={'result':safe_result(result),'connection_version':VERSION,'storage':'browser_downloads'}
        if state.output is not None:
            directory=state.output/uuid.uuid4().hex
            directory.mkdir(exist_ok=False)
            (directory/'request.json').write_text(text)
            (directory/'result.json').write_text(encode(reply))
            reply['saved_directory']=str(directory)
        return web.Response(text=encode(reply),content_type='application/json')
    finally:
        # A disconnected/shutting-down handler must not release its slot while its worker still runs.
        cancel.set()
        try:
            await asyncio.shield(job)
        finally:
            state.tasks.discard(job);session.active=None;state.busy=False

async def cancel(request):
    session=request.app[STATE].api_session(request)
    identity=strict_load(await body(request),2048)
    if not isinstance(identity,dict) or set(identity)!={'execution_id','request_body_sha256','input_revision'}:
        raise ValueError('Cancellation identity required')
    if not isinstance(identity['execution_id'],str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',identity['execution_id']):raise ValueError('Invalid identity')
    if not isinstance(identity['request_body_sha256'],str) or not re.fullmatch(r'[0-9a-f]{64}',identity['request_body_sha256']):raise ValueError('Invalid checksum')
    if type(identity['input_revision']) is not int:raise ValueError('Invalid revision')
    if session.active:
        envelope,event=session.active
        if any(envelope.get(k)!=v for k,v in identity.items()):raise web.HTTPConflict(text='Cancellation does not match this session attempt.')
        event.set();result='CANCELLATION_REQUESTED'
    elif identity['execution_id'] in session.seen:result='ATTEMPT_ALREADY_FINISHED'
    else:
        if len(session.early_cancel)>=MAX_ATTEMPTS:raise web.HTTPTooManyRequests(text='Cancellation limit reached.')
        session.early_cancel[identity['execution_id']]=identity;result='EARLY_CANCELLATION_RECORDED'
    return web.json_response({'status':result})

async def cleanup(app):
    state=app[STATE]
    for session in state.sessions.values():
        if session.active:session.active[1].set()
    if state.tasks:await asyncio.gather(*state.tasks,return_exceptions=True)

def create_app(origins, *, local=False):
    if not origins:raise ValueError('Set RENDER_EXTERNAL_URL or RMO_PUBLIC_ORIGINS before public launch.')
    for origin in origins:
        u=urlsplit(origin)
        if u.scheme!=('http' if local else 'https') or not u.netloc or u.path or u.query or u.fragment or u.username:
            raise ValueError('Use explicit application origins without paths or credentials.')
    app=web.Application(middlewares=[headers],client_max_size=OUTER_LIMIT)
    app[STATE]=State(origins,local)
    app.router.add_get('/',index)
    app.router.add_get('/healthz',health)
    app.router.add_get('/assets/{name}',asset)
    app.router.add_get('/api/status',status)
    app.router.add_post('/api/run',calculate)
    app.router.add_post('/api/diagnose',calculate)
    app.router.add_post('/api/cancel',cancel)
    app.on_cleanup.append(cleanup)
    return app

def main():
    parser=argparse.ArgumentParser(description='RMO public or local application')
    parser.add_argument('--local',action='store_true',help='Bind to loopback for local use')
    parser.add_argument('--port',type=int,default=int(os.environ.get('PORT','8765')))
    args=parser.parse_args()
    if not 1<=args.port<=65535:parser.error('Invalid port')
    origins=([f'http://127.0.0.1:{args.port}'] if args.local else
             [s for s in [os.environ.get('RENDER_EXTERNAL_URL','').rstrip('/'),*os.environ.get('RMO_PUBLIC_ORIGINS','').split(',')] if s])
    app=create_app(origins,local=args.local)
    web.run_app(app,host='127.0.0.1' if args.local else '0.0.0.0',port=args.port,
                access_log=None,shutdown_timeout=35,handler_cancellation=False)

if __name__=='__main__':main()
