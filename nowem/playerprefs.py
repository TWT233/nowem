import plistlib

from urllib.parse import unquote
from re import finditer
from base64 import b64decode
from struct import unpack

_KEY_PLAYERPREFS = b'e806f6'


def _xor_endec(b: bytes, key: bytes) -> bytes:
    return bytes([key[i % len(key)] ^ b[i] for i in range(len(b))])


def _dec_key(s: str) -> bytes:
    return _xor_endec(b64decode(unquote(s)), _KEY_PLAYERPREFS)


def _dec_val(key: str, s: str) -> bytes:
    b = b64decode(unquote(s))
    b = b[0:len(b) - (11 if b[-5] != 0 else 7)]
    return _xor_endec(b, key.encode() + _KEY_PLAYERPREFS)


def dec_xml(file: str) -> dict:
    res = {}

    with open(file, 'r') as f:
        content = f.read()

    for m in finditer(r'<string name="(.*)">(.*)</string>', content):
        try:
            key = _dec_key(m.group(1)).decode()
        except:
            continue

        val = _dec_val(key, m.group(2))

        if key == 'UDID':
            val = ''.join([chr(val[4 * i + 6] - 10) for i in range(36)])
        elif len(val) == 4:
            val = str(unpack('i', val)[0])

        res[key] = val

    return res


def dec_plist_xml(file: str) -> dict:
    """in Apple devices, playerprefs is stored as plist
    for PlayCover over Mac, it is located at
    ~/Library/Containers/tw.sonet.princessconnect/Data/Library/Preferences/tw.sonet.princessconnect.plist"""
    res = {}

    with open(file, 'rb') as f:
        pl: dict = plistlib.load(f)
        for k, v in pl.items():
            try:
                key = _dec_key(k).decode()
                val = _dec_val(key, v)
            except Exception:
                ...

            if key == 'UDID':
                val = ''.join([chr(val[4 * i + 6] - 10) for i in range(36)])
            elif len(val) == 4:
                val = str(unpack('i', val)[0])
            res[key] = val

    return res
