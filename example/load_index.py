import asyncio
import json

from nowem import PCRClient


async def main():
    ppf = 'tw.sonet.princessconnect.v2.playerprefs'
    c = PCRClient('3.7.0', playerprefs=f'../data/{ppf}.xml')
    await c.call.check.check_agreement()
    await c.call.check.game_start()
    json.dump(await c.call.load.index(no_headers=False), open('../data/index.json', 'w', encoding='utf-8'),
              ensure_ascii=False)
    d = await c.call.clan_battle.top(clan_id=122233, is_first=1, current_clan_battle_coin=12233)
    print(d)


asyncio.get_event_loop().run_until_complete(main())
