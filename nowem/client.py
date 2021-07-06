import functools
import logging
import random
import string
import time
from typing import Union

from .aiorequests import post
from .playerprefs import dec_xml
from .secret import PCRSecret

_API_ROOT = ['https://api-pc.so-net.tw',
             'https://api2-pc.so-net.tw',
             'https://api3-pc.so-net.tw',
             'https://api4-pc.so-net.tw']

log = logging.getLogger(__name__)


class PCRClient:

    def __init__(self,
                 *,
                 playerprefs: str = None,
                 udid: str = None,
                 short_udid: str = None,
                 viewer_id: str = None,
                 server_id: int = None,
                 proxy: dict = None):
        # check arguments
        if not playerprefs:
            if not udid or not short_udid or not viewer_id:
                raise Exception('missing playerprefs and ids')

        udid = udid or dec_xml(playerprefs)['UDID']
        short_udid = short_udid or dec_xml(playerprefs)['SHORT_UDID']
        viewer_id = viewer_id or dec_xml(playerprefs)['VIEWER_ID']
        server_id = server_id or int(dec_xml(playerprefs)['TW_SERVER_ID'])
        if server_id > 4 or server_id < 1:
            raise ValueError('unacceptable server id, accept: (0,4]')

        log.debug(f'cert setup: server_id = {server_id}, viewer_id = {viewer_id}')
        log.debug(f'udid = {udid}, short_udid = {short_udid}')

        self.sec = PCRSecret(udid, short_udid, viewer_id)
        self.server_id = server_id
        self.proxy = proxy or {}

        # init when login()
        self.game_data = None
        self.token = ''.join(random.choices(string.digits, k=16))

        self.api_root = _API_ROOT[server_id - 1]

    async def req(self, api: str, params: dict, no_headers=True):
        log.debug(f'exec request: api = {api}')
        log.debug(f'params = {params}')
        data, headers = self.sec.prepare_req(api, params)
        log.debug(f'headers = {headers}')

        resp = await post(self.api_root + api, data=data, headers=headers, timeout=5, proxies=self.proxy)
        res = await self.sec.handle_resp(resp, no_headers)
        log.debug(f'request success: api = {api}')
        log.debug(f'request result = {res}')
        return res

    async def login(self):
        await self.call.check.check_agreement().exec()
        await self.call.check.game_start().exec()
        self.game_data = await self.call.load.index().exec()
        self.token = ''.join(random.choices(string.digits, k=16))

    async def donate_equipment(self):
        clan_id = (await self.call.clan.info().exec())['clan']['detail']['clan_id']
        chats = await self.call.clan.chat_info_list(clan_id).exec()

        equip_reqs = filter(lambda x: x['user_donation_num'] == 0 and x['donation_num'] <= 8, chats['equip_requests'])
        chat_reqs = filter(lambda x: x['message_type'] == 2 and x['create_time'] > int(time.time()) - 28800,
                           chats['clan_chat_message'])

        for c in chat_reqs:
            e = functools.reduce(lambda x, y: y if y['message_id'] == c['message_id'] else x, equip_reqs, {})
            if not e:
                continue
            u = functools.reduce(lambda x, y: y if y['equip_id'] == e['equip_id'] else x, chats['user_equip_data'])
            await self.call.equipment.donate(clan_id, c['message_id'], 2, u['equip_count']).exec()

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
        self.client: Union[PCRClient, None] = None
        self.api = ''
        self.params = {}

    async def exec(self, no_headers=True) -> dict:
        return await self.client.req(self.api, self.params, no_headers)


class _ReqBase(_Req):
    def __init__(self, c: PCRClient):
        super().__init__()
        self.client = c

    @property
    def check(self):
        return _ReqCheck(self)

    @property
    def load(self):
        return _ReqLoad(self)

    @property
    def home(self):
        return _ReqHome(self)

    @property
    def clan(self):
        return _ReqClan(self)

    @property
    def profile(self):
        return _ReqProfile(self)

    @property
    def payment(self):
        return _ReqPayment(self)

    @property
    def equipment(self):
        return _ReqEquipment(self)

    @property
    def tutorial(self):
        return _ReqTutorial(self)

    @property
    def quest(self):
        return _ReqQuest(self)

    @property
    def shop(self):
        return _ReqShop(self)

    @property
    def mission(self):
        return _ReqMission(self)

    @property
    def room(self):
        return _ReqRoom(self)

    @property
    def event(self):
        return _ReqEvent(self)

    @property
    def story(self):
        return _ReqStory(self)

    @property
    def present(self):
        return _ReqPresent(self)


