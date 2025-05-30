# "images" submodule, e.g. import routers.images

from fastapi import APIRouter, File, Form, Body, Query, UploadFile, HTTPException
from pydantic import BaseModel, Field
from config import rabbit_connection, opensearch_client, base_config
import requests, json, base64
from typing import Annotated
from urllib.request import *
import torch
from PIL import Image
from io import BytesIO
# from torchvision import transforms
# from transformers import AutoModelForImageSegmentation
from ben2 import BEN_Base
import time
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu') 

# rmbgmodel = AutoModelForImageSegmentation.from_pretrained('briaai/RMBG-2.0', trust_remote_code=True)
# # torch.set_float32_matmul_precision(['high', 'highest'][0])
# rbgmodel.to(device)
# rmbgmodel.eval()
# # Data settings
# image_size = (512, 512)
# transform_image = transforms.Compose([
#     transforms.Resize(image_size),
#     transforms.ToTensor(),
#     transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
# ])

# ben2
ben2model = BEN_Base.from_pretrained("PramaLLC/BEN2")
ben2model.to(device).eval()

# birefnet = AutoModelForImageSegmentation.from_pretrained('ZhengPeng7/BiRefNet', trust_remote_code=True)
# torch.set_float32_matmul_precision(['high', 'highest'][0])
# birefnet.to(device)
# birefnet.eval()
# birefnet.half()
# # # Data settings
# image_size = (1024, 1024)
# transform_image = transforms.Compose([
#     transforms.Resize(image_size),
#     transforms.ToTensor(),
#     transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
# ])

# InSPyReNet
# from transparent_background import Remover
# remover = Remover(mode='fast', jit=False, device=device)

# rembg
# from rembg import remove, new_session

visualsearch_router = APIRouter(tags=['Visual search routes'])


class Output(BaseModel):
	product_id: int
	product_name: str
	product_shortdescription:str
	cover_name:str
	score: float = Field(None, alias="_score")


@visualsearch_router.get("/")
def index():
    return {"message": "Make a get request to '/similar_products' or a post to /reverse_search to search through products"}


