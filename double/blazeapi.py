from typing import Any

import aiohttp


class Client:
    def __init__(self,
                 session: aiohttp.ClientSession,
                 headers: dict = None,
                 base_url: str = 'https://blaze.com/api'):
        headers = headers.copy() or {}

        headers['Origin'] = 'https://blaze.com/'
        headers['Referer'] = 'https://blaze.com/en/games/double'

        session.headers.update(headers)
        self._session = session

        if base_url.endswith('/'):
            base_url = base_url[:len(base_url) - 1]

        self._base_url = base_url

    async def _get(self, endpoint: str) -> aiohttp.ClientResponse:
        url = self._build_url(endpoint)
        r = await self._session.get(url)
        r.raise_for_status()
        return r

    async def _post(self, endpoint: str, data: Any) -> aiohttp.ClientResponse:
        url = self._build_url(endpoint)
        r = await self._session.post(url, json=data)
        r.raise_for_status()
        return r

    def _build_url(self, endpoint):
        endpoint = endpoint[1:] if endpoint.startswith('/') else endpoint
        return f'{self._base_url}/{endpoint}'
