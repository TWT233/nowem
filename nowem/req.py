import asyncio
import functools
import logging
import random
import re
import string
from typing import Union

from . import client
from .secret import PCRSecret

log = logging.getLogger(__name__)


def end_point(func):
    @functools.wraps(func)
    async def dec(*args, **kwargs) -> _Req:
        self = args[0]
        self.api += f'/{func.__name__}'
        no_headers = kwargs.pop('no_headers', True)
        latency = kwargs.pop('latency', 0.5)

        func(*args, **kwargs)

        res = await self.client.req(self.api, self.params, no_headers)
        await asyncio.sleep(latency)
        return res

    return dec


def route_only(cls):
    def fake_init(self, r: _Req):
        self.api = r.api + f"/{re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()}"
        self.client = r.client
        self.params = r.params

    cls.__init__ = fake_init
    return cls


class _Req:
    def __init__(self):
        self.client: Union['client.PCRClient', None] = None
        self.api = ''
        self.params = {}


class ReqDispatcher(_Req):
    def __init__(self, c: 'client.PCRClient'):
        super().__init__()
        self.client = c

    @property
    def daily_task(self):
        return DailyTask(self)

    @property
    def check(self):
        return Check(self)

    @property
    def load(self):
        return Load(self)

    @property
    def home(self):
        return Home(self)

    @property
    def clan(self):
        return Clan(self)

    @property
    def clan_battle(self):
        return ClanBattle(self)

    @property
    def profile(self):
        return Profile(self)

    @property
    def payment(self):
        return Payment(self)

    @property
    def equipment(self):
        return Equipment(self)

    @property
    def tutorial(self):
        return Tutorial(self)

    @property
    def quest(self):
        return Quest(self)

    @property
    def shop(self):
        return Shop(self)

    @property
    def mission(self):
        return Mission(self)

    @property
    def room(self):
        return Room(self)

    @property
    def event(self):
        return Event(self)

    @property
    def story(self):
        return Story(self)

    @property
    def present(self):
        return Present(self)

    @property
    def account(self):
        return Account(self)

    @property
    def tool(self):
        return Tool(self)

    @property
    def chara_fortune(self):
        return CharaFortune(self)


@route_only
class DailyTask(_Req):
    @end_point
    def top(self, setting_alchemy_count=1, is_check_by_term_normal_gacha=0):
        """{
        "setting_alchemy_count": 1,
        "is_check_by_term_normal_gacha": 0,
        }"""
        self.params = {
            'settings_alchemy_count': setting_alchemy_count,
            'is_check_by_term_normal_gacha': is_check_by_term_normal_gacha,
        }


@route_only
class CharaFortune(_Req):
    @end_point
    def draw(self, fortune_id: int, unit_id: int):  # anniversary
        self.params = {'fortune_id': fortune_id, 'unit_id': unit_id}


@route_only
class Tool(_Req):
    @end_point
    def check_agreement(self):
        self.params = {}

    @end_point
    def signup(self):
        self.params = {'carrier': 'OnePlus', 'agreement_ver': 1002, 'policy_ver': 2001}


@route_only
class Account(_Req):
    @end_point
    def publish_transition_code(self, pwd: str):
        self.params = {'password': PCRSecret.md5(pwd)}


@route_only
class Present(_Req):
    @end_point
    def index(self):
        self.params = {'time_filter': -1, 'type_filter': 0, 'desc_flag': True, 'offset': 0}

    @end_point
    def receive_all(self):
        self.params = {'time_filter': -1, 'type_filter': 0, 'desc_flag': True}


@route_only
class Story(_Req):
    """
    check: enter the scene
    start: finish reading

    makeup of the story_id:
    e.g. 2001000:  2 | 0 | 01|000
                   a | b | c | d
        a: type
            1: chara
            2: mainline
            3: guild
            4: extra
            9: special event(such as kaiser_battle or anniversary)
        b: episode(only available in mainline story, a==2)
        c: chapter(when a!=2, usually used with b)
        d: story
    """

    @end_point
    def check(self, story_id: int):
        self.params = {'story_id': story_id}

    @end_point
    def start(self, story_id: int):
        self.params = {'story_id': story_id}

    @end_point
    def force_release(self, story_group_id: int):
        self.params = {'story_group_id': story_group_id}


@route_only
class Event(_Req):
    @route_only
    class Hatsune(_Req):
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
        return Event.Hatsune(self)


@route_only
class Room(_Req):
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


@route_only
class Mission(_Req):
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


@route_only
class Check(_Req):
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


@route_only
class Load(_Req):
    @end_point
    def index(self):
        self.params = {'carrier': 'OnePlus'}


@route_only
class Tutorial(_Req):
    @end_point
    def update_step(self, step: int, skip: int, user_name: str = ''):
        self.params = {'step': step, 'skip': skip, 'user_name': user_name}


@route_only
class Home(_Req):
    @end_point
    def index(self, message_id: int, is_first: bool):
        self.params = {'message_id': message_id,
                       'tips_id_list': [],
                       'is_first': 1 if is_first else 0,
                       'gold_history': 0}


@route_only
class Clan(_Req):
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


@route_only
class ClanBattle(_Req):
    @end_point
    def top(self, clan_id: int, is_first: int, current_clan_battle_coin: int):
        self.params = {
            'clan_id': clan_id,
            'is_first': is_first,
            'current_clan_battle_coin': current_clan_battle_coin,
        }


@route_only
class Shop(_Req):
    @end_point
    def recover_stamina(self):
        jewel = self.client.game_data['user_jewel']['free_jewel'] + self.client.game_data['user_jewel']['paid_jewel']
        if jewel < 100:
            log.warning(f'low jewel:{jewel}')
        self.params = {'current_currency_num': jewel}


@route_only
class Profile(_Req):
    @end_point
    def get_profile(self, uid: int):
        self.params = {'target_viewer_id': uid}


@route_only
class Payment(_Req):
    @end_point
    def item_list(self):
        self.params = {}

    @end_point
    def send_log(self, log_key: str = None, log_message: str = None):
        self.params = {'log_key': log_key or 'evInitializeFailed',
                       'log_message': log_message or 'Error checking for billing v3 support. (response: 3:Unknown IAB '
                                                     'Helper Error)'}


@route_only
class Quest(_Req):
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


@route_only
class Equipment(_Req):
    @end_point
    def donate(self, clan_id: int, message_id: int, donation_num: int, current_equip_num: int):
        self.params = {'clan_id': clan_id,
                       'message_id': message_id,
                       'donation_num': donation_num,
                       'current_equip_num': current_equip_num}
