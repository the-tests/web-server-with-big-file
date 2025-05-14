import config as cfg

from datetime import datetime
from copy import deepcopy
from json import dumps
from aiohttp import web

from worker import update_cache


async def get_item(r: web.Request) -> web.Response:
    print('REQUEST ->', datetime.now().isoformat())
    num = r.match_info.get('item_num', None)
    if num is None:
        return web.Response(
            text=(
                f"{r.app['THE_CACHE']['update_date']} / "
                f"{len(r.app['THE_CACHE']['items'])}"
            ),
            content_type='text/html',
            charset='utf-8',
        )
    else:
        num = int(num)
        if len(r.app['THE_CACHE']['items']) <= num:
            return web.Response(
                text='Item not found',
                content_type='text/html',
                charset='utf-8',
            )
        item = deepcopy(r.app['THE_CACHE']['items'][num])
        item['categories'] = list(item['categories'])
        return web.Response(
            text=dumps(item, indent=2),
            content_type='application/json',
            charset='utf-8',
        )


if __name__ == '__main__':
    app = web.Application()
    app['THE_CACHE'] = {'update_date': None, 'items': []}
    app.add_routes([web.get('/{item_num}', get_item)])
    app.add_routes([web.get('/', get_item)])
    # TODO: process is not exiting by keyboard interrupt
    app.cleanup_ctx.append(update_cache)
    print(f'Starting server on http://{cfg.HOST}:{cfg.PORT}')
    try:
        web.run_app(app, port=cfg.PORT, host=cfg.HOST)
    except KeyboardInterrupt:
        print('Bye bye')
