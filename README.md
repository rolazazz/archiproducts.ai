## What is visual product search?
AI visual search is a technology that enables users to retrieve information by utilizing images instead of queries based on text. Instead of typing in keywords, users can input images or use pictures taken with their devices (such as smartphones or cameras) to initiate a search.

The visual search system then analyzes the image’s visual characteristics and returns relevant results based on the content or objects depicted in the image. AI visual search technology relies on advanced image recognition and machine learning techniques to understand the content of the images and match them with relevant items, products, or information from a database.

![](https://miro.medium.com/v2/resize:fit:720/format:webp/1*FwaIWPF8sOfXJWKh70PXoQ.png)
*Image Similarity result based on Deep Learning, source: https://ioannotator.com/image-similarity-search*


## How does visual product search work?
AI visual search operates through a sophisticated interplay of image analysis, computer vision algorithms, and machine learning. Here’s a breakdown of how the process unfolds:

![](https://d3lkc3n5th01x7.cloudfront.net/wp-content/uploads/2023/10/19034457/visual-product-search.png)

**Image analysis**: The process of visual product search starts with the analysis of the uploaded image. Computer vision algorithms dissect the image to identify and extract features encompassing colors, textures, shapes, and patterns. These features are crucial for understanding the visual content of the image.

**Feature extraction**: Computer vision algorithms pinpoint key points, objects, and colors within the image. This involves breaking down the image into components that can be quantified and compared, enabling the system to understand its visual characteristics.

**Comparison to catalog**: The extracted features are compared against an extensive database or catalog of images, which typically contains product images, item attributes, labels, and descriptions. The search engine endeavors to find matching items in the catalog that share similar visual attributes with the input image.

**Machine learning**: Visual product search is underpinned by machine learning algorithms. As the system processes more images and learns from each interaction, it refines its ability to recognize patterns and relationships between images. This iterative learning process enhances the system’s accuracy and precision over time.

**Search results**: The system generates a set of search results based on the comparison. These results are usually displayed to the user as product thumbnails accompanied by relevant metadata such as labels, tags, or descriptions. Users can then explore the visually matched products.


## Prominent examples of AI visual search engines
Here are some prominent AI visual search engines that have gained traction in recent years:

**Google Lens**: Google Lens, Google’s AI visual search technology, debuted in 2017. It started as an exclusive feature for Google Pixel smartphones but later became available as an app for all Android devices. Google Lens is now integrated into Google’s core search tools. It identifies similar images and can also recognize objects within the image to refine its results. Additionally, it employs language, words, and metadata from the images’ host websites to deliver relevant outcomes. Google Lens isn’t limited to finding products; it can also translate text, identify animals, and explore various subjects.

**Bing Visual Search**: Bing Visual Search, introduced by Microsoft in 2009 and re-launched in 2018, serves as an alternative to Google Lens. It can compare products, identify landmarks, and pinpoint image sources using reverse image search and other visual search techniques. Additionally, it assists photographers and artists in identifying instances of their original work being copied and uploaded.

**Pinterest Lens**: Pinterest Lens emerged in 2017, catering to users on the popular social media platform. It empowers users to discover analogous products and fresh ideas through images. While Google Lens and Bing Visual Search extend beyond their respective platforms, Pinterest Lens is restricted to images within Pinterest. Over time, Pinterest Lens has introduced features like the Shop tab, leading users to shoppable pins. It’s a preferred choice for finding home decor inspiration, fashion ideas, and recipes.


## How do we define similarity?
To build this system, we first need to define how we want to compute the similarity between two images. One widely popular practice is to compute dense representations (`embeddings`) of the given images and then use the cosine similarity metric to determine how similar the two images are.

 *Embeddings* represent images in `vector space`. This gives us a nice way to meaningfully compress the high-dimensional pixel space of images (224 x 224 x 3, for example) to something much lower dimensional (768, for example). The primary advantage of doing this is the reduced computation time in the subsequent steps.

![](https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/blog/image_similarity/embeddings.png)


## Computing embeddings
To compute the embeddings from the images, we'll use a vision model that has some understanding of how to represent the input images in the vector space. This type of model is also commonly referred to as image encoder.

### CLIP
[**CLIP**](https://openai.com/research/clip) (Contrastive Language-Image Pre-training) is a method created by OpenAI for training models capable of aligning image and text representations. Images and text are drastically different modalities, but CLIP manages to map both to a shared space, allowing for all kinds of neat tricks.


## Vector search algorithms
The simple way to find similar vectors is to use k-nearest neighbors (`k-NN`) algorithms, which compute the distance between a query vector and the other vectors in the vector database.

### Approximate k-NN
An approximate nearest neighbor approach uses one of several algorithms to return the approximate k-nearest neighbors to a query vector. Usually, these algorithms sacrifice indexing speed and search accuracy in return for performance benefits such as lower latency, smaller memory footprints, and more scalable search. Approximate k-NN is the best choice for searches over large indexes (that is, hundreds of thousands of vectors or more) that require low latency. You should not use approximate k-NN if you want to apply a filter on the index before the k-NN search, which greatly reduces the number of vectors to be searched. In this case, you should use either the score script method or painless extensions.


### Vector similarity metrics
All search engines use a similarity metric to rank and sort results and bring the most relevant results to the top. When you use a plain text query, the similarity metric is called TF-IDF, which measures the importance of the terms in the query and generates a score based  n the number of textual matches. When your query includes a vector, the similarity metrics are spatial in nature, taking advantage of proximity in the vector space. `Vector databases` supports several similarity or distance measures:
* **Euclidean distance** – The straight-line distance between points.
* **Cosine similarity** – The cosine of the angle between two vectors in a vector space.
* **Inner product** – The product of the magnitudes of two vectors and the cosine of the angle between them. Usually used for natural language processing (NLP) vector similarity.



## Requirements
### Python environment
**Python v3.9+**

Make sure, you can access and use Python.

## How to
Before starting using similarity search on your images, you must set up an OpenSearch/ElasticSearch cluster with data (indices) and NLP models.

By Data, I mean Elasticsearch index (or more), which contains a document per image with its image embeddings. The image embeddings is the vector describing the image features generated by CLIP model. 

### 0. Setup Python Virtual Evironment (.venv)
We must set up a Python environment to use scripts for the api.
A virtual environment, a self-contained directory tree that contains a Python installation for a particular version of Python, plus a number of additional packages. 
```bash
$ git clone https://github.com/rolazazz/archiproducts-ai
$ cd archiproducts-ai
$ cd py
$ python -m venv .venv
$ ./.venv/bin/activate
$ pip install -r requirements.txt
```
### 1. OpenSearch cluster
You can use the docker-compose bundled in the repository, your cluster, or the OpenSearch cloud service by Amazon AWS. To run the OpenSearch cluster locally, use the following docker-compose example.



## Run the API locally
Make sure that Python environment is set and all requirements are installed as described above and that you are in the main project folder.
```bash
$ cd py
$ python main.py
```



## How to run Archiproducts AI API in Docker 
To run the application in a Docker container, we need to build it and then run the Docker image with the OpenCLIP/FastAPI application.
```bash
$ # just make sure you are in the py project directory 
$ cd archiproducts-ai/py
````

### Build the image
In order to be able to run the application in the Docker environment, we need to build the image locally. Because this 
is a Python application with dependencies, the build of the image might take longer. All the requirements are installed.   
```bash
$ docker build . --tag archiproducts-ai:0.0.1 --tag archiproducts-ai:latest
```
Once, the build is complete, we can verify if the image is available.
```bash
$ docker images | grep archiproducts-ai
```

### Run the image
To run the application, we need to run the Docker image. 
```bash
$ docker run -d -p 8000:8000 --name archiproducts-ai archiproducts-ai:latest
```

## Run with Docker-Compose
You can use the docker-compose bundled in the repository to run:
- an OpenSearch Service cluster locally with a persistent volume attached to each node
- a instance of OpenCLIP API to infear on new images
- a virtual network

Use the following docker-compose example.

```bash
$ cd archiproducts-ai
$ docker-compose build app
$ docker-compose up -d
```

## How To





https://github.com/kieled/fastapi-aiopika-boilerplate