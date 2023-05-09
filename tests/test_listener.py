# pylint: disable=too-many-arguments
import asyncio
from dataclasses import asdict
from unittest.mock import ANY

import pytest

from route_builder.utils import Route, Error


REQUESTS = [
    {
        'points_coordinates': [[55.97999, 37.18581], [55.97863, 37.18954]],
        'with_map': True,
    },
    {
        'points_coordinates': [[55.97999, 37.18581], [55.97863, 37.18954]],
    }
]


@pytest.mark.parametrize('request_body', REQUESTS)
@pytest.mark.parametrize('builder_return_value', [Route([], 0, 0, None), Error('Одна ошибка и ты ошибся')])
async def test_listener(mocker, mock_geo, server, publisher, consumer, request_body, builder_return_value):
    """ Проверка rpc-модуля без гео-функциональности """
    route_builder_patcher = mocker.patch('route_builder.builders.build_route')
    route_builder_patcher.return_value = builder_return_value

    await publisher.publish(request_body)

    await asyncio.sleep(2)

    route_builder_patcher.assert_called_once_with(ANY, **request_body)

    consumer.process_message.assert_called_once_with(asdict(route_builder_patcher.return_value))


@pytest.mark.geo
@pytest.mark.parametrize('request_body', REQUESTS)
async def test_listener_with_builder(disable_osmnx_cache, disable_osmnx_logs,
                                     server, publisher, consumer, request_body):
    """ Проверка rpc-модуля с гео-функциональностью """
    await publisher.publish(request_body)

    await asyncio.sleep(5)

    consumer.process_message.assert_called_once()
    response_body = consumer.process_message.call_args[0][0]

    assert isinstance(response_body['paths'], list)
    assert isinstance(response_body['length'], float)
    assert isinstance(response_body['travel_time'], float)
    assert isinstance(response_body['map'], str) if 'with_map' in request_body else response_body['map'] is None
