import boto3

from time import perf_counter
from json import loads

from datetime import datetime
from multiprocessing import Queue

from asyncio import sleep, create_task
from multiprocessing import Process
from aiohttp import web

import config as cfg


def start_download_in_background(q: Queue, key: str) -> None:

    def __target(q: Queue, key: str) -> None:
        print(f'Downloading of {key} started at', datetime.now().isoformat())
        s = perf_counter()
        raw_data = boto3.client(
            's3',
            region_name=cfg.REGION,
            aws_access_key_id=cfg.AWS_KEY,
            aws_secret_access_key=cfg.AWS_SECRET,
            endpoint_url=cfg.ENDPOINT_URL,
        ).get_object(
            Bucket=cfg.S3_BUCKET,
            Key=key,
        )['Body'].read()

        print(f'Downloading of {key} took {perf_counter() - s} seconds')

        s = perf_counter()
        data = loads(raw_data)
        for item in data:
            if item['categories'] is not None:
                item['categories'] = frozenset(item['categories'])

        print(
            f'Data conversion for {key} took {perf_counter() - s} seconds {len(data)}'
        )

        chunk_num = 0
        while len(data) > cfg.CHUNK_SIZE * chunk_num:
            q.put(data[cfg.CHUNK_SIZE * chunk_num:cfg.CHUNK_SIZE * (chunk_num + 1)])
            chunk_num += 1
        q.put(None)
        print(f'Queue size: {q.qsize()}')

    Process(target=__target, args=(q, key)).start()
    print('Download function started')


async def update_items(cache: dict, key: str) -> None:
    '''
    Warning: cache will be modified in place
    '''
    items = []
    q = Queue()
    start_download_in_background(q, key)
    while True:
        if q.empty():
            await sleep(0.1)
            continue
        items_chunk = q.get()
        if items_chunk is None:
            print('Items length:', len(items))
            break
        items += items_chunk
        await sleep(0.0001)
    q.close()
    cache[key] = items
    print('Copy to cache is completed')


async def update_cache(app: web.Application):
    async def __task(app):
        while True:
            if len(app['THE_CACHE']['keys_to_update']) == 0:
                print('No keys to update')
            else:
                # use slice to avoid modifying the list while iterating
                for key in tuple(app['THE_CACHE']['keys_to_update']):
                    await update_items(app['THE_CACHE']['data'], key)
                app['THE_CACHE']['update_date'] = datetime.now().isoformat()    
            await sleep(cfg.TIMEOUT)

    create_task(__task(app))
    yield
