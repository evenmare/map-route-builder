import logging
import asyncio
import json
from dataclasses import asdict

import aio_pika

import settings
from route_builder import builders


logger = logging.getLogger(__name__)


async def run(graph) -> None:
    """
    Запуск rpc-модуля
    :param graph: используемый для построения маршрутов граф
    :return: None
    """
    connection = await aio_pika.connect_robust(settings.RMQ_URL)

    # Creating channel
    channel = await connection.channel()

    # Maximum message count which will be processing at the same time.
    await channel.set_qos(prefetch_count=settings.RMQ_PREFETCH_COUNT)

    # Declaring queue
    queue = await channel.declare_queue(settings.RMQ_QUEUE, auto_delete=True)

    async def publish(routing_key: str, correlation_id: str, data: dict):
        await channel.default_exchange.publish(aio_pika.Message(
            body=json.dumps(data).encode(),
            correlation_id=correlation_id,
        ), routing_key=routing_key)
        logger.info("============== MESSAGE %s REPLIED ==============", correlation_id)

    async def process_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process():
            logger.info("============== MESSAGE %s RECEIVED ==============", message.correlation_id)
            request_data = json.loads(message.body)
            response_data = asdict(builders.build_route(graph, **request_data))
            await publish(message.reply_to, message.correlation_id, response_data)

    await queue.consume(process_message)

    try:
        # Wait until terminate
        await asyncio.Future()
    finally:
        await connection.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)

    if not settings.APP_NAME:
        raise ValueError('APP_NAME: value required')

    _graph = builders.Graph(settings.BBOX, settings.NETWORK_TYPE)
    _graph.build()

    asyncio.run(run(_graph))
