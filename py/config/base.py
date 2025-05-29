from pydantic_settings import BaseSettings


class Base(BaseSettings):
    RABBITMQ_LOCAL_HOST_NAME: str = '192.168.1.224'
    RABBITMQ_LOCAL_PORT: int = 5672
    RABBITMQ_DEFAULT_USER: str = 'guest'
    RABBITMQ_DEFAULT_PASS: str = 'guest'
    RABBITMQ_QUEUE: str = 'test_queue'
    
    OPENSEARCH_HOST: str = 'localhost'
    OPENSEARCH_PORT: int = 9200
    OPENSEARCH_USER: str = 'admin'
    OPENSEARCH_PASSWORD: str = 'admin'
    
    INDEX_NAME: str = "openclip-b-32-xlm-roberta-base-multilingual-e5-large"
    INDEX2_NAME: str = "timm-vit_base_patch16_384"
    
    EMBEDDINGS_API_CLIP_URL: str = "http://localhost:7860/clip-embed"
    EMBEDDINGS_API_SENTENCE_URL: str = "http://localhost:7860/sentence-embed"
    EMBEDDINGS_API_IMAGE_URL: str = "http://localhost:7860/image-embed"
    EMBEDDINGS_API_HEADERS: str = "{}"
    EMBEDDINGS_API_TIMEOUT: float = 10
    



    CLIENT_ORIGIN: str = 'http://localhost:3000'
    
	


base_config = Base()

RABBIT_URL = f'amqp://{base_config.RABBITMQ_DEFAULT_USER}:' \
             f'{base_config.RABBITMQ_DEFAULT_PASS}@' \
             f'{base_config.RABBITMQ_LOCAL_HOST_NAME}:' \
             f'{base_config.RABBITMQ_LOCAL_PORT}/'
