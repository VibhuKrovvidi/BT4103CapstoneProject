import os
import tqdm
import requests
import zipfile

from __future__ import division
from sklearn.cluster import KMeans
from numbers import Number
from pandas import DataFrame
import sys, codecs, numpy

URL = "http://nlp.stanford.edu/data/glove.6B.zip"

def fetch_data(url=URL, target_file='glove.zip', delete_zip=False):
    #if the dataset already exists exit
    if os.path.isfile(target_file):
        print("datasets already downloded :) ")
        return

    #download (large) zip file
    #for large https request on stream mode to avoid out of memory issues
    #see : http://masnun.com/2016/09/18/python-using-the-requests-module-to-download-large-files-efficiently.html
    print("**************************")
    print("  Downloading zip file")
    print("  >_<  Please wait >_< ")
    print("**************************")
    response = requests.get(url, stream=True)
    #read chunk by chunk
    handle = open(target_file, "wb")
    for chunk in tqdm.tqdm(response.iter_content(chunk_size=512)):
        if chunk:  
            handle.write(chunk)
    handle.close()  
    print("  Download completed ;) :") 
    #extract zip_file
    zf = zipfile.ZipFile(target_file)
    print("1. Extracting {} file".format(target_file))
    zf.extractall()
    if delete_zip:
        print("2. Deleting {} file".format(dataset_name+".zip"))
        os.remove(path=zip_file)

fetch_data()

# glove_file = "glove.42B.300d.txt"
# import tqdm

# EMBEDDING_VECTOR_LENGTH = 50 # <=200
# def construct_embedding_matrix(glove_file, word_index):
#     embedding_dict = {}
#     with open(glove_file,'r') as f:
#         for line in f:
#             values=line.split()
#             # get the word
#             word=values[0]
#             if word in word_index.keys():
#                 # get the vector
#                 vector = np.asarray(values[1:], 'float32')
#                 embedding_dict[word] = vector
#     ###  oov words (out of vacabulary words) will be mapped to 0 vectors

#     num_words=len(word_index)+1
#     #initialize it to 0
#     embedding_matrix=np.zeros((num_words, EMBEDDING_VECTOR_LENGTH))

#     for word,i in tqdm.tqdm(word_index.items()):
#         if i < num_words:
#             vect=embedding_dict.get(word, [])
#             if len(vect)>0:
#                 embedding_matrix[i] = vect[:EMBEDDING_VECTOR_LENGTH]
#     return embedding_matrix
  
# embedding_matrix =  construct_embedding_matrix(glove_file, tokenizer.tokenizer.word_index)











# # load the whole embedding into memory
# embeddings_index = dict()
# f = open('../input/glove6b/glove.twitter.27B.txt')

# for line in f:
#     values = line.split()
#     word = values[0]
#     coefs = np.asarray(values[1:], dtype='float32')
#     embeddings_index[word] = coefs

# f.close()
# print('Loaded %s word vectors.' % len(embeddings_index))