@visualsearch_router.get('/similar_products', response_model=list[Output])
def find_similar_products_by_id(
	product_id:	Annotated[int,	Query(description="The product_id to search for similarity")] = None, 
	image_id:	Annotated[str,	Query(description="The image_id to search for similarity")] = "",
	from_:	 	Annotated[int,	Query(description="Starting document offset. Needs to be non-negative and defaults to 0.", alias="from", min=0)] = 0,
	size: 		Annotated[int,	Query(description="Defines the number of hits to return. Defaults to 25.", max=100)] = 25,
	min_score:	Annotated[float,Query(description="Minimum _score for matching documents: documents with a lower _score are not included in the search results", max=1)] = 0):
	"""
	### Search visually similar products given a product_id or image_id.
	Finds the most visually similar products to the query product.
	To achive this we need to compute dense representations (embeddings) of the given images and then use the cosine similarity metric to determine how similar the two images are.
	### Args:
	* **product_id** (int): the product_id to search for similarity.
	* **image_id** (string): the image_id to search for similarity.
	* **from** (int): starting document offset. Needs to be non-negative and defaults to 0.
	* **size** (int): number of results to returns.
	### Returns:
	(List[Product]): list of product data
	"""

	# lookup pregenerated embeddings by product_id or image_id
	lookup_reponse = opensearch_client.search(
		index= base_config.INDEX_NAME,
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
		index= base_config.INDEX_NAME,
		body= {
			"from": from_,
			"size": size,
			"min_score": min_score,
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
		_source= ["product_id", "manufacturer_name", "product_name", "product_shortdescription", "cover_name"]	
	)

	return [{**item["_source"], **{'_score':item["_score"]}} for item in search_response['hits']['hits']]


@visualsearch_router.post('/reverse_search', response_model=list[Output])
def find_similiar_products_by_image(
	file:		Annotated[bytes,File(description="An attached binary file that will be used for similarity search")] = None,
	url:		Annotated[str,	Form(description="The Url an image that will be used for similarity search")] = None, 
	from_:	 	Annotated[int,	Form(description="Starting document offset. Needs to be non-negative and defaults to 0.", alias="from", min=0)] = 0,
	size: 		Annotated[int,	Form(description="Defines the number of hits to return. Defaults to 25.", max=100)] = 25,
	min_score:	Annotated[float,Form(description="Minimum _score for matching documents: documents with a lower _score are not included in the search results", max=1)] = 0):
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

	image = Image.open(BytesIO(file)).convert("RGB")
	# image.thumbnail((2048,2048), Image.Resampling.LANCZOS)

	# briaai/RMBG-2.0
	# input_images = transform_image(image).unsqueeze(0)#.to(device)
	# # Prediction
	# with torch.no_grad():
	# 	preds = rbgmodel(input_images)[-1].sigmoid()#.cpu()
	# pred = preds[0].squeeze()
	# pred_pil = transforms.ToPILImage()(pred)
	# mask = pred_pil.resize(image.size)
	# image.putalpha(mask)
	# new_image = Image.new("RGBA", image.size, "WHITE") # Create a white rgba background
	# new_image.paste(image, (0, 0), image)
	# new_image = new_image.convert('RGB')

	# ben2
	foreground = ben2model.inference(image, refine_foreground=False,)
	new_image = Image.new("RGBA", image.size, "WHITE") # Create a white rgba background
	new_image.paste(foreground, (0, 0), foreground)
	new_image = new_image.convert('RGB')
	# new_image.save('output.jpg')

	# birefnet
	# input_images = transform_image(image).unsqueeze(0).to(device).half()
	# # Prediction
	# with torch.no_grad():
	# 	preds = birefnet(input_images)[-1].sigmoid().cpu()
	# pred = preds[0].squeeze()
	# pred_pil = transforms.ToPILImage()(pred)
	# mask = pred_pil.resize(image.size)
	# image.putalpha(mask)
	# new_image = Image.new("RGBA", image.size, "WHITE") # Create a white rgba background
	# new_image.paste(image, (0, 0), image)
	# new_image.convert('RGB').save('output.jpg')

	# InSPyReNet
	# foreground = remover.process(image)
	# new_image = Image.new("RGBA", image.size, "WHITE") # Create a white rgba background
	# new_image.paste(foreground, (0, 0), foreground)
	# new_image.convert('RGB').save('output.jpg')

	# rembg
	# new_image = remove(image, 
	# 				session=new_session('birefnet-general'), 
	# 				bgcolor=(255, 255, 255, 255))
	# new_image.convert('RGB').save('output.jpg')

	buffered = BytesIO()
	new_image.convert("RGB").save(buffered, format="JPEG")

	# encode the image
	im_text = base64.b64encode(buffered.getvalue()).decode('utf-8')

	try:
		response = requests.post(
			url=	base_config.EMBEDDINGS_API_IMAGE_URL, 
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
			index= base_config.INDEX2_NAME,
			body= {
				"from": from_,
				"size": size,
				"min_score": min_score,
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
			_source= ["product_id", "manufacturer_name", "product_name", "product_shortdescription", "cover_name"]	
		)

		return [{**item["_source"], **{'_score':item["_score"]}} for item in search_response['hits']['hits']]

	except Exception as exc:
		raise HTTPException(status_code=503, detail=str(exc))


@visualsearch_router.post('/hybrid_search', response_model=list[Output])
def find_products_by_hybrid_search(
	query:		Annotated[str,	Body(description="Query of the image to search")] = None, 
	from_:	 	Annotated[int,	Body(description="Starting document offset. Needs to be non-negative and defaults to 0.", alias="from", min=0)] = 0,
	size: 		Annotated[int,	Body(description="Defines the number of hits to return. Defaults to 25.", max=100)] = 25,
	# min_score:	Annotated[float,Form(description="Minimum _score for matching documents: documents with a lower _score are not included in the search results", max=1)] = 0
	):
	"""
	### Hybrid Search with a given query.
	Combines semantic search into textual fields and text-to-image search of product's CoverImage.
	If the exact product doesn’t appear, very similar ones pop up.
	### Args:
	* **query** (string): a search phrase to search for.
	* **from** (int): starting document offset. Needs to be non-negative and defaults to 0.
	* **size** (int): number of results to returns.
	### Returns:
	(List[Product]): list of product data
	"""
	if not query:
		raise HTTPException(status_code=400, detail="the parameter 'query' is mandatory")

	try:
		im_response = requests.post(
			url=	base_config.EMBEDDINGS_API_CLIP_URL, 
			headers=json.loads(base_config.EMBEDDINGS_API_HEADERS),
			timeout=base_config.EMBEDDINGS_API_TIMEOUT,
			data=	'{"text": "'+query+'"}'
		)
		# response = requests.post(url= URL, headers= headers, data= json.dumps({"text":"sofa"}), files = {"form_field_name": file})
		txt_response = requests.post(
			url=	base_config.EMBEDDINGS_API_E5_URL, 
			headers=json.loads(base_config.EMBEDDINGS_API_HEADERS),
			timeout=base_config.EMBEDDINGS_API_TIMEOUT,
			data=	'{"text": "query: '+query+'"}'
		)

	except requests.exceptions.ReadTimeout:
		raise HTTPException(status_code=408, detail="Timeout generating embeddings from input image")
	
	except Exception as exc:
		raise HTTPException(status_code=500, detail=str(exc))
	
	if im_response.ok == False or ():
		raise HTTPException(status_code=500, detail="Unable to generate embeddings from input image")
	if txt_response.ok == False or ():
		raise HTTPException(status_code=500, detail="Unable to generate embeddings from input text")


	try:
		clip_vector = json.loads(im_response.text).get('embeddings')[0]
		e5_vector = json.loads(txt_response.text).get('embeddings')[0]

		search_response = opensearch_client.search(
			index= base_config.INDEX_NAME,
			body= {
				"from": from_,
				"size": size,
				# "min_score": min_score,
				"query":{
					"bool":{
						"should" : [
							{
							"knn": {
								"cover_embeddings":{
									"k": 500,
									"vector": clip_vector,
									"boost": 1.5
								}
							}}
							,
							{
							"knn": {
								"text_embeddings":{
									"k": 500,
									"vector": e5_vector,
									"boost": 1.0
								}
							}},
							{
							"term" : {
								"product_name": {
									"value":query,
									"boost": 0.1
								} 
							}}
							,
							{
							"term" : {
								"manufacturer_name": {
									"value":query,
									"boost": 0.1
								} 
							}}
						] 
					}
				}	
			},
			_source= ["product_id", "manufacturer_name", "product_name", "product_shortdescription", "cover_name"]	
		)

		return [{**item["_source"], **{'_score':item["_score"]}} for item in search_response['hits']['hits']]

	except Exception as exc:
		raise HTTPException(status_code=503, detail=str(exc))

