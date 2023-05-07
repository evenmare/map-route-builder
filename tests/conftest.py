import asyncio
import threading

from unittest.mock import AsyncMock
import pytest

import settings
from listener.__main__ import run
from tests.utils import Publisher, Consumer
from route_builder import utils, builders


TEST_BBOX = utils.Bbox(55.98323, 55.97630, 37.19288, 37.18280)
REPLY_RMQ_QUERY = f'{settings.APP_NAME}:test_reply'


@pytest.fixture()
def disable_osmnx_cache(mocker):
    """ Отключение кеша osmnx """
    mocker.patch('osmnx.settings.use_cache', False)
    yield


@pytest.fixture()
def disable_osmnx_logs(mocker):
    """ Отключение логов osmnx """
    mocker.patch('osmnx.settings.log_console', False)
    yield


def _setup_loop(loop):
    """ Настройка asyncio.loop """
    asyncio.set_event_loop(loop)
    loop.run_forever()


@pytest.fixture()
def server():
    """ Запуск listener'a. Создается единоразово на все тесты """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

        thread = threading.Thread(target=_setup_loop, args=(loop, ), daemon=True)
        thread.start()

        graph = builders.Graph(TEST_BBOX, 'drive')
        graph.build()

        asyncio.run_coroutine_threadsafe(run(graph), loop)

    yield


@pytest.fixture()
def mock_geo(mocker):
    """ Мок гео-функциональности """
    graph_builder_patcher = mocker.patch('route_builder.builders.Graph.build')
    graph_builder_patcher.return_value = None

    yield


@pytest.fixture()
async def publisher():
    """ Запуск издателя """
    _publisher = Publisher(settings.RMQ_URL, settings.RMQ_QUEUE, reply_to=REPLY_RMQ_QUERY)
    await _publisher.create_connection()

    yield _publisher

    await _publisher.close()


@pytest.fixture()
async def consumer():
    """ Запуск """
    _consumer = Consumer(settings.RMQ_URL, REPLY_RMQ_QUERY)
    await _consumer.create_connection()
    await _consumer.consume()

    _consumer.process_message = AsyncMock(return_value=None)

    yield _consumer

    await _consumer.close()
