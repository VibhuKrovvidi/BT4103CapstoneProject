import json
from keras.preprocessing.text import text_to_word_sequence
from statistics import mean, median, mode

with open('C:/Users/TzeMin/Documents/capstone/BT4103CapstoneProject/Scraping/smsCorpus_en_20150309_all.json') as f:
    corpus = json.load(f)

    users = set()
    texts = []
    for text in corpus['smsCorpus']['message']:
        users.add(text['source']['userProfile']['userID']['$'])
        texts.append(text_to_word_sequence(str(text['text']['$'])))
    
    texts = texts[:1000]
    lengths = [len(text) for text in texts]
    sequence_length = mode(lengths)

    print("Number of Users:", len(users))
    print("Number of Texts:", len(corpus['smsCorpus']['message']))
    print("Sequence Length: ", sequence_length)
    print(texts)