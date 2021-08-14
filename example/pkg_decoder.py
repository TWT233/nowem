import asyncio
import json

from nowem import PCRClient


async def main():
    c = PCRClient(playerprefs='../data/t1-reader.xml', proxy={}, version='2.8.1')
    print(f'udid_iv: {c.sec._udid_iv}')

    while True:
        raw = input('base64>>>')
        dec, key = c.sec.unpack(raw.encode())
        print(dec)
        print(json.dumps(dec))
        print(f'key: {key}')
        if 'viewer_id' in dec:
            print(f'viewer_id: {c.sec.decrypt(dec["viewer_id"].encode())}')


asyncio.get_event_loop().run_until_complete(main())
