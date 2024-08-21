from pydantic_settings import BaseSettings


class Base(BaseSettings):
    RABBITMQ_LOCAL_HOST_NAME: str = 'rabbit'
    RABBITMQ_LOCAL_PORT: int = 5672
    RABBITMQ_DEFAULT_USER: str = 'guest'
    RABBITMQ_DEFAULT_PASS: str = 'guest'
    RABBITMQ_QUEUE: str = 'test_queue'
    
    OPENSEARCH_HOST: str = 'localhost'
    OPENSEARCH_PORT: int = 9200
    OPENSEARCH_USER: str = 'admin'
    OPENSEARCH_PASSWORD: str = 'admin'
    
    INDEX_NAME: str = "embeddings-openclip-b-32"
    
    EMBEDDINGS_API_CLIP_URL: str = "http://localhost:7860/clip-embed"
    EMBEDDINGS_API_E5_URL: str = "http://localhost:7860/e5-embed"
    EMBEDDINGS_API_HEADERS: str = "{}"
    EMBEDDINGS_API_TIMEOUT: float = 5.0
    



    CLIENT_ORIGIN: str = 'http://localhost:3000'
    
	


base_config = Base()

RABBIT_URL = f'amqp://{base_config.RABBITMQ_DEFAULT_USER}:' \
             f'{base_config.RABBITMQ_DEFAULT_PASS}@' \
             f'{base_config.RABBITMQ_LOCAL_HOST_NAME}:' \
             f'{base_config.RABBITMQ_LOCAL_PORT}/'
