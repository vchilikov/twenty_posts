import asyncio
import concurrent.futures
import sys

import aiohttp_jinja2
import asyncio_redis
import jinja2
from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest

from messages import Messages
from settings import REDIS_CONNECTION, MESSAGES_CHANNEL, DEFAULT_PORT

messages = Messages.get_instance()


async def message_subscribe():
    connection = await asyncio_redis.Connection.create(**REDIS_CONNECTION)
    try:
        subscriber = await connection.start_subscribe()
        await subscriber.subscribe([MESSAGES_CHANNEL])
        while True:
            reply = await subscriber.next_published()
            messages.append(repr(reply.value))
            print('Сообщение: ', repr(reply.value))
    finally:
        connection.close()


@aiohttp_jinja2.template('index.html')
async def index(request):
    return {
        'messages': messages
    }


async def post_index(request):
    data = await request.post()
    connection = await asyncio_redis.Connection.create(**REDIS_CONNECTION)
    try:
        await connection.publish(MESSAGES_CHANNEL, data['message'])
    finally:
        connection.close()
    return web.json_response({
        'status': 'ok'
    })


async def long_poll(request):
    last_pk = request.GET['last_pk']
    while True:
        if messages.has_new_pk(last_pk):
            break
        try:
            await asyncio.sleep(0.5)
        except concurrent.futures._base.CancelledError:
            raise HTTPBadRequest
    return web.json_response({'status': 'ok', 'result': messages})


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT

    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

    app.router.add_get('/', index)
    app.router.add_post('/', post_index)
    app.router.add_get('/long_poll/', long_poll)

    app['redis_listener'] = app.loop.create_task(message_subscribe())

    web.run_app(app, port=port)
