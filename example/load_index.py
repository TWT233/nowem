import asyncio
import json

from nowem import PCRClient


async def main():
    c = PCRClient(playerprefs='../data/t1-reader.xml', proxy={"http": "localhost:7892", "https": "localhost:7892"},
                  version='2.8.1')
    await c.call.check.check_agreement().exec()
    await c.call.check.game_start().exec()
    json.dump(await c.call.load.index().exec(no_headers=False), open('../data/index.json', 'w', encoding='utf-8'),
              ensure_ascii=False)


asyncio.get_event_loop().run_until_complete(main())
