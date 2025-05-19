import config as cfg

from datetime import datetime
from copy import deepcopy
from json import dumps
from aiohttp import web

from asyncio import Lock
from uuid import uuid4

from worker import update_cache, update_items


async def overall(r: web.Request) -> web.Response:
    print('REQUEST [overall] ->', datetime.now().isoformat())
    data = { k: len(v) for k, v in r.app['THE_CACHE']['data'].items() }
    data['__update_date'] = r.app['THE_CACHE']['update_date']
    return web.Response(
        text=dumps(data),
        content_type='application/json',
        charset='utf-8',
    )


async def get_item(r: web.Request) -> web.Response:
    print('REQUEST [get_item] ->', datetime.now().isoformat())
    num = r.match_info.get('item_num', None)
    key = r.match_info.get('key', None)
    if num is None or key is None:
        return web.Response(
            status=400,
            text='Key and item number are required',
            content_type='text/html',
            charset='utf-8',
        )
    num = int(num)
    if len(r.app['THE_CACHE']['data'].get(key, [])) <= num:
        return web.Response(
            text=f'Item `{key}:{num}` not found',
            content_type='text/html',
            charset='utf-8',
        )
    item = deepcopy(r.app['THE_CACHE']['data'][key][num])
    item['categories'] = list(item['categories'])
    return web.Response(
        text=dumps(item, indent=2),
        content_type='application/json',
        charset='utf-8',
    )


async def download(r: web.Request) -> web.Response:
    rqid = uuid4().hex
    print(f'REQUEST [{rqid}] ->', datetime.now().isoformat())
    key = r.match_info.get('key', None)
    if key is None:
        return web.Response(
            status=400,
            text='Key is required',
            content_type='text/html',
            charset='utf-8',
        )
    print(f'  [{rqid}] -> check if key is already in cache')
    if key not in r.app['THE_CACHE']['data']:
        async with r.app['THE_CACHE']['locks'].setdefault(key, Lock()):
            print(f'  [{rqid}] -> check if key is already in cache after lock')
            if key not in r.app['THE_CACHE']['data']:
                try:
                    print(f'  [{rqid}] -> key is not in cache, downloading')
                    await update_items(r.app['THE_CACHE']['data'], key)
                finally:
                    if key in r.app['THE_CACHE']['locks']:
                        print(f'  [{rqid}] -> removing lock')
                        del r.app['THE_CACHE']['locks'][key]
        r.app['THE_CACHE']['keys_to_update'].add(key)
    return web.Response(
        text=(
            f'Download of {key} completed. Data length is '
            f'{len(r.app["THE_CACHE"]["data"][key])}'
        ),
        content_type='text/html',
        charset='utf-8',
    )


async def remove(r: web.Request) -> web.Response:
    print('REQUEST [remove] ->', datetime.now().isoformat())
    key = r.match_info.get('key', None)
    if key is None:
        return web.Response(
            status=400,
            text='Key is required',
            content_type='text/html',
            charset='utf-8',
        )
    try:
        async with r.app['THE_CACHE']['locks'].setdefault(key, Lock()):
            if key in r.app['THE_CACHE']['data']:
                del r.app['THE_CACHE']['data'][key]
            if key in r.app['THE_CACHE']['keys_to_update']:
                r.app['THE_CACHE']['keys_to_update'].remove(key)
    finally:
        if key in r.app['THE_CACHE']['locks']:
            print('  [remove] -> removing lock')
            del r.app['THE_CACHE']['locks'][key]

    return web.Response(status=204)


if __name__ == '__main__':
    app = web.Application()
    app['THE_CACHE'] = {
        'update_date': None,
        'data': {},
        'keys_to_update': set(),
        'locks': {},
    }
    app.add_routes([web.get('/get/{key}/{item_num}', get_item)])
    app.add_routes([web.get('/', overall)])
    app.add_routes([web.get('/d/{key}', download)])
    app.add_routes([web.get('/r/{key}', remove)])
    # TODO: process is not exiting by keyboard interrupt
    app.cleanup_ctx.append(update_cache)
    print(f'Starting server on http://{cfg.HOST}:{cfg.PORT}')
    try:
        web.run_app(app, port=cfg.PORT, host=cfg.HOST)
    except KeyboardInterrupt:
        print('Bye bye')
