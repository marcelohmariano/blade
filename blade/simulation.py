import asyncio
from typing import Any

import pandas as pd

from blade import blade
from blade import play


def _open(filename: str) -> pd.DataFrame:
    df = pd.read_excel(filename)

    df = df.loc[(df.Cor != 'tipminer.com')]
    df.reset_index(drop=True, inplace=True)

    df.Horario = pd.to_datetime(df.Horario, format='%d/%m/%Y %H:%M')
    df.sort_values(by='Horario', inplace=True)

    return df


class Bettor(play.Bettor):
    def __init__(self, wallet: play.Wallet):
        self._wallet = wallet

    async def bet(self, amount: float, **kwargs):
        self._wallet.sub(amount)


class Channel(blade.Channel):
    colors = {'branco': 0, 'vermelho': 1, 'preto': 2}

    def __init__(self, filenames: list[str]):
        super().__init__()
        self._filenames = filenames

    async def _produce_message(self, row: Any):
        data = {
            'color': self.colors[row.Cor],
            'created_at': row.Horario,
            'status': 'waiting'
        }

        await self.add(blade.Message('double.tick', data))
        data['status'] = 'rolling'
        await self.add(blade.Message('double.tick', data))

    async def _produce_messages(self) -> None:
        for filename in self._filenames:
            for _, row in _open(filename).iterrows():
                await self._produce_message(row)

    def start_producing_messages(self) -> None:
        asyncio.create_task(self._produce_messages())
