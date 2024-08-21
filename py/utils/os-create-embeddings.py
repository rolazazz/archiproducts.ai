import sys, os, time, json, pathlib, argparse
import open_clip, torch
from sentence_transformers import SentenceTransformer
from PIL import Image
from tqdm import tqdm
from opensearchpy import SSLError
from opensearchpy.helpers import parallel_bulk

sys.path.insert(0, str(pathlib.Path(os.path.dirname(__file__)).parent))
from config import opensearch_client, base_config


PATH_TO_IMAGES = "C:\\AppData\\product-images\\"
REBUILD_INDEX = True
CHUNK_SIZE = 100

parser = argparse.ArgumentParser()
parser.add_argument('--dest_index', dest='dest_index', required=False, default=base_config.INDEX_NAME,
                    help="OpenSearch destination index. Default: " + base_config.INDEX_NAME)
args = parser.parse_args()


def main():
	global args
	lst = []
	DEST_INDEX = args.dest_index

	start_time = time.perf_counter()
	device = "cuda" if torch.cuda.is_available() else "cpu"

	clipmodel, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k', device=device)
	# clipmodel, _, preprocess = open_clip.create_model_and_transforms('ViT-L-14', pretrained='laion2b_s32b_b82k', device=device)
	tokenizer = open_clip.get_tokenizer('ViT-B-32')

	st_model = SentenceTransformer('intfloat/multilingual-e5-large', device=device)

	duration = time.perf_counter() - start_time
	print(f'Duration load model = {duration}')

	with open('./py/utils/catalog-product-all.json',  encoding="utf8") as user_file:
		parsed_json = json.load(user_file)[:1000]

	#for row in tqdm(parsed_json, desc='Processing json', total=len(parsed_json)):
	for row in tqdm(parsed_json, desc='Processing json', total=len(parsed_json)):
		try:
				
			filename = f"{row['CoverImage']['FileName']}"
			filepath = f"{PATH_TO_IMAGES}b_{filename}"
			image = Image.open(filepath)
			embeddings = clip_image_embedding(image, preprocess, clipmodel, device).tolist()
			text = f"passage: {row['Name']['Value']['en']} {row['Categories'][0]['NameSingular']['en']} ({', '.join([x['NameSingular']['en'] for x in row['Attributes']])}), produced by {row['Manufacturer']['Name']}{', design by ' if row['Designers'] else ''}{' '.join([x['Name'] for x in row['Designers']])}"
			doc = {
				'_id': row['_id'],
				'product_id' : row['_id'],
				'product_name': row['Name']['Value']['en'],
				'product_shortdescription': row['ShortDescription']['Value']['en'],
				'manufacturer_name': row['Manufacturer']['Name'],
				'cover_id': filename,
				'cover_name': filename,
				'cover_embeddings': embeddings,
				# 'relative_path': os.path.relpath(filepath).split(PREFIX)[1],
				# 'images': [image_map(x) for x in row['Images']],
                'text_embeddings': st_model.encode(text, convert_to_tensor=True, device=device).tolist()
			}
			lst.append(doc)
			
		except Exception as e:
			print ("Unexpected Error")
			raise 

	duration = time.perf_counter() - start_time
	print(f'Duration creating image embeddings = {duration}')



	try:
		with open("./py/utils/os-index-mappings.json", "r") as config_file:
			config = json.loads(config_file.read())

			if REBUILD_INDEX:
				if opensearch_client.indices.exists(index=DEST_INDEX):
					print("Deleting existing %s" % DEST_INDEX)
					opensearch_client.indices.delete(index=DEST_INDEX, ignore=[400, 404])

				print("Creating index %s" % DEST_INDEX)
				index_body = {
					"settings": config["settings"],
					"mappings": config["mappings"],
				}
				response = opensearch_client.indices.create(
					index=DEST_INDEX,
					# mappings=config["mappings"],
					# settings=config["settings"],
					body=index_body,
					ignore=[400, 404],
					request_timeout=120)


		count = 0
		for success, info in parallel_bulk(
				client=opensearch_client,
				actions=lst,
				thread_count=2,
				chunk_size=CHUNK_SIZE,
				timeout=120,
				index=DEST_INDEX
		):
			if success:
				count += 1
				if count % CHUNK_SIZE == 0:
					print('Indexed %s documents' % str(count), flush=True)
					sys.stdout.flush()
			else:
				print('Doc failed', info)

		print('Indexed %s documents' % str(count), flush=True)
		duration = time.perf_counter() - start_time
		print(f'Total duration = {duration}')
		print("Done!\n")
	except SSLError as e:
		if "SSL: CERTIFICATE_VERIFY_FAILED" in e.message:
			print("\nCERTIFICATE_VERIFY_FAILED exception. Please check the CA path configuration for the script.\n")
			raise
		else:
			raise
	except Exception as e:
		raise



def clip_image_embedding(image, preprocess, model, device):
    pre = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        image_features = model.encode_image(pre)[0]
    return image_features




if __name__ == '__main__':
    main()