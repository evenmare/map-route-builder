from dotenv import load_dotenv
from envparse import env

from route_builder.utils import Bbox

load_dotenv()


DEBUG = env.bool('DEBUG', default=False)
USE_CACHE = env.bool('USE_CACHE', default=True)

APP_NAME = env.str('APP_NAME', default='rpc-route-route_builder')

RMQ_HOST = env.str('RMQ_HOST', default='localhost')
RMQ_PORT = env.int('RMQ_PORT', default=5672)
RMQ_PREFETCH_COUNT = env.int('RMQ_PREFETCH_COUNT', default=10)

RMQ_USER = env.str('RMQ_USER', default='guest')
RMQ_PASSWORD = env.str('RMQ_PASSWORD', default='guest')
RMQ_QUEUE = env.str('RMQ_QUEUE', default=f'{APP_NAME}:cmd')
RMQ_URL_QUERY_PARAMS = env.str('RMQ_URL_QUERY_PARAMS', default='')
RMQ_URL = f"amqp://{RMQ_USER}:{RMQ_PASSWORD}@{RMQ_HOST}:{RMQ_PORT}/?{RMQ_URL_QUERY_PARAMS}"

CPU_LIMITER = env.int('CPU_LIMITER', default=None)
NETWORK_TYPE = env.str('NETWORK_TYPE')

BBOX = Bbox(env.float('BBOX_NORTH'), env.float('BBOX_SOUTH'),
            env.float('BBOX_EAST'), env.float('BBOX_WEST'))
