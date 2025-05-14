import aioboto3

from time import perf_counter
from json import loads

from asyncio import new_event_loop
from datetime import datetime
from multiprocessing import Queue

from asyncio import sleep, create_task
from multiprocessing import Process
from aiohttp import web

import config as cfg

async def update_cache(app: web.Application):

    def __blocking_background_task(q: Queue):

        async def __do_async_stuff():
            async with aioboto3.Session().client(
                's3',
                region_name=cfg.REGION,
                aws_access_key_id=cfg.AWS_KEY,
                aws_secret_access_key=cfg.AWS_SECRET,
                endpoint_url=cfg.ENDPOINT_URL,
            ) as client:
                async with (
                    await client.get_object(
                        Bucket=cfg.S3_BUCKET,
                        Key=cfg.S3_KEY,
                    )
                )['Body'] as stream:
                    return await stream.read()

        print('Heavy load started at', datetime.now().isoformat())
        s = perf_counter()

        loop = new_event_loop()
        raw_data = loop.run_until_complete(__do_async_stuff())
        print(f'Heavy load async request took {perf_counter() - s} seconds')

        data = loads(raw_data)
        for item in data:
            if item['categoreis'] is not None:
                item['categoreis'] = frozenset(item['categoreis'])

        print(f'Heavy load took {perf_counter() - s} seconds {len(data)}')

        chunk_num = 0
        while len(data) > cfg.CHUNK_SIZE * chunk_num:
            q.put(data[cfg.CHUNK_SIZE * chunk_num:cfg.CHUNK_SIZE * (chunk_num + 1)])
            chunk_num += 1
        q.put(None)
        print(f'Queue size: {q.qsize()}')

    async def __task(app):
        while True:
            items = []
            q = Queue()
            Process(target=__blocking_background_task, args=(q,)).start()
            print('Blocking function started')
            while True:
                if q.empty():
                    await sleep(0)
                    continue
                item = q.get()
                if item is None:
                    print('Items length:', len(items))
                    break
                items += item
                await sleep(0)
            q.close()
            app['THE_CACHE']['update_date'] = datetime.now().isoformat()
            app['THE_CACHE']['items'] = items
            await sleep(cfg.TIMEOUT)

    create_task(__task(app))
    yield
