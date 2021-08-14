import asyncio

from nowem import PCRClient, PCRAPIException


async def main():
    c = PCRClient(playerprefs='../data/t1-reader.xml', version='2.8.1')
    print(c.sec.viewer_id)
    await c.login()

    # tutorial
    await c.pass_tutorial()

    # re login
    await c.login()
    await c.call.home.index(1, True).exec()
    await c.call.payment.item_list().exec()
    await c.call.payment.send_log().exec()

    await c.call.account.publish_transition_code('ZZxxcc123').exec()

    qid = 11001001  # normal
    # qid = 12001001
    while True:
        print(qid)
        try:
            r = await c.call.quest.finish(await c.call.quest.start(qid).exec()).exec(1)
        except PCRAPIException as e:
            if e.message == '體力目前不足。':
                break
        else:
            print(r)
            qid = r['unlock_quest_list'][0]

    await c.call.mission.index().exec()
    await c.call.mission.accept(3).exec()
    await c.call.mission.index().exec()
    await c.call.mission.accept(1).exec()
    await c.call.mission.index().exec()
    await c.call.mission.accept(2).exec()

    # event
    # await c.call.event.hatsune.top(10061).exec()
    # await c.call.story.check(5061000).exec()
    # await c.call.story.start(5061000).exec()
    # di = await c.call.event.hatsune.quest_top(10061).exec()
    # qsr = await c.call.event.hatsune.quest_start(10061, 10061101).exec()
    # await c.call.event.hatsune.quest_finish(10061, qsr).exec()
    # await c.call.event.hatsune.top(10061).exec()
    # await c.call.event.hatsune.gacha_index(10061).exec()
    # await c.call.event.hatsune.gacha_exec(10061, 10, 10).exec()
    # for i in di['quest_list']:
    #     if i['clear_flag'] != 0:
    #         continue
    #     print(i)
    #     qsr = await c.call.event.hatsune.quest_start(10061, i['quest_id']).exec()
    #     r = await c.call.event.hatsune.quest_finish(10061, qsr).exec()
    #     print(r)
    # while True:
    #     qsr = await c.call.event.hatsune.quest_start(10061, 10061110).exec()
    #     r = await c.call.event.hatsune.quest_finish(10061, qsr).exec()
    #     print(r)
    #     await asyncio.sleep(1)


asyncio.get_event_loop().run_until_complete(main())
