import json
import logging
import asyncio
from aio_pika.abc import AbstractIncomingMessage

from .tasks import test_task, product_changed_event_handler

fieldsToWatch = set(['Name','ShortDescription','CoverImage','Attributes','Materials','Styles','Features','Designers'])

async def message_router(
        message: AbstractIncomingMessage,
) -> None:
    async with message.process():
        body = json.loads(message.body.decode())
        
        if body.get('type') == 'test_message':
            return test_task(body)
        
        if 'urn:message:Edil.Shared.Contracts.Events:ProductChangedEvent' in body.get('messageType') \
        	and set(body['message']['updatedFields']).intersection(fieldsToWatch):
            # return product_changed_event_handler(body)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, product_changed_event_handler, body)
        # return logging.info('Not recognized task type')


__all__ = ['message_router']
