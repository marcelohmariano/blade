import asyncio
from typing import Any, Callable, Awaitable

import aiohttp
import socketio

from blade import blade


def _build_url(endpoint):
    endpoint = endpoint[1:] if endpoint.startswith('/') else endpoint
    return f'https://blaze.com/api/{endpoint}'


class HTTPClient:
    def __init__(self, headers: dict[str, str]):
        self._session = aiohttp.ClientSession(headers=headers)
        self._session.headers['origin'] = 'https://blaze.com/'

    async def __aenter__(self) -> 'HTTPClient':
        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await self._session.close()

    async def _request(self,
                       method: str,
                       endpoint: str, **kwargs) -> aiohttp.ClientResponse:
        url = _build_url(endpoint)
        response = await self._session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    async def _get(self, endpoint: str) -> aiohttp.ClientResponse:
        return await self._request('GET', endpoint)

    async def _post(self, endpoint: str, data: Any) -> aiohttp.ClientResponse:
        return await self._request('POST', endpoint, json=data)

    async def roulette_bet(
        self,
        amount: float,
        wallet_id: int,
        free_bet: bool = False,
        **kwargs,
    ) -> None:
        payload = {'amount': str(amount),
                   'currency_type': 'BRL',
                   'free_bet': free_bet,
                   'wallet_id': wallet_id}
        payload.update(**kwargs)
        await self._post('/roulette_bets', data=payload)


class SocketIOClient:
    def __init__(self, token: str, headers: dict[str, Any]):
        self._token = token
        self._headers = headers
        self._sio = socketio.AsyncClient(reconnection=True)

    def on_data(
        self,
        handler: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        self._sio.on('data', handler)

    async def connect(self) -> None:
        await self._sio.connect(url='wss://api-v2.blaze.com',
                                headers=self._headers,
                                transports='websocket',
                                socketio_path='replication')

    async def wait(self) -> None:
        await self._sio.wait()

    async def close(self) -> None:
        await self._sio.disconnect()

    async def send_cmd(self, cmd_id: str, **kwargs) -> None:
        payload = {'id': cmd_id, 'payload': kwargs}
        await self._sio.emit(event='cmd', data=payload)

    async def authenticate(self) -> None:
        await self.send_cmd('authenticate', token=self._token)

    async def subscribe(self, game_room: str) -> None:
        await self.send_cmd('subscribe', room=game_room)


class Channel(blade.Channel):
    def __init__(self, name: str, token: str, headers: dict[str, str] = None):
        super().__init__()
        self._name = name
        self._token = token
        self._client = SocketIOClient(token, headers)

    async def _handle_data_event(self, data: dict[str, Any]) -> None:
        message = blade.Message(id_=data.get('id'), data=data.get('payload'))
        await self.add(message)

    async def close(self) -> None:
        await super().close()
        await self._client.close()

    async def connect(self) -> None:
        self._client.on_data(self._handle_data_event)

        await self._client.connect()
        await self._client.authenticate()
        await self._client.subscribe(self._name)

        asyncio.create_task(self._client.wait())


class Bettor:
    def __init__(self, wallet_id: int, headers: dict[str, str]):
        self._wallet_id = wallet_id
        self._client = HTTPClient(headers)

    async def bet(self, amount: float, **kwargs):
        await self._client.roulette_bet(amount=amount,
                                        wallet_id=self._wallet_id,
                                        **kwargs)
