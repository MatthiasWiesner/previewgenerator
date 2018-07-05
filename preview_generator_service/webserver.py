# -*- coding: utf-8 -*-
import json
import time
import base64
import logging
import aio_pika
from aiohttp import web
from pprint import pformat
from functools import wraps


def auth_required(f):
    @wraps(f)
    def wrapper(self, request):
        auth_header = request.headers.get('Authorization', None)
        if auth_header:
            key = auth_header.split('Basic ')[-1]
            if key in self.auth_keys:
                return f(self, request)

        raise web.HTTPForbidden(
            headers={'WWW-Authenticate': 'Basic realm="Preview Generator Service"'})
    return wrapper


class Webserver(object):
    def __init__(self, settings):
        self.settings = settings
        self.amqp_config = settings.config['amqp']
        print(settings.config)
        auth_user = settings.config['webserver']['auth_userpw']
        self.auth_keys = [base64.b64encode(bytes(auth_user, 'utf-8')).decode('ascii')]

    def run(self):
        app = web.Application()
        app.router.add_get('/', self.index)
        app.router.add_post('/generatepreview', self.handle_generate_preview)

        app.on_startup.append(self.on_startup)
        app.on_shutdown.append(self.on_shutdown)

        self.app = app
        web.run_app(app)

    def stop(self):
        self.app.loop.close()

    async def on_startup(self, app):
        print("Establish amqp connection and channel")
        self.connection = await aio_pika.connect_robust(self.amqp_config['url'])
        self.channel = await self.connection.channel()

    async def on_shutdown(self, app):
        print("Close amqp connection and channel")
        await self.channel.close()
        await self.connection.close()

    async def index(self, request):
        doc = {
            "previewgenerator request": {
                "description": "Download file and creates a preview image, report back to given webhook uri",
                "path": "/generatepreview",
                "method": "POST",
                "params": {
                    "download_uri": {
                        "type": "string",
                        "description": "Complete url to the downloadable file"
                    },
                    "signed_s3_uri": {
                        "type": "string",
                        "description": "Complete presigned url to upload the preview image"
                    },
                    "callback_uri": {
                        "type": "string",
                        "description": "Complete url to the callback uri"
                    },
                }
            }
        }
        return web.json_response(doc)

    @auth_required
    async def handle_generate_preview(self, request):
        body = await request.read()
        logging.info("Incoming request with body: {}".format(body))
        try:
            payload = json.loads(bytes(body).decode('utf-8'))
            assert 'download_url' in payload
            assert 'signed_s3_url' in payload
            assert 'callback_url' in payload

            await self.enqueue_generate_preview_request(body)
            return web.Response(status=202)

        except AssertionError as err:
            return web.Response(status=422, text='Unprocessable Entity: missing parameter ({})'.format(err))
        except Exception as e:
            return web.Response(status=500, text=str(e))

    async def enqueue_generate_preview_request(self, body):
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=body), routing_key=self.amqp_config['previewgenerator']['routing_key']
        )