class _ReqPresent(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/present'

    @end_point
    def index(self):
        self.params = {'time_filter': -1, 'type_filter': 0, 'desc_flag': True, 'offset': 0}

    @end_point
    def receive_all(self):
        self.params = {'time_filter': -1, 'type_filter': 0, 'desc_flag': True}


class _ReqStory(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/story'

    @end_point
    def check(self, story_id: int):
        self.params = {'story_id': story_id}

    @end_point
    def start(self, story_id: int):
        self.params = {'story_id': story_id}


class _ReqEvent(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/event'

    class _Hatsune(_Req):
        def __init__(self, r: _Req):
            super().__init__()
            self.client = r.client
            self.api = r.api + '/hatsune'

        @end_point
        def top(self, event_id: int):
            self.params = {'event_id': event_id}

        @end_point
        def gacha_index(self, event_id: int):
            self.params = {'event_id': event_id, 'gacha_id': event_id}

        @end_point
        def gacha_exec(self, event_id: int, gacha_times: int, current_cost_num: int):
            self.params = {'event_id': event_id, 'gacha_id': event_id,
                           'gacha_times': gacha_times, 'current_cost_num': current_cost_num,
                           'loop_box_multi_gacha_flag': 0}

        @end_point
        def quest_top(self, event_id: int):
            self.params = {'event_id': event_id}

        @end_point
        def boss_battle_start(self, event_id: int, boss_id: int, current_ticket_num: int):
            self.params = {'event_id': event_id, 'boss_id': boss_id, 'current_ticket_num': current_ticket_num}

        # @end_point
        # def boss_battle_finish(self, event_id: int, boss_id: int):
        #     self.params = {'event_id': event_id, 'boss_id': boss_id}
        # complex, pass

        @end_point
        def quest_start(self, event_id: int, quest_id: int, owner_viewer_id: int = 0, support_unit_id: int = 0,
                        support_battle_rarity: int = 0, is_friend: bool = False):
            # quest_id = 11000000 + chap_n * 1000 + map_n (normal)
            # quest_id = 12000000 + chap_n * 1000 + map_n (hard)
            self.params = {'event_id': int(event_id),
                           'quest_id': int(quest_id),
                           'token': self.client.token,
                           'owner_viewer_id': owner_viewer_id,
                           'support_unit_id': support_unit_id,
                           'support_battle_rarity': support_battle_rarity,
                           'is_friend': 1 if is_friend else 0}

        @end_point
        def quest_finish(self, event_id: int, quest_start_result: dict, auto_clear: bool = False,
                         owner_viewer_id: int = 0,
                         support_position: int = 0,
                         is_friend: bool = False):
            self.params = {'event_id': event_id, 'quest_id': quest_start_result['quest_id'],
                           'remain_time': 73479,
                           'unit_hp_list': [],
                           'auto_clear': 1 if auto_clear else 0, 'fps': 60,
                           'owner_viewer_id': owner_viewer_id, 'support_position': support_position,
                           'is_friend': 1 if is_friend else 0}
            for i in quest_start_result['skin_data_for_request']:
                self.params['unit_hp_list'].append(
                    {'viewer_id': self.client.sec.viewer_id, 'unit_id': i['unit_id'], 'hp': 100})
            for i in quest_start_result['quest_wave_info'][2]['enemy_info_list']:
                self.params['unit_hp_list'].append({'viewer_id': 0, 'unit_id': i['enemy_id'], 'hp': 0})

    @property
    def hatsune(self):
        return _ReqEvent._Hatsune(self)


class _ReqRoom(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/room'

    @end_point
    def start(self):
        self.params = {}

    @end_point
    def receive_all(self):
        self.params = {}

    @end_point
    def level_up_start(self, serial_id: int, floor_number: int = 1):
        # 5:stamina 6:exp 7:mana
        self.params = {'floor_number': floor_number, 'serial_id': serial_id}


class _ReqMission(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/mission'

    @end_point
    def index(self):
        self.params = {'request_flag': {'quest_clear_rank': 0}}

    @end_point
    def accept(self, type: int, id: int = 0, buy_id: int = 0):
        # type:
        #   1: daily
        #   2: normal
        #   4: medal
        # id:
        #   0: all
        self.params = {'type': type, 'id': id, 'buy_id': buy_id}


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


class _ReqTutorial(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/tutorial'

    @end_point
    def update_step(self, step: int, skip: int, user_name: str = ''):
        self.params = {'step': step, 'skip': skip, 'user_name': user_name}


class _ReqHome(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/home'

    @end_point
    def index(self, message_id: int, is_first: bool):
        self.params = {'message_id': message_id,
                       'tips_id_list': [],
                       'is_first': 1 if is_first else 0,
                       'gold_history': 0}


class _ReqClan(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/clan'

    @end_point
    def info(self):
        self.params = {'clan_id': 0, 'get_user_equip': 1}

    @end_point
    def chat_info_list(self, clan_id, count: int = 10, wait_interval: int = 3, search_date: str = '2099-12-31'):
        self.params = {
            'clan_id': clan_id,
            'start_message_id': 0,
            'search_date': search_date,
            'direction': 1,
            'count': count,
            'wait_interval': wait_interval,
            'update_message_ids': [],
        }


class _ReqShop(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/shop'

    @end_point
    def recover_stamina(self):
        jewel = self.client.game_data['user_jewel']['free_jewel'] + self.client.game_data['user_jewel']['paid_jewel']
        if jewel < 100:
            log.warning(f'low jewel:{jewel}')
        self.params = {'current_currency_num': jewel}


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

    @end_point
    def start(self, quest_id: int, owner_viewer_id: int = 0, support_unit_id: int = 0,
              support_battle_rarity: int = 0, is_friend: bool = False):
        # quest_id = 11000000 + chap_n * 1000 + map_n (normal)
        # quest_id = 12000000 + chap_n * 1000 + map_n (hard)
        self.params = {'quest_id': quest_id,
                       'token': ''.join(random.choices(string.digits, k=16)),
                       'owner_viewer_id': owner_viewer_id,
                       'support_unit_id': support_unit_id,
                       'support_battle_rarity': support_battle_rarity,
                       'is_friend': 1 if is_friend else 0}

    @end_point
    def finish(self, quest_start_result: dict, auto_clear: bool = False, owner_viewer_id: int = 0,
               support_position: int = 0,
               is_friend: bool = False):
        self.params = {'quest_id': quest_start_result['quest_id'], 'remain_time': 73479,
                       'unit_hp_list': [],
                       'auto_clear': 1 if auto_clear else 0, 'fps': 60,
                       'owner_viewer_id': owner_viewer_id, 'support_position': support_position,
                       'is_friend': 1 if is_friend else 0}
        for i in quest_start_result['skin_data_for_request']:
            self.params['unit_hp_list'].append(
                {'viewer_id': self.client.sec.viewer_id, 'unit_id': i['unit_id'], 'hp': 100})
        for i in quest_start_result['quest_wave_info'][2]['enemy_info_list']:
            self.params['unit_hp_list'].append({'viewer_id': 0, 'unit_id': i['enemy_id'], 'hp': 0})


class _ReqEquipment(_Req):
    def __init__(self, r: _Req):
        super().__init__()
        self.client = r.client
        self.api = r.api + '/equipment'

    @end_point
    def donate(self, clan_id: int, message_id: int, donation_num: int, current_equip_num: int):
        self.params = {'clan_id': clan_id,
                       'message_id': message_id,
                       'donation_num': donation_num,
                       'current_equip_num': current_equip_num}
