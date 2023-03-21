from typing import Callable, Awaitable

import socketio


class DoubleEvent:
    def __init__(self, **kwargs):
        self.status = kwargs.get('status')
        self.color = kwargs.get('color')

    def __eq__(self, other):
        return self.status == other.status

    def __str__(self):
        return str(vars(self))


class WalletEvent:
    def __init__(self, **kwargs):
        self.balance = kwargs.get('balance')


class Reactor:
    def __init__(self,
                 token: str,
                 ws_url: str = 'wss://api-v2.blaze.com',
                 headers: dict = None):
        self._token = token
        self._ws_url = ws_url
        self._headers = headers
        self._handlers = {}
        self._sio = socketio.AsyncClient(reconnection=True)

    async def _handle_connect_event(self) -> None:
        payload = {'id': 'subscribe', 'payload': {'room': 'double_v2'}}
        await self._sio.emit(event='cmd', data=payload)

        payload = {'id': 'authenticate', 'payload': {'token': self._token}}
        await self._sio.emit(event='cmd', data=payload)

    async def _handle_data_event(self, event: dict) -> None:
        ret = self._handlers.get(event.get('id'))
        if ret is None:
            return
        handler, event_cls = ret[0], ret[1]

        payload = event['payload']
        await handler(event_cls(**payload))

    def on_double_event(self,
                        handler: Callable[[DoubleEvent], Awaitable[None]]):
        self._handlers['double.tick'] = (handler, DoubleEvent)

    def on_wallet_event(self,
                        handler: Callable[[WalletEvent], Awaitable[None]]):
        self._handlers['wallet.balance-changed'] = (handler, WalletEvent)

    async def process_events(self) -> None:
        self._sio.on('connect', self._handle_connect_event)
        self._sio.on('data', self._handle_data_event)

        await self._sio.connect(url=self._ws_url,
                                headers=self._headers,
                                transports='websocket',
                                socketio_path='replication')

        await self._sio.wait()

    async def stop(self) -> None:
        await self._sio.disconnect()
