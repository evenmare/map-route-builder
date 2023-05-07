from typing import Optional, Literal
import json

import aio_pika


class BaseQueueWorker:
    """ Базовая функциональность воркера для очереди """
    # TODO: create exchange differs from default
    connection_method_name: Literal['connect', 'connect_robust'] = 'connect_robust'

    connection: Optional[aio_pika.abc.AbstractConnection]
    channel: Optional[aio_pika.abc.AbstractChannel]
    exchange: Optional[aio_pika.abc.AbstractExchange]

    def __init__(self, connection_url: str, routing_key: str, robust: Optional[bool] = True) -> None:
        """
        :param connection_url:
        :param routing_key:
        :param robust:
        """
        self.connection_url = connection_url
        self.routing_key = routing_key

        if not robust:
            self.connection_method_name = 'connect'

    async def create_connection(self) -> None:
        """
        Создание подключения, канала и инициализация обменника
        :return: None
        """
        self.connection = await getattr(aio_pika, self.connection_method_name)(self.connection_url)

        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)

        self.exchange = self.channel.default_exchange

    async def close(self) -> None:
        """
        Закрытие подключения
        :return: None
        """
        if self.channel:
            await self.channel.close()

        if self.connection:
            await self.connection.close()


class Publisher(BaseQueueWorker):
    """ Издатель """
    def __init__(self, *args, reply_to: str = None, **kwargs):
        """
        :param reply_to: routing key для ответа
        :param args: значения неименованных параметров
        :param kwargs: значения именованных параметров
        """
        super().__init__(*args, **kwargs)
        self.reply_to = reply_to

    async def publish(self, payload: dict):
        """
        Публикация
        :param payload: тело сообщения
        :return: None
        """
        await self.exchange.publish(
            aio_pika.Message(body=json.dumps(payload).encode(),
                             reply_to=self.reply_to,
                             correlation_id=self.reply_to),
            routing_key=self.routing_key,
        )


class Consumer(BaseQueueWorker):
    """ Подписчик """
    @staticmethod
    async def process_message(response_body: dict):
        """
        Обработка тела сообщения
        :param response_body: тело сообщения
        :return: None
        """

    async def _process_message(self, message: aio_pika.abc.AbstractIncomingMessage):
        """
        Обработка сообщения
        :param message: сообщение
        :return: None
        """
        async with message.process():
            await self.process_message(json.loads(message.body))

    async def consume(self):
        """
        Подписка на очередь
        :return: None
        """
        queue = await self.channel.declare_queue(self.routing_key, auto_delete=True)
        await queue.consume(self._process_message)
