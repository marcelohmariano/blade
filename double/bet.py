from double import blazeapi
from double import event
from double import stats
from double import wallet

WHITE = 0
RED = 1
BLACK = 2


class Placer(blazeapi.Client):
    async def place_bet(self, color: int, amount: float,
                        wallet_id: int) -> None:
        data = {
            'amount': str(amount),
            'currency_type': 'BRL',
            'color': color,
            'free_bet': False,
            'wallet_id': wallet_id
        }
        await self._post('/roulette_bets', data=data)


class Strategy:
    def __init__(self,
                 event_reactor: event.Reactor,
                 wallet_syncer: wallet.Syncer,
                 bet_placer: Placer,
                 bet_amount: float,
                 bet_max_tries: int):
        self._event_reactor = event_reactor
        self._wallet_syncer = wallet_syncer
        self._bet_placer = bet_placer

        self._initial_bet_amount = bet_amount

        self._last_event = None
        self._strategy_colors = []
        self._bet_colors = []

        self._bet_tries = 0
        self._bet_max_bets = bet_max_tries

        self._stats = stats.Stats()
        self._stats.balance = wallet_syncer.balance
        self._stats.update_bet_amounts(self._initial_bet_amount)

    async def on_double_event(self, evt: event.DoubleEvent) -> None:
        if self._last_event and self._last_event == evt:
            return
        self._last_event = evt

        if self._wallet_syncer.balance < self._stats.total_bet_amount():
            await self._finish()
            return

        match evt.status:
            case 'waiting':
                await self._place_bets()
            case 'rolling':
                await self._check_results(evt)

    async def _place_bets(self) -> None:
        color = self._next_color()
        await self._bet_placer.place_bet(color,
                                         self._stats.color_bet_amount,
                                         self._wallet_syncer.id)
        self._bet_colors.append(color)

        await self._bet_placer.place_bet(WHITE,
                                         self._stats.white_bet_amount,
                                         self._wallet_syncer.id)
        self._bet_colors.append(WHITE)

        self._stats.inc_bets()
        self._stats.show()

    async def _check_results(self, evt: event.DoubleEvent) -> None:
        if len(self._bet_colors) == 0:
            return

        if evt.color not in self._bet_colors:
            self._bet_tries += 1
            self._stats.update_loss_amount()

            if self._bet_tries >= self._bet_max_bets:
                self._stats.increase_bet_after_loss()
                self._bet_tries = 0
        else:
            self._stats.update_win_amount(evt.color)
            self._stats.update_bet_amounts(self._initial_bet_amount)
            self._bet_tries = 0

        self._bet_colors.clear()
        self._stats.balance = await self._wallet_syncer.sync()

        self._stats.show()

    def _next_color(self) -> int:
        if len(self._strategy_colors) == 0:
            self._strategy_colors.extend([RED, RED, BLACK, BLACK])
        return self._strategy_colors.pop(0)

    async def _finish(self) -> None:
        await self._event_reactor.stop()
        print()
