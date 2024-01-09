# "images" submodule, e.g. import routers.images

from fastapi import APIRouter, File, Form, Body, Query, UploadFile, HTTPException
from pydantic import BaseModel
from config import rabbit_connection, opensearch_client, base_config
import requests, json, base64
from typing import Annotated
from urllib.request import *


visualsearch_router = APIRouter(tags=['Visual search routes'])


class Output(BaseModel):
	product_id: int
	product_name: str
	product_shortdescription:str


@visualsearch_router.get("/")
def index():
    return {"message": "Make a get request to '/similar_products' or a post to /reverse_search to search through products"}


@visualsearch_router.get('/similar_products', response_model=list[Output])
async def find_similar_products_by_id(
	product_id:	Annotated[int,	Query(description="The product_id to search for similarity")] = None, 
	image_id:	Annotated[str,	Query(description="The image_id to search for similarity")] = "",
	size: 		Annotated[int,	Query(description="The number of results to return", max=100)] = 10):
	"""
	### Search visually similar products given a product_id or image_id.
	Finds the most visually similar products to the query product.
	To achive this we need to compute dense representations (embeddings) of the given images and then use the cosine similarity metric to determine how similar the two images are.
	### Args:
	* **url** (string): Url of an image to use for similarity search.
	* **file** (File): File attachment used for similarity search.
	* **size** (int): number of results to returns.
	### Returns:
	(List[Product]): list of product data
	"""

	# lookup pregenerated embeddings by product_id or image_id
	lookup_reponse = opensearch_client.search(
		index= "embeddings-openclip-b-32",
		body= {
			"size": 1,
			"query":{
				"bool":{
					"should":[
						{"term": {
							"product_id": {
								"value": product_id,
							}
						}},
						{"term": {
							"cover_id": {
								"value": image_id,
							}
						}}
					],
					"minimum_should_match": 1
				}			
			}
		},
		_source= ["product_id", "cover_id", "cover_name", "cover_embeddings"]	
	)

	# if exists than search for similar images	
	results = lookup_reponse['hits']['hits']
	if len(results)==0:
		raise HTTPException(status_code=404, detail="the reference Product cannot be found")

	embeddings = results[0]['_source']['cover_embeddings']
	product_id = results[0]['_source']['product_id']

	search_response = opensearch_client.search(
		index= "embeddings-openclip-b-32",
		body= {
			"size": size,
			"query":{
				"bool":{
					"must": [
						{"knn": {
							"cover_embeddings":{
								"k": 50,
								"vector": embeddings
							}
						}}
					],
					"must_not": [
						{"term":{
							"product_id": {
								"value": product_id
							}
						}}
					]
				}
			}	
		},
		_source= ["product_id", "manufacturer_name", "product_name", "product_shortdescription"]	
	)

	return [item["_source"] for item in search_response['hits']['hits']]



@visualsearch_router.post('/reverse_search', response_model=list[Output])
async def find_similiar_products_by_image(
	file:	Annotated[bytes,File(description="An attached binary file that will be used for similarity search")] = None,
	url:	Annotated[str,	Form(description="The Url an image that will be used for similarity search")] = None, 
	size: 	Annotated[int,	Form(description="The number of results to return", max=100)] = 10):
	"""
	### Reverse Image Search with a given image.
	A reverse image search is the use of a photo to search online without text.
	If the exact product doesn’t appear, very similar ones pop up.
	### Args:
	* **url** (string): Url of an image to use for similarity search.
	* **file** (File): File attachment used for similarity search.
	* **size** (int): number of results to returns.
	### Returns:
	(List[Product]): list of product data
	"""
	if not url and not file:
		raise HTTPException(status_code=400, detail="Unable to find an image to process: pass at least the parameter 'url' or attach a 'file' in multipart/form-data ")

	# if there's a valid url, download as file
	if url:
		try:
			request = requests.get(url)
			file = request.content
		except:
			raise HTTPException(status_code=400, detail=f"Unable to download file from given url '{url}'")
	
	# else use attached file

	im_text = base64.b64encode(file).decode('utf-8')

	try:
		response = requests.post(
			url=	base_config.EMBEDDINGS_API_URL, 
			headers=json.loads(base_config.EMBEDDINGS_API_HEADERS),
			timeout=base_config.EMBEDDINGS_API_TIMEOUT,
			data=	'{"image": "'+im_text+'"}'
		)
		# response = requests.post(url= URL, headers= headers, data= json.dumps({"text":"sofa"}), files = {"form_field_name": file})
	except requests.exceptions.ReadTimeout:
		raise HTTPException(status_code=408, detail="Timeout generating embeddings from input image")
	
	except Exception as exc:
		raise HTTPException(status_code=500, detail=str(exc))
	
	if response.ok == False or ():
		raise HTTPException(status_code=500, detail="Unable to generate embeddings from input image")


	try:
		embeddings = json.loads(response.text).get('embeddings')[0]

		search_response = opensearch_client.search(
			index= "embeddings-openclip-b-32",
			body= {
				"size": size,
				"query":{
					"bool":{
						"must": [
							{"knn": {
								"cover_embeddings":{
									"k": 50,
									"vector": embeddings
								}
							}}
						]
					}
				}	
			},
			_source= ["product_id", "manufacturer_name", "product_name", "product_shortdescription"]	
		)

		return [item["_source"] for item in search_response['hits']['hits']]

	except Exception as exc:
		raise HTTPException(status_code=503, detail=str(exc))

