import os, time, requests, base64, json
import logging
from config import opensearch_client, base_config

session = requests.Session()

def product_changed_event_handler(message: dict):
	content = message.get("message")
	print(f'ProductChangedEvent message: {content}')

	start_time = time.perf_counter()
	try:
		product_id = content.get("productId")

		# sending get request and saving the response as response object
		response = session.get(
			url = f'https://www.archiproducts.com/api/products/{product_id}',
			headers={'appkey':'A1E6B816-4661-46C9-B117-91955C8564E3', 'Accept-Encoding':'gzip, deflate', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'})
		logging.info(f'https://www.archiproducts.com/api/products/{product_id}, duration = {str(response.elapsed)}')
		
		# the product may not exists...
		if response.ok == False:
			logging.info(f"Product (id={product_id}) doesn't exist")
			pass

		# extracting data in json format
		data = response.json()
		im_url = data['Image']['Formats']['Large']

		# coverimage base64 encoding
		response = session.get(im_url, headers={'whoiam': 'edl-worker', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'})
		if response.ok == False:
			raise logging.error(f"Unable to download image ({im_url})")
		file = response.content
		im_text = base64.b64encode(file).decode('utf-8')

		# get embeddings with ML model
		response = session.post(
			url=	base_config.EMBEDDINGS_API_URL, 
			headers=json.loads(base_config.EMBEDDINGS_API_HEADERS),
			timeout=base_config.EMBEDDINGS_API_TIMEOUT,
			data=	'{"image": "'+im_text+'"}'
		)
		embeddings = response.json().get('embeddings')[0]
		logging.info(f'embedding genneration, duration = {str(response.elapsed)}')

	except requests.exceptions.ReadTimeout:
		raise logging.exception("Timeout generating embeddings from input image")
	
	except Exception as exc:
		raise logging.exception(str(exc))
	
	if response.ok == False or ():
		raise logging.error("Unable to generate embeddings from input image")


	try:
		doc = {
				'product_id' : data['Id'],
				'product_name': data['Name'],
				'product_shortdescription': data['ShortDescription'],
				'manufacturer_name': data['Manufacturer']['Name'],
				'cover_id': data['Image']['FileName'],
				'cover_name': os.path.basename(data['Image']['FileName']),
				'cover_embeddings': embeddings,
			}
		response = opensearch_client.index(
			index = base_config.INDEX_NAME,
			body = doc,
			id = data['Id'],
			refresh = True
		)

		duration = time.perf_counter() - start_time
		# print(f'Duration = {duration}')
		logging.info(f'Total Duration = {duration}')

	
	except Exception as exc:
		raise Exception(status_code=500, detail=str(exc))


