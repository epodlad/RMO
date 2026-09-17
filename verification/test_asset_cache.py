"""HTTP regression checks for public asset caching and private response isolation."""
import unittest

from aiohttp.test_utils import TestClient, TestServer
from web_app.server import PUBLIC, STATE, create_app


class AssetCacheTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = create_app(['http://127.0.0.1:8765'], local=True)
        self.client = TestClient(TestServer(self.app))
        await self.client.start_server()
        self.app[STATE].origins = {str(self.client.make_url('/')).rstrip('/')}
        self.asset = '/assets/' + min(
            (p for p in (PUBLIC / 'assets').iterdir() if p.is_file()),
            key=lambda p: p.stat().st_size,
        ).name

    async def asyncTearDown(self):
        await self.client.close()

    async def test_assets_support_cache_and_revalidation(self):
        response = await self.client.get(self.asset)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers['Cache-Control'],
                         'public, max-age=31536000, immutable')
        self.assertNotIn('Set-Cookie', response.headers)
        etag = response.headers['ETag']
        await response.read()
        response = await self.client.get(self.asset, headers={'If-None-Match': etag})
        self.assertEqual(response.status, 304)
        self.assertEqual(await response.read(), b'')
        self.assertIn('immutable', response.headers['Cache-Control'])

    async def test_private_and_error_responses_remain_uncacheable(self):
        for path in ['/', '/healthz', '/api/status', '/assets/missing.png']:
            response = await self.client.get(path)
            self.assertEqual(response.headers['Cache-Control'], 'no-store', path)
            await response.read()
        response = await self.client.get(self.asset, headers={'Sec-Fetch-Site': 'cross-site'})
        self.assertEqual(response.status, 403)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')


if __name__ == '__main__':
    unittest.main()
