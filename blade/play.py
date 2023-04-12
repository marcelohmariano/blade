import abc
from typing import Any

from blade import blade


class Wallet:
    def __init__(self, balance: float):
        self._balance = balance

    def add(self, amount: float) -> None:
        self._balance += amount

    def sub(self, amount: float) -> None:
        self._balance -= amount

    @property
    def balance(self) -> float:
        return self._balance


class Bettor(abc.ABC):
    @abc.abstractmethod
    async def bet(self, amount: float, **kwargs) -> None:
        pass


class Bet(dict):
    def __getattr__(self, name: str) -> Any:
        if name in self:
            return self.get(name)
        raise AttributeError(f'{name} not found in {self.__class__.__name__}')

    @property
    def amount(self) -> float:
        return self.get('amount', 0)


class Bets:
    def __init__(self):
        self._bets = []
        self._amount = 0.0

    def __len__(self) -> int:
        return len(self._bets)

    def add(self, bet: Bet):
        if bet not in self._bets:
            self._bets.append(bet)
            self._amount += bet.amount

    def clear(self) -> None:
        self._bets.clear()
        self._amount = 0.0

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def inputs(self) -> list[Bet]:
        return self._bets


class Action:
    @abc.abstractmethod
    async def __call__(self, runner: blade.Bot,
                       message: blade.Message) -> None:
        pass


class PlaceBetsStrategy(abc.ABC):
    @abc.abstractmethod
    def on_place_bets(self, message: blade.Message, bets: Bets) -> None:
        pass


class PlaceBetsAction(Action):
    def __init__(
        self,
        wallet: Wallet,
        bettor: Bettor,
        strategy: PlaceBetsStrategy,
        bets: Bets,
    ):
        self._wallet = wallet
        self._bettor = bettor
        self._strategy = strategy
        self._bets = bets

    async def __call__(self, runner: blade.Bot,
                       message: blade.Message) -> None:
        self._bets.clear()
        self._strategy.on_place_bets(message, self._bets)

        if self._bets.amount <= 0:
            return

        if self._wallet.balance < self._bets.amount:
            await runner.stop()
            return

        for bet_input in self._bets.inputs:
            await self._bettor.bet(**bet_input)


class CheckResultStrategy(abc.ABC):
    @abc.abstractmethod
    def on_check_win(self, message: blade.Message, bet: Bet) -> bool:
        pass

    @abc.abstractmethod
    def on_win(self, message: blade.Message, bet: Bet, amount: float) -> None:
        pass

    @abc.abstractmethod
    def on_loss(self, message: blade.Message, amount: float) -> None:
        pass

    @abc.abstractmethod
    def on_complete(self) -> None:
        pass


class CheckResultAction(Action):
    def __init__(self, strategy: CheckResultStrategy, bets: Bets):
        self._strategy = strategy
        self._bets = bets

    async def __call__(self, runner: blade.Bot,
                       message: blade.Message) -> None:
        if self._bets.amount <= 0:
            return

        self._check_win(message)
        self._strategy.on_complete()

    def _check_win(self, message: blade.Message) -> None:
        for bet in self._bets.inputs:
            if not self._strategy.on_check_win(message=message, bet=bet):
                continue

            self._strategy.on_win(message=message, amount=bet.amount, bet=bet)
            return

        self._strategy.on_loss(message=message, amount=self._bets.amount)


class Play:
    def __init__(self):
        self._actions = {}
        self._last_message_status = None

    async def __call__(self, runner: blade.Bot,
                       message: blade.Message) -> None:
        if self._skip(message):
            return

        action = self._actions.get(message.data.status)
        if action:
            await action(runner, message)

    def _skip(self, message: blade.Message) -> bool:
        if self._last_message_status == message.data.status:
            return True
        self._last_message_status = message.data.status
        return False

    def when(self, status: str, action: Action) -> None:
        self._actions[status] = action
