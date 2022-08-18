import asyncio
from utils.rankings import *


async def main():
    print('Hello ...')
    await add_global_ranking_records({728495196303523900: 6.53})
    print('... World!')


asyncio.run(main())
