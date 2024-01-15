import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from config import base_config, rabbit_connection
import uvicorn
from dotenv import load_dotenv

load_dotenv()


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("logs/fastapi.log", mode="a"),
        logging.StreamHandler()
    ]
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await rabbit_connection.connect()
    yield
    await rabbit_connection.disconnect()


api = FastAPI(
      		lifespan=lifespan,
            title="Product Similarity API",
			description="""
				Product Similarity API helps you do search for similar product by product_id or image file. 🚀

				You will be able to:
                        
                * **Finds the most visually similar products** to the query product.

				* **Reverse Image Search** with a given image.
            	A reverse image search is the use of a photo to search online without text.
                If the exact product doesn’t appear, very similar ones pop up.
            """,
			summary="We can use machine learning to return meaningful similar images, text, or audio in the proper context. Simple, and fast!",
			version="0.0.1",
			terms_of_service="http://www.archiproducts.com/terms/",
			# contact={
			# 	"name": "Deadpoolio the Amazing",
			# 	"url": "http://x-force.example.com/contact/",
			# 	"email": "dp@x-force.example.com",
			# },
			license_info={
				"name": "Apache 2.0",
				"url": "https://www.apache.org/licenses/LICENSE-2.0.html",
			},
	)

# app.include_router(router, prefix='/api/v1')
api.include_router(router)

api.add_middleware(
    CORSMiddleware,
    allow_origins=[base_config.CLIENT_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
	uvicorn.run("main:api", host='127.0.0.1', port=8000, reload=True)