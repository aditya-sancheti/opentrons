import aiohttp
import json
import logging
import traceback

from aiohttp import web
from opentrons.server import serialize

log = logging.getLogger(__name__)

# Keep these in sync with ES code
CALL_RESULT_MESSAGE = 0
CALL_ACK_MESSAGE = 1
NOTIFICATION_MESSAGE = 2
CONTROL_MESSAGE = 3

class Server(object):
    def __init__(self, root=None, host='127.0.0.1', port=31950):
        self.objects = { id(self): self }
        self.root = root
        self.host = host
        self.port = port

    def start(self):
        app = web.Application()
        app.router.add_get('/', self.handler)
        web.run_app(app, host=self.host, port=self.port)

    def update_refs(self, refs):
        self.objects.update(refs)

    def resolve_args(self, args):
        def resolve(a):
            if isinstance(a, dict) and a['$meta'] and a['$meta']['that']:
                return self.objects[a['$meta']['that']]
            return a

        return [resolve(a) for a in args]

    def get_root(self):
        return self.root

    async def dispatch(self, that, name, args):
        if not that in self.objects:
            raise ValueError('dispatch: object with id {0} not found'.format(that))

        obj = self.objects[that]
        function = getattr(type(obj), name)

        log.debug('dispatch: will call {0}.{1}({2})'
            .format(obj, name, ', '.join([str(a) for a in args])))

        if not function:
            raise ValueError(
                'Function {0} not found in {1}'.format(name, type(obj)))

        if not callable(function):
            raise ValueError(
                'Attribute {0} of {1} is not a function'.format(name, type(obj)))

        res = function(obj, *self.resolve_args(args))
        self.objects[id(res)] = res

        return res

    def update_meta(self, obj, meta):
        if '$meta' not in obj:
            obj['$meta'] = {}
        obj['$meta'].update(meta)
        return obj

    async def process(self, message, send):
        if message.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(message.data)

            # Acknowledge the call
            await send(self.update_meta({}, {
                    'id': data['id'],
                    'type': CALL_ACK_MESSAGE 
                }))

            meta = { 'id': data.pop('id'), 'type': CALL_RESULT_MESSAGE }
            try:
                res = await self.dispatch(**data)
                meta.update({'status': 'success'})
            except Exception as e:
                log.warning('Exception while dispatching a method call: {0}'.format(traceback.format_exc()))
                res = str(e)
                meta.update({'status': 'error'})
            finally:
                root, refs = serialize.get_object_tree(res)
                self.update_refs(refs)
                await send(self.update_meta(root, meta))

        elif message.type == aiohttp.WSMsgType.ERROR:
            log.error(
                'WebSocket connection closed with exception %s' % ws.exception())

    async def handler(self, request):
        log.debug('Starting handler for request: {0}'.format(request))
        ws = web.WebSocketResponse()

        await ws.prepare(request)

        def send(payload):
            log.debug('Sending {0} to {1}: '.format(payload, ws))
            return ws.send_str(json.dumps(payload))

        # Our first message is address of Server instance
        root, _ = serialize.get_object_tree(self, shallow=True)
        root = self.update_meta(root, {'type': CONTROL_MESSAGE})
        await send(root)

        async for msg in ws:
            log.debug('Received: {0}'.format(msg))
            try:
                await self.process(msg, send)
            except Exception as e:
                ws.close()
                log.error('Exception while processing message: {0}'.format(traceback.format_exc()))

        return ws
