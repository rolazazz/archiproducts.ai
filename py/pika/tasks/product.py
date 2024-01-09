import requests, base64, json
from config import base_config


def product_changed_event_handler(message: dict):
	content = message.get("message")
	print(f'ProductChangedEvent message: {content}')


	product_id = content.get("productId")

	try:
		# sending get request and saving the response as response object
		response = requests.get(
			url = f'https://www.archiproducts.com/api/products/{product_id}',
			headers={'appkey' : 'A1E6B816-4661-46C9-B117-91955C8564E3'})
		
		# extracting data in json format
		data = response.json()
		im_url = data['Image']['Formats']['Medium']
		request = requests.get(im_url)
		file = request.content
		im_text = base64.b64encode(file).decode('utf-8')

	except Exception:
		pass

	try:
		response = requests.post(
			url=	base_config.EMBEDDINGS_API_URL, 
			headers=json.loads(base_config.EMBEDDINGS_API_HEADERS),
			timeout=base_config.EMBEDDINGS_API_TIMEOUT,
			data=	'{"image": "'+im_text+'"}'
		)

		embeddings = json.loads(response.text).get('embeddings')[0]

		print(embeddings)

		# response = requests.post(url= URL, headers= headers, data= json.dumps({"text":"sofa"}), files = {"form_field_name": file})
	except requests.exceptions.ReadTimeout:
		raise Exception(status_code=408, detail="Timeout generating embeddings from input image")
	
	except Exception as exc:
		raise Exception(status_code=500, detail=str(exc))
	
	if response.ok == False or ():
		raise Exception(status_code=500, detail="Unable to generate embeddings from input image")


		


