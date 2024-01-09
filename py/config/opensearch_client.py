from opensearchpy import OpenSearch, SSLError 
from .base import base_config


opensearch_client = OpenSearch(
						hosts=base_config.OPENSEARCH_HOST,
						http_auth=(base_config.OPENSEARCH_USER, base_config.OPENSEARCH_PASSWORD),
						use_ssl = True,
						verify_certs= False,
						ssl_assert_hostname = False,
						ssl_show_warn = False,
						http_compress = False, # enables gzip compression for request bodies
					)