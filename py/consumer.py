import asyncio
import logging
import aio_pika

from config import base_config, RABBIT_URL
from pika import message_router
from localizations import consumer

PARALLEL_TASKS = 2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("logs/consumer.log", mode="a"),
        logging.StreamHandler()
    ]
)


async def main() -> None:
	connection = await aio_pika.connect_robust(RABBIT_URL)

	queue_name = base_config.RABBITMQ_QUEUE

	async with connection:

		# creating channel
		channel = await connection.channel()
		await channel.set_qos(prefetch_count=PARALLEL_TASKS)

		# declaring queue
		queue = await channel.declare_queue(queue_name, auto_delete=True)

		# declaring exchange
		exchange = await channel.declare_exchange(
			name='Edil.Shared.Contracts.Events:ProductChangedEvent', 
			type=aio_pika.ExchangeType.FANOUT, 
			durable=True,
			auto_delete=False)

		# binding queue
		await queue.bind(exchange)

		logging.info(consumer.STARTED)

		await queue.consume(message_router)

		try:
			await asyncio.Future()
		finally:
			await connection.close()


if __name__ == "__main__":
    logging.info(consumer.STARTING)
    asyncio.run(main())
