import os

import aiohttp
import dotenv

from double import bet
from double import event
from double import wallet


async def run() -> None:
    dotenv.load_dotenv()

    auth_token = os.getenv('BLAZE_API_TOKEN')

    headers = {
        'User-agent': os.getenv('DEVICE_USER_AGENT'),
        'Authorization': f'Bearer {auth_token}',
    }

    async with aiohttp.ClientSession() as session:
        wallet_syncer = wallet.Syncer(session=session, headers=headers)
        await wallet_syncer.sync()

        event_reactor = event.Reactor(token=auth_token, headers=headers)

        bet_placer = bet.Placer(session=session, headers=headers)
        strategy = bet.Strategy(event_reactor=event_reactor,
                                wallet_syncer=wallet_syncer,
                                bet_placer=bet_placer,
                                bet_amount=0.4,
                                bet_max_tries=2)

        event_reactor.on_double_event(strategy.on_double_event)
        await event_reactor.process_events()
