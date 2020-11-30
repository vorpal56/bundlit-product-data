import os
import numpy as np
import pandas as pd
import pickle
from sklearn.feature_extraction.text  import TfidfVectorizer
from sklearn.metrics.pairwise import sigmoid_kernel

pd.set_option('display.max_colwidth', 140)
data_folder = os.path.abspath("data")
products = pd.read_csv(os.path.join(data_folder, "flipkart_com-ecommerce_sample.csv"))

def product_recommendation(title):
	tfidf_v = TfidfVectorizer(
		max_features=None,
		strip_accents="unicode",
		analyzer="word",
		min_df=10,
		token_pattern=r"\w{1,}",
		ngram_range=(1,3),#take the combination of 1-3 different kind of words
		stop_words="english"
	)
	products["description"] = products["description"].fillna("")
	products["product_name"] = products["product_name"].str.lower()
	tfidf_matrix = tfidf_v.fit_transform(products["description"])
	sig = sigmoid_kernel(tfidf_matrix, tfidf_matrix)
	indices = pd.Series(products.index, index=products["product_name"]).drop_duplicates()
	index = indices.get(title.lower())
	if index is not None:
		sorted_sig_scores = list(enumerate(sig[index]))
		sorted_sig_scores = sorted(sorted_sig_scores, key=lambda item: item[1], reverse=True)
		top_10_products = [sorted_sig_scores[i][0] for i in range(0, 11)]
		return products["product_name"].iloc[top_10_products].unique()
	return [index]

if __name__ == "__main__":
	print(product_recommendation("Style Foot Bellies"))