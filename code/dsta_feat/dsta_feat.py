import pandas as pd
import numpy as np
import nltk
import regex
import re
from tqdm import tqdm
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem.wordnet import WordNetLemmatizer 
from sklearn.feature_extraction.text import TfidfVectorizer
import stanza
stanza.download('en') # download English model
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

class DSTA_Feature():
	def __init__(self):
		self.nlp = stanza.Pipeline('en')

	def feature_extraction(self, txt):
		# Convert para into sentences
	    sentList = nltk.sent_tokenize(txt)

	    retlist = [];
	    # For each sentence
	    for line in sentList:
	        # Tag and word tokenize
	        txt_list = nltk.word_tokenize(line)
	        taggedList = nltk.pos_tag(txt_list)
	        
	        newwordList = []
	        # Merge possible consecutive features ("Phone Battery" ==> "PhoneBattery")
	        flag = 0
	        for i in range(0,len(taggedList)-1):
	            if(taggedList[i][1]=="NN" and taggedList[i+1][1]=="NN"):
	                newwordList.append(taggedList[i][0]+taggedList[i+1][0])
	                flag=1
	            else:
	                if(flag==1):
	                    flag=0
	                    continue
	                newwordList.append(taggedList[i][0])
	                if(i==len(taggedList)-2):
	                    newwordList.append(taggedList[i+1][0])
	        finaltxt = ' '.join(word for word in newwordList)
	    
	    	# Remove stop words and tag
	        stop_words = set(stopwords.words('english'))
	        new_txt_list = nltk.word_tokenize(finaltxt)
	        wordsList = [w for w in new_txt_list if not w in stop_words]
	        taggedList = nltk.pos_tag(wordsList)
	        
	        # Use dependancy analysis to parse and extract features + descriptors
	        doc = self.nlp(finaltxt)
	        dep_node = []
	        try:
	            for dep_edge in doc.sentences[0].dependencies:
	                dep_node.append([dep_edge[2].text, dep_edge[0].id, dep_edge[1]])
	            for i in range(0, len(dep_node)):
	                if (int(dep_node[i][1]) != 0):
	                    dep_node[i][1] = newwordList[(int(dep_node[i][1]) - 1)]
	        except:
	            pass;
	        
	        # Final features + descriptors
	        featureList = []
	        categories = []
	        for i in taggedList:
	            if(i[1]=='JJ' or i[1]=='NN' or i[1]=='JJR' or i[1]=='NNS' or i[1]=='RB'):
	                featureList.append(list(i))
	                categories.append(i[0])
	        
	        fcluster = []
	        for i in featureList:
	            filist = []
	            for j in dep_node:
	                if((j[0]==i[0] or j[1]==i[0]) and (j[2] in [
	                    # Different types of words that are identified as potential features
	                    "nsubj",
	                    #"acl:relcl",
	                    "obj",
	                    "dobj",
	                    #"agent",
	                    #"advmod",
	                    #"amod",
	                    #"neg",
	                    #"prep_of",
	                    #"acomp",
	                    #"xcomp",
	                    #"compound"
	                ])):
	                    if(j[0]==i[0]):
	                        filist.append(j[1])
	                    else:
	                        filist.append(j[0])
	            fcluster.append([i[0], filist])
	        print(fcluster) 
	        
	        retlist.append(fcluster)
	    return retlist;

    def do_extraction(self, df, feat_count, feat_sent, content_str = "Content"):
	    idx = 0;
	    # Replace "" with nan's for removal
	    df[content_str].replace('', np.nan, inplace=True)
	    df.dropna(subset=[content_str], inplace=True)
	    
	    review_list = df[content_str].to_list()
	     
	    print(" Processing : " , df.shape[0], "rows of data")
	    for review in tqdm(review_list):
	        print("Review Number : ", idx);
	        
	        # Some data pre-processing
	        
	        review = review.lower()
	        
	        # Merge hyphenated words
	        separate = review.split('-')
	        review = ''.join(separate)
	        
	        # Remove non-alphabets
	        review = re.sub(r'[^a-z\s\t]', '', review)
	        
	        idx += 1;
	        if idx >= df.shape[0]:
	            break;
	        try:
	            output = self.feature_extraction(review);
	        except:
	            pass;
	        for sent in output:
	            for pair in sent:
	                print(pair)
	                if pair[0] in feat_sent:
	                    if pair[1] is not None:
	                        flist = feat_sent[pair[0]]
	                        if isinstance(pair[1], list):
	                            for i in pair[1]:
	                                flist.append(i)
	                        else:
	                            flist.append(pair[1])
	                        feat_sent[pair[0]] = flist;
	                else:
	                    if pair[1] is not None:
	                        flist = pair[1]
	                    else:
	                        flist = list()
	                    feat_sent[pair[0]] = flist;
	                
	                if pair[0] in feat_count:
	                    feat_count[pair[0]] = feat_count[pair[0]] + 1;
	                else:
	                    feat_count[pair[0]] = 1
	    
	    return feat_count, feat_sent;
    

    def get_sentiment(feat_count, feat_sent, nlp):

	    sentiment_score = dict()
	    singlish = pd.read_csv("")
	    # Delete features with no descriptors
	    cob = feat_sent.copy()
	    for feat in cob.keys():
	        #print(cob[feat])
	        
	        if cob[feat] == []:
	            del feat_sent[feat]
	        else:
	            feat_sent[feat] = ' ,'.join(feat_sent[feat])

	    # Define a new df to track at descriptor level
	    dcolumns = ["Feature", "Descriptor", "Sentiment", "Freq of Feature"]
	    desc_df = pd.DataFrame(columns=dcolumns)
	    
	    # Run pre-built sentiment score and take avg of all descriptors
	    for f in tqdm(feat_sent.keys()):
	        print("Calculating Sentiment for: ", f);
	        print(feat_sent[f].split(" ,"))
	        ssum = 0;
	        for g in feat_sent[f].split(" ,"):

	            try:
	                doc = nlp(g);

	                for i in doc.sentences:

	                        #print(i.sentiment)
	                        ssum += i.sentiment;
	                        new_row = [[f, g, i.sentiment, feat_count[f]]]
	                        desc_df = desc_df.append(pd.DataFrame(new_row, columns=dcolumns))
	            except:
	                pass;

	        sentiment_score[f] = ssum / len(b[f])

	    adf = pd.DataFrame.from_dict(feat_count, orient='index', columns=['Freq'])
	    adf.sort_values(by="Freq", ascending=False, inplace = True)

	    

	    avg_sent = pd.DataFrame.from_dict(sentiment_score, orient='index', columns=["Avg_sent"])
	    desc_words = pd.DataFrame.from_dict(feat_sent, orient="index", columns=["Descriptors"])
	    
	    avg_sent = avg_sent.merge(desc_words, left_index=True, right_index=True)
	    
	    
	    final_sent = avg_sent.merge(adf, left_index=True, right_index=True)
	    final_sent.sort_values(by="Freq", ascending=False, inplace=True)
	    return final_sent, desc_df;

    def run_feat_extraction(self):

