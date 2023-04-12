#!/usr/bin/env python3
import asyncio
import os

import dotenv

import blade
from blade import double, blaze
from blade import simulation

allowed_minutes = {6, 9, 11, 13, 16, 23, 24}


class Strategy(blade.PlaceBetsStrategy, blade.CheckResultStrategy):
    def __init__(self, wallet: blade.Wallet, initial_bet_amount: float):
        self._wallet = wallet

        self._initial_balance = self._wallet.balance
        self._initial_bet_amount = initial_bet_amount
        self._current_bet_amount = self._initial_bet_amount

        self._win_count = 0
        self._loss_count = 0
        self._white_count = 0

        self._win_amount = 0.0
        self._loss_amount = 0.0

        self._update_screen()

    def __str__(self) -> str:
        return ' | '.join([
            f'Balance: {self._wallet.balance:.2f}',
            f'Bet: {self._current_bet_amount:.2f}',
            f'Won: {self._win_amount:.2f}',
            f'Lost: {self._loss_amount:.2f}',
            f'Wins: {self._win_count}',
            f'Losses: {self._loss_count}',
            f'Whites: {self._white_count}'
        ])

    def _update_screen(self) -> None:
        print(self)

    def _update_earnings(self) -> None:
        win_amount = self._wallet.balance - self._initial_balance
        self._win_amount = max(win_amount, 0.0)

        loss_amount = self._initial_balance - self._wallet.balance
        self._loss_amount = max(loss_amount, 0.0)

    def _count_win(self, amount: float, color: double.Color) -> None:
        if color == double.Color.WHITE:
            self._white_count += 1
            win_amount = amount * 14
        else:
            win_amount = amount * 2

        self._wallet.add(win_amount)
        self._win_count += 1
        self._loss_count = 0
        self._current_bet_amount = self._initial_bet_amount

    def _count_loss(self):
        self._loss_count += 1
        if self._loss_count % 14 == 0:
            self._current_bet_amount = self._loss_amount

    def on_place_bets(self, message: blade.Message, bets: blade.Bets) -> None:
        if message.time.minute not in allowed_minutes:
            return
        bets.add(double.bet(self._current_bet_amount, double.Color.WHITE))

    def on_check_win(self, message: blade.Message, bet: blade.Bet) -> bool:
        return message.data.color == bet.color

    def on_win(self, bet: blade.Bet, amount: float, **kwargs) -> None:
        self._count_win(amount, bet.color)

    def on_loss(self, **kwargs) -> None:
        self._count_loss()

    def on_complete(self) -> None:
        self._update_earnings()
        self._update_screen()


def load_config() -> tuple[str, dict[str, str]]:
    dotenv.load_dotenv()
    token = os.getenv('BLAZE_TOKEN')
    headers = {
        'user-agent': os.getenv('USER_AGENT'),
        'referer': 'https://blaze.com/en/games/double'
    }
    return token, headers


def create_play(
    wallet: blade.Wallet, bettor: blade.Bettor, strategy: Strategy
) -> blade.Play:
    bets = blade.Bets()

    play = blade.Play()
    play.when(status='waiting',
              action=blade.PlaceBetsAction(wallet=wallet,
                                           bettor=bettor,
                                           strategy=strategy,
                                           bets=bets))
    play.when(status='rolling',
              action=blade.CheckResultAction(strategy=strategy, bets=bets))

    return play


async def main() -> None:
    token, headers = load_config()

    channel = blaze.Channel('double_v2', token, headers)
    await channel.connect()
    # channel = simulation.Channel(filenames=['24.xlsx'])
    # channel.start_producing_messages()

    wallet = blade.Wallet(2000.0)
    bettor = simulation.Bettor(wallet)
    strategy = Strategy(wallet=wallet, initial_bet_amount=5)

    play = create_play(wallet, bettor, strategy)

    bot = blade.Bot(channel)
    bot.on('double.tick', play)
    await bot.run()


if __name__ == '__main__':
    asyncio.run(main())
