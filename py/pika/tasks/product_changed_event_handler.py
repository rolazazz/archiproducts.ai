import opensearchpy
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
			headers={'appkey':'584F5FD3-D76A-44B7-AB7E-01D4B8A1B8B7', 'Accept-Encoding':'gzip, deflate', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'})
		logging.info(f'https://www.archiproducts.com/api/products/{product_id}, duration = {str(response.elapsed)}')
		
		
		if response.ok == False:

			# if the product is offline remove it from the index
			# if doc doesn't exist, it will raise a not found exception
			response = opensearch_client.delete(
				index = base_config.INDEX_NAME,
				id = product_id
			)
			logging.info(f"Product (id={product_id}) is offline or doesn't exist")
			
		else:

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
				url=	base_config.EMBEDDINGS_API_CLIP_URL, 
				headers=json.loads(base_config.EMBEDDINGS_API_HEADERS),
				timeout=base_config.EMBEDDINGS_API_TIMEOUT,
				json=	{'image': im_text}
			)
			if response.ok == False or ():
				raise logging.error("Unable to generate embeddings from input image")
			im_embeddings = response.json().get('embeddings')[0]

			text = f"passage: {data['Name']} {data['ShortDescription']} ({', '.join([x['Name'] for x in data['Features']+data['Materials']+data['Styles'] ])}), produced by {data['Manufacturer']['Name']}{', design by ' if data['Designers'] else ''}{' '.join([x['Name'] for x in data['Designers']])}"
			response = session.post(
				url=	base_config.EMBEDDINGS_API_SENTENCE_URL_URL, 
				headers=json.loads(base_config.EMBEDDINGS_API_HEADERS),
				timeout=base_config.EMBEDDINGS_API_TIMEOUT,
				json=	{"text": text}
			)
			if response.ok == False or ():
				raise logging.error("Unable to generate embeddings from text")
			tx_embeddings = response.json().get('embeddings')[0]

			logging.info(f'embedding genneration, duration = {str(response.elapsed)}')


			doc = {
				'product_id' : data['Id'],
				'product_name': data['Name'],
				'product_shortdescription': data['ShortDescription'],
				'manufacturer_name': data['Manufacturer']['Name'],
				'cover_id': data['Image']['FileName'],
				'cover_name': os.path.basename(data['Image']['FileName']),
				'cover_embeddings': im_embeddings,
				'text_embeddings': tx_embeddings
			}
			response = opensearch_client.index(
				index = base_config.INDEX_NAME,
				body = doc,
				id = data['Id'],
				refresh = True
			)


			# get embeddings with ML model
			response = session.post(
				url=	base_config.EMBEDDINGS_API_IMAGE_URL, 
				headers=json.loads(base_config.EMBEDDINGS_API_HEADERS),
				timeout=base_config.EMBEDDINGS_API_TIMEOUT,
				json=	{'image': im_text}
			)
			if response.ok == False or ():
				raise logging.error("Unable to generate embeddings from input image")
			im_embeddings = response.json().get('embeddings')[0]

			doc = {
				'product_id' : data['Id'],
				'product_name': data['Name'],
				'product_shortdescription': data['ShortDescription'],
				'manufacturer_name': data['Manufacturer']['Name'],
				'cover_id': data['Image']['FileName'],
				'cover_name': os.path.basename(data['Image']['FileName']),
				'cover_embeddings': im_embeddings
			}
			response = opensearch_client.index(
				index = base_config.INDEX2_NAME,
				body = doc,
				id = data['Id'],
				refresh = True
			)



	except opensearchpy.exceptions.NotFoundError:
		pass

	except requests.exceptions.ReadTimeout:
		raise logging.exception("Timeout generating embeddings from input image")
	
	except Exception as exc:
		raise logging.exception(str(exc))
	
	



	duration = time.perf_counter() - start_time
	# print(f'Duration = {duration}')
	logging.info(f'Total Duration = {duration}')
