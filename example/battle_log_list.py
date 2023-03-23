import asyncio
import json
import logging

from nowem import PCRClient, playerprefs

logging.basicConfig(level='DEBUG')


async def main():
    c = PCRClient('3.7.0', pp_xml=playerprefs.dec_plist_xml('../data/tw.sonet.princessconnect.plist'))
    await c.call.check.check_agreement()
    await c.call.check.game_start()
    index = await c.call.load.index(no_headers=False)
    json.dump(index, open('../data/index.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    await c.call.clan.info()
    await c.call.clan_battle.top(35506, 1, 11705)

    await c.call.clan_battle.battle_log_list(1055, 0, [5], [1, 2, 3, 4], 0, [], 1, 1)


asyncio.run(main())
