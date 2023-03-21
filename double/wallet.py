import aiohttp

from double import blazeapi


class Syncer(blazeapi.Client):
    def __init__(self,
                 session: aiohttp.ClientSession,
                 headers: dict = None,
                 base_url: str = 'https://blaze.com/api'):
        super().__init__(session, headers, base_url)
        self.id = None
        self.balance = 0.00

    def _update(self, value: float) -> float:
        if isinstance(value, str):
            value = float(value)
        self.balance = value
        return self.balance

    async def sync(self) -> float:
        r = await self._get('/wallets')
        data = await r.json()
        data = data[0]

        self.id = data['id']
        return self._update(data['balance'])
