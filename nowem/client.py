import functools
import logging
import random
import string
import time
import uuid

from .aiorequests import post, get
from .playerprefs import dec_xml
from .req import ReqDispatcher
from .secret import PCRSecret

_API_ROOT = ['https://api-pc.so-net.tw',
             'https://api2-pc.so-net.tw',
             'https://api3-pc.so-net.tw',
             'https://api4-pc.so-net.tw']

log = logging.getLogger(__name__)


class PCRClient:

    def __init__(self,
                 version,
                 *,
                 playerprefs: str = '',
                 pp_xml: dict = {},
                 udid: str = '',
                 short_udid: str = '',
                 viewer_id: str = '',
                 server_id: int = 0,
                 proxy: dict = None):
        # check arguments
        if playerprefs:
            pp_xml = dec_xml(playerprefs)

        udid = udid or pp_xml['UDID']
        short_udid = short_udid or pp_xml['SHORT_UDID']
        viewer_id = viewer_id or pp_xml['VIEWER_ID']
        server_id = server_id or int(pp_xml['TW_SERVER_ID'])

        if not udid or not short_udid or not viewer_id:
            raise ValueError(f'missing arguments: udid={udid}, short_udid={short_udid}, viewer_id={viewer_id}')

        if not version:
            raise ValueError(f'')

        if server_id > 4 or server_id < 1:
            raise ValueError('unacceptable server id, accept: (0,4]')

        log.debug(f'cert setup: server_id = {server_id}, viewer_id = {viewer_id}, short_udid = {short_udid}')
        log.debug(f'udid = {udid}')

        self.sec = PCRSecret(udid, short_udid, viewer_id, version)
        self.server_id = server_id
        self.proxy = proxy or {}

        # init when login()
        self.game_data = None
        self.token = ''.join(random.choices(string.digits, k=16))

        self.api_root = _API_ROOT[server_id - 1]

    async def register(self, udid=str(uuid.uuid1()), version: str = ''):
        log.warning(f'registering now, udid={udid}')

        self.sec = PCRSecret(udid, '0', '0', version)
        await self.call.tool.check_agreement()

        gh = {'Upgrade-Insecure-Requests': '1',
              'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; HD1900 Build/N2G48C; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/68.0.3440.70 Mobile Safari/537.36',
              'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
              'Accept-Encoding': 'gzip, deflate',
              'Accept-Language': 'zh-CN,en-US;q=0.9',
              'X-Requested-With': 'tw.sonet.princessconnect'}

        await get(self.api_root + '/agreement/first_view/1002/2001', headers=gh,
                  proxies=self.proxy)

        r = (await self.call.tool.signup(no_headers=False).exec())['data_headers']

        self.sec = PCRSecret(r['udid'], r['short_udid'], r['viewer_id'], version)
        log.info(f"{r['viewer_id']} {r['short_udid']} {r['udid']}")

    async def req(self, api: str, params: dict, no_headers=True):
        log.debug(f'exec request: api = {api}')
        data, headers = self.sec.prepare_req(api, params)

        resp = await post(self.api_root + api, data=data, headers=headers, timeout=5, proxies=self.proxy)
        res = await self.sec.handle_resp(resp, no_headers)
        log.debug(f'request success: api = {api}')
        log.debug(f'request result = {res}')
        return res

    async def login(self):
        await self.call.check.check_agreement(latency=0.5)
        await self.call.check.game_start(latency=0.5)
        self.game_data = await self.call.load.index()
        self.token = ''.join(random.choices(string.digits, k=16))

    async def pass_tutorial(self, latency=0.5):
        # tutorial
        steps = [1, 2, 3, 4, 5, 6, 7, 20, 30, 40, 50, 60, 100]
        for i in steps:
            await self.call.tutorial.update_step(i, 0, latency=latency)
            log.info(f'tutorial step: {i}')

    async def donate_equipment(self):
        clan_id = (await self.call.clan.info())['clan']['detail']['clan_id']
        chats = await self.call.clan.chat_info_list(clan_id)

        equip_reqs = filter(lambda x: x['user_donation_num'] == 0 and x['donation_num'] <= 8, chats['equip_requests'])
        chat_reqs = filter(lambda x: x['message_type'] == 2 and x['create_time'] > int(time.time()) - 28800,
                           chats['clan_chat_message'])

        for c in chat_reqs:
            e = functools.reduce(lambda x, y: y if y['message_id'] == c['message_id'] else x, equip_reqs, {})
            if not e:
                continue
            u = functools.reduce(lambda x, y: y if y['equip_id'] == e['equip_id'] else x, chats['user_equip_data'])
            await self.call.equipment.donate(clan_id, c['message_id'], 2, u['equip_count'])

    @property
    def call(self):
        return ReqDispatcher(self)
