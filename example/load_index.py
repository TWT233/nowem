import asyncio
import json

from nowem import PCRClient


async def main():
    ppf = 'tw.sonet.princessconnect.v2.playerprefs'
    c = PCRClient(playerprefs=f'../data/{ppf}.xml', version='2.8.1')
    await c.call.check.check_agreement()
    await c.call.check.game_start()
    json.dump(await c.call.load.index(no_headers=False), open('../data/index.json', 'w', encoding='utf-8'),
              ensure_ascii=False)


asyncio.get_event_loop().run_until_complete(main())
