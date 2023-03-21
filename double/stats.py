class Stats:
    def __init__(self):
        self.balance = 0.0
        self.won = 0.0
        self.lost = 0.0
        self.last_loss = 0.0
        self.color_bet_amount = 0.0
        self.white_bet_amount = 0.0
        self.bets = 0
        self.wins = 0
        self.losses = 0

    def __str__(self):
        return ' '.join([
            f'Balance: {self.balance:.2f}',
            f'Won: {self.won:.2f}',
            f'Lost: {self.lost:.2f}',
            f'Bet: {self.total_bet_amount():.2f}',
            f'Bets: {self.bets}',
            f'Wins: {self.wins}',
            f'Loss: {self.losses}'
        ])

    def show(self) -> None:
        print(str(self) + '   ', end='\r', flush=True)

    def inc_bets(self) -> None:
        self.bets += 1

    def update_loss_amount(self):
        amount = self.total_bet_amount()
        self.lost += amount
        self.last_loss += amount

    def increase_bet_after_loss(self) -> None:
        self.update_bet_amounts(self.last_loss)
        self.losses += 1

    def update_bet_amounts(self, amount: float) -> None:
        self.color_bet_amount = amount
        self.white_bet_amount = max(amount / 4, 0.1)

    def total_bet_amount(self) -> float:
        return self.color_bet_amount + self.white_bet_amount

    def color_win_amount(self) -> float:
        return self.color_bet_amount * 2

    def white_win_amount(self) -> float:
        return self.white_bet_amount * 14

    def update_win_amount(self, color: int) -> None:
        amount = self.white_win_amount() if color == 0 else self.color_win_amount()
        self.won += amount
        self.last_loss = 0.0
        self.wins += 1
