import asyncio
import base64
import json

from nowem import PCRClient, playerprefs


def read_raw(raw: str):
    """
    for requests, the raw is plain binary, so cannot be b64decoded and should be b64encoded
    for responses, the raw is b64encoded already, thus just need to be encoded
    """
    try:
        base64.b64decode(raw, validate=True)
    except Exception:
        return base64.b64encode(bytes.fromhex(''.join(raw.split(' '))))
    return raw.encode()


async def main():
    c = PCRClient('3.7.0', pp_xml=playerprefs.dec_plist_xml('../data/tw.sonet.princessconnect.plist'))

    while True:
        raw = input('input(hex/b64)>>>')
        dec, key = c.sec.unpack(read_raw(raw))
        print(f'data: {json.dumps(dec)}')
        print(f'key: {key}')
        if 'viewer_id' in dec:
            print(f'viewer_id: {c.sec.decrypt(dec["viewer_id"].encode())}')


asyncio.run(main())
