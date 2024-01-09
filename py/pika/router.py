import json
import logging

from aio_pika.abc import AbstractIncomingMessage

from .tasks import test_task, product_changed_event_handler


async def message_router(
        message: AbstractIncomingMessage,
) -> None:
    async with message.process():
        body = json.loads(message.body.decode())
        if body.get('type') == 'test_message':
            return test_task(body)
        if 'urn:message:Edil.Shared.Contracts.Events:ProductChangedEvent' in body.get('messageType'):
            return product_changed_event_handler(body)
        return logging.info('Not recognized task type')


__all__ = ['message_router']
