import asyncio

from nowem import PCRClient, PCRAPIException


async def main():
    ppf = 'tw.sonet.princessconnect.v2.playerprefs'
    c = PCRClient('3.7.0', playerprefs=f'../data/{ppf}.xml')
    print(c.sec.viewer_id)
    await c.login()

    # tutorial
    await c.pass_tutorial()

    # re login
    await c.login()
    await c.call.home.index(1, True)
    await c.call.payment.item_list()
    await c.call.payment.send_log()

    await c.call.account.publish_transition_code('ZZxxcc123')

    qid = 11001001  # normal
    # qid = 12001001
    while True:
        print(qid)
        try:
            r = await c.call.quest.finish(await c.call.quest.start(qid))
        except PCRAPIException as e:
            if e.message == '體力目前不足。':
                break
        else:
            print(r)
            qid = r['unlock_quest_list'][0]

    await c.call.mission.index()
    await c.call.mission.accept(3)
    await c.call.mission.index()
    await c.call.mission.accept(1)
    await c.call.mission.index()
    await c.call.mission.accept(2)

    # event
    # await c.call.event.hatsune.top(10061)
    # await c.call.story.check(5061000)
    # await c.call.story.start(5061000)
    # di = await c.call.event.hatsune.quest_top(10061)
    # qsr = await c.call.event.hatsune.quest_start(10061, 10061101)
    # await c.call.event.hatsune.quest_finish(10061, qsr)
    # await c.call.event.hatsune.top(10061)
    # await c.call.event.hatsune.gacha_index(10061)
    # await c.call.event.hatsune.gacha_exec(10061, 10, 10)
    # for i in di['quest_list']:
    #     if i['clear_flag'] != 0:
    #         continue
    #     print(i)
    #     qsr = await c.call.event.hatsune.quest_start(10061, i['quest_id'])
    #     r = await c.call.event.hatsune.quest_finish(10061, qsr)
    #     print(r)
    # while True:
    #     qsr = await c.call.event.hatsune.quest_start(10061, 10061110)
    #     r = await c.call.event.hatsune.quest_finish(10061, qsr)
    #     print(r)
    #     await asyncio.sleep(1)


asyncio.get_event_loop().run_until_complete(main())
