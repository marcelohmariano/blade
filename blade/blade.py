import asyncio
import collections.abc
import datetime
import functools
from typing import Any
from typing import Awaitable
from typing import Callable

_build_message_data = functools.partial(collections.namedtuple, 'MessageData')

MessageHandler = Callable[['Bot', 'Message'], Awaitable[None]]


class Message:
    def __init__(self, id_: str, data: dict[str, Any]):
        self._id = id_
        self._data = _build_message_data(data.keys())(*data.values())

        try:
            created_at = self._data.created_at
            if isinstance(created_at, datetime.datetime):
                self._time = created_at
            else:
                self._time = datetime.datetime.fromisoformat(created_at)
        except AttributeError:
            self._time = datetime.datetime.now()

    def __str__(self):
        return str({
            'id': self._id,
            'time': self._time.isoformat(),
            'data': getattr(self._data, '_asdict')()
        })

    @property
    def id(self) -> str:
        return self._id

    @property
    def time(self) -> datetime.datetime:
        return self._time

    @property
    def data(self) -> Any:
        return self._data


class Channel(collections.abc.AsyncIterator[Message]):
    def __init__(self):
        self._messages = asyncio.Queue()

    def __aiter__(self) -> collections.abc.AsyncIterator[Message]:
        return self

    async def __anext__(self) -> Message:
        message = await self._messages.get()
        self._messages.task_done()

        if message is None:
            raise StopAsyncIteration

        return message

    async def add(self, message: Message) -> None:
        await self._messages.put(message)

    async def close(self) -> None:
        await self._messages.put(None)


class Bot:
    def __init__(self, channel: Channel):
        self._channel = channel
        self._handlers = {}

    async def _handle(self, message: Message) -> None:
        handler = self._handlers.get(message.id)
        if handler is None:
            return
        await handler(self, message)

    def on(self, message: str, handler: MessageHandler) -> None:
        if not message:
            raise ValueError('message is required')
        self._handlers[message] = handler

    async def run(self) -> None:
        async for message in self._channel:
            await self._handle(message)

    async def stop(self) -> None:
        await self._channel.close()
