import enum

import blade


class Color(enum.IntEnum):
    WHITE = 0
    RED = 1
    BLACK = 2


def bet(amount: float, color: Color) -> blade.Bet:
    return blade.Bet(amount=amount, color=color.value)
