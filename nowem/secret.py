import base64
import hashlib
import logging
import random
import string
from typing import Tuple

import msgpack
from Cryptodome.Cipher import AES
from Cryptodome.Util import Padding

from .exception import PCRAPIException

_SALT_MD5 = 'r!I@nt8e5i='

_DEFAULT_HEADERS = {
    # client
    'Accept-Encoding': 'gzip',
    'User-Agent': 'Dalvik/2.1.0 (Linux, U, Android 5.1.1, PCRT00 Build/LMY48Z)',
    # entity
    'Content-Type': 'application/octet-stream',
    # transport
    'Expect': '100-continue',
    # game related headers
    'APP-VER': '2.6.0',
    'BATTLE-LOGIC-VERSION': '4',
    'BUNDLE-VER': '',
    # device related headers
    'DEVICE': '2',
    'DEVICE-ID': '',
    'DEVICE-NAME': 'blackshark DLT-A0',
    'GRAPHICS-DEVICE-NAME': 'Adreno (TM) 640',
    # miscs
    'IP-ADDRESS': '172.16.1.27',
    'KEYCHAIN': '',
    'LOCALE': 'Jpn',
    'PLATFORM': '2',
    'PLATFORM-OS-VERSION': 'Android OS 7.1.2 / API-25 (N2G48C/N975FXXU1ASGO)',
    'REGION-CODE': '',
    'RES-VER': '00017004',
    'X-Unity-Version': '2018.4.21f1',
}


class PCRSecret:
    def __init__(self, udid: str, short_udid: str, viewer_id: str):
        self.udid = udid
        self.short_udid = short_udid
        self.viewer_id = viewer_id

        self.headers = _DEFAULT_HEADERS.copy()
        self.headers['SID'] = self.md5(self.viewer_id + self.udid)

    @staticmethod
    def md5(s: str) -> str:
        return hashlib.md5((s + _SALT_MD5).encode('utf8')).hexdigest()

    @staticmethod
    def _random_iv() -> str:
        return ''.join(random.choices(string.digits, k=32))

    @staticmethod
    def _random_key() -> bytes:
        return bytes(random.choices(b'0123456789abcdef', k=32))

    def _udid_iv(self) -> bytes:
        return self.udid.replace('-', '')[:16].encode('utf8')

    @staticmethod
    def enc_short_udid(su: str) -> str:
        # body = random.choices(string.digits, k=4 * len(su))
        # for i in range(len(su)):
        #     body[4 * i + 2] = chr(ord(su[i]) + 10)
        # return f'{len(su):0>4x}' + ''.join(body) + PCRSecret._random_iv()
        return f'{len(su):0>4x}' + ''.join([f'__{chr(ord(i) + 10)}_' for i in su]) + PCRSecret._random_iv()

    def encrypt(self, s: str, key: bytes) -> bytes:
        aes = AES.new(key, AES.MODE_CBC, self._udid_iv())
        return aes.encrypt(Padding.pad(s.encode('utf8'), 16)) + key

    def decrypt(self, data: bytes) -> Tuple[bytes, bytes]:
        data = base64.b64decode(data.decode('utf8'))
        aes = AES.new(data[-32:], AES.MODE_CBC, self._udid_iv())
        return aes.decrypt(data[:-32]), data[-32:]

    def pack(self, obj: dict, key: bytes) -> Tuple[bytes, bytes]:
        aes = AES.new(key, AES.MODE_CBC, self._udid_iv())
        packed = msgpack.packb(obj, use_bin_type=False)
        return packed, aes.encrypt(Padding.pad(packed, 16)) + key

    def unpack(self, data: bytes) -> Tuple[dict, bytes]:
        data = base64.b64decode(data.decode('utf8'))
        aes = AES.new(data[-32:], AES.MODE_CBC, self._udid_iv())
        dec = Padding.unpad(aes.decrypt(data[:-32]), 16)
        return msgpack.unpackb(dec, strict_map_key=False), data[-32:]

    def prepare_req(self, api: str, params: dict) -> Tuple[bytes, dict]:
        key = PCRSecret._random_key()
        logging.getLogger(__name__).debug(f'generated key={key}')

        if 'SHORT-UDID' not in self.headers:
            self.headers['SHORT-UDID'] = self.enc_short_udid(self.short_udid)
        if 'SID' not in self.headers:
            self.headers['SID'] = self.md5(self.viewer_id + self.udid)

        params['viewer_id'] = base64.b64encode(self.encrypt(self.viewer_id, key))

        packed, crypted = self.pack(params, key)

        param_sha1 = hashlib.sha1((self.udid + api).encode())
        param_sha1.update(base64.b64encode(packed))
        param_sha1.update(self.viewer_id.encode())
        self.headers['PARAM'] = param_sha1.hexdigest()

        return crypted, self.headers

    async def handle_resp(self, resp) -> dict:
        response, key = self.unpack(await resp.content)
        logging.getLogger(__name__).debug(f'raw_response = {response}')
        logging.getLogger(__name__).debug(f'key = {key}')

        data_headers = response['data_headers']
        data = response['data']

        if 'server_error' in data:
            data = data['server_error']
            raise PCRAPIException(data['message'], data['status'], data_headers['result_code'])

        if 'viewer_id' in data_headers:
            self.viewer_id = str(data_headers['viewer_id'])

        if 'required_res_ver' in data_headers:
            self.headers['RES-VER'] = data_headers['required_res_ver']

        return data
