import functools
import logging

from .aiorequests import post
from .playerprefs import dec_xml
from .secret import PCRSecret

_API_ROOT = ['https://api-pc.so-net.tw',
             'https://api2-pc.so-net.tw',
             'https://api3-pc.so-net.tw',
             'https://api4-pc.so-net.tw']


class PCRClient:
    logger = logging.getLogger(__name__)

    def __init__(self,
                 *,
                 playerprefs: str = None,
                 udid: str = None,
                 short_udid: str = None,
                 viewer_id: str = None,
                 server_id: int = None,
                 proxy: dict = None):
        if not playerprefs:
            if not udid or not short_udid or not viewer_id:
                raise Exception('missing playerprefs and ids')
        udid = udid or dec_xml(playerprefs)['UDID']
        short_udid = short_udid or dec_xml(playerprefs)['SHORT_UDID']
        viewer_id = viewer_id or dec_xml(playerprefs)['VIEWER_ID']
        server_id = server_id or int(dec_xml(playerprefs)['TW_SERVER_ID'])

        self.logger.info(f'cert setup: server_id = {server_id}, viewer_id = {viewer_id}')
        self.logger.debug(f'udid = {udid}, short_udid = {short_udid}')

        self.sec = PCRSecret(udid, short_udid, viewer_id)
        self.server_id = server_id
        self.proxy = proxy or {}

        # init when login()
        self.game_data = None

        # TODO: adapt other servers
        self.api_root = _API_ROOT[server_id - 1]

    async def req(self, api: str, params: dict):
        self.logger.info(f'exec request: api = {api}')
        self.logger.debug(f'params = {params}')
        data, headers = self.sec.prepare_req(api, params)
        self.logger.debug(f'headers = {headers}')

        resp = await post(self.api_root + api, data=data, headers=headers, timeout=5, proxies=self.proxy)
        res = await self.sec.handle_resp(resp)
        self.logger.info(f'request success: api = {api}')
        self.logger.debug(f'request result = {res}')

        return res

    async def login(self):
        await self.call.check().check_agreement().exec()
        await self.call.check().game_start().exec()
        self.game_data = await self.call.load().index().exec()

    @property
    def call(self):
        return _ReqBase(self)


def end_point(func):
    @functools.wraps(func)
    def dec(*args, **kwargs) -> _Req:
        args[0].api += f'/{func.__name__}'
        func(*args, **kwargs)
        return args[0]

    return dec


class _Req:
    def __init__(self):
        self.client = None
        self.api = ''
        self.params = {}

    async def exec(self) -> dict:
        return await self.client.req(self.api, self.params)


class _ReqBase(_Req):
    def __init__(self, c: PCRClient):
        super().__init__()
        self.client = c

    def check(self):
        return _ReqCheck(self)

    def load(self):
        return _ReqLoad(self)

    def clan(self):
        return _ReqClan(self)

    def profile(self):
        return _ReqProfile(self)

    def payment(self):
        return _ReqPayment(self)


class _ReqCheck(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/check'

    @end_point
    def check_agreement(self):
        self.params = {}

    @end_point
    def game_start(self):
        self.params = {
            'app_type': 0,
            'campaign_data': '',
            'campaign_sign': '38082d22ef968d0e2c3fdd7cea75d716',
            'campaign_user': 114044,
            'endpointArn': '',
            'countrycode': 'CN',
            'FOXYOROKOBINODANCE': 'dec925fa8e3d6af9310a4714e4362ff5',
            'FOXYOROKOBINOMAI': 'e0773a614b41a3b2e44cdfd063e59075'
        }


class _ReqLoad(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/load'

    @end_point
    def index(self):
        self.params = {'carrier': 'blackshark'}


class _ReqClan(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/clan'

    @end_point
    def info(self):
        self.params = {'clan_id': 0, 'get_user_equip': 1}

    @end_point
    def chat_info_list(self, clan_id, count: int = 30, wait_interval: int = 3):
        self.params = {
            'clan_id': clan_id,
            'start_message_id': 0,
            'search_date': '2099-12-31',
            'direction': 1,
            'count': count,
            'wait_interval': wait_interval,
            'update_message_ids': [],
        }


class _ReqProfile(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/profile'

    @end_point
    def get_profile(self, uid: int):
        self.params = {'target_viewer_id': uid}


class _ReqPayment(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/payment'

    @end_point
    def item_list(self):
        self.params = {}

    @end_point
    def send_log(self, log_key: str = None, log_message: str = None):
        self.params = {'log_key': log_key or 'evInitializeFailed',
                       'log_message': log_message or 'Error checking for billing v3 support. (response: 3:Unknown IAB '
                                                     'Helper Error)'}


class _ReqQuest(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/quest'

    @end_point
    def quest_skip(self, quest_id: int, random_count: int, current_ticket_num: int):
        self.params = {'quest_id': quest_id, 'random_count': random_count, 'current_ticket_num': current_ticket_num}
