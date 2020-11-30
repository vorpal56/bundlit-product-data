import re, os, pickle
from collections import OrderedDict
from random import sample
from csv import reader
from urllib.parse import urlparse
import numpy as np
import pandas as pd

data_folder = os.path.abspath("data")

def clean_description(data, price):
	substituted_price = re.sub(r'Rs\.\s?[0-9]+,?[0-9]+,?[0-9]+', "CAD ${:,.2f}".format(price), data, flags=re.IGNORECASE)
	substituted_website = re.sub(r'flipkart.com', "bundl.it", substituted_price, flags=re.IGNORECASE)
	substituted_region = re.sub(r'India', "Canada", substituted_website, flags=re.IGNORECASE)
	final = re.sub(r'\t', ' ', re.sub(r'\n', '', re.sub(r'"', '', substituted_region)))
	return final

def split_to_list(data):
	'''
	This removes products wrapped in quotes 
	for example parsing ""something"" will be returned as "something" and parsing "something" will be return as something
	This is not good as quotes need to be maintained for the representation of data in terms of product name and description
	'''
	return next(reader([data], delimiter=',', quotechar='"'))

def add_item_to_dict(dict_obj, key, value):
	if key not in dict_obj:
		dict_obj[key] = [value]
	else:
		parent_variants = dict_obj[key][0].get("variants") # how do we determine parent variant?
		local_variants = [variant_pair for variant_pair in parent_variants]

		if len(value.get("variants")) == len(parent_variants):
			is_valid_variants = [local_variants[i][0] == variant_pair[0] for i, variant_pair in enumerate(value.get("variants"))]
			if all(is_valid_variants):
				dict_obj[key].append(value)
			# else:
			# 	print("eq", value["id"], "has different variants than", dict_obj[key][0].get("id"))
		# else:
		# 	print("value has length {}, parent has length {}".format(len(value.get("variants")), len(parent_variants)))
	return

def categories_till_depth(data, depth=3):
	return data.split(' >> ')[:depth]

def exchange_to_cad(rs_val):
	return round(rs_val * 0.0176, 2) # google finance value on Nov 16, 6:00pm EST

products = pd.read_csv(os.path.join(data_folder, "flipkart_com-ecommerce_sample.csv"))
products = pd.read_csv(os.path.join(data_folder, "sample_10000.csv"))
products["description"] = products["description"].fillna("")
products["product_specifications"] = products["product_specifications"].fillna("")
products["brand"] = products["brand"].fillna("")
key_types = set()
valid_variant_keys = set(["color", "fit", "number of contents in sales package", "type", "size", "material", "pattern", "pack of", "model number", "model name", "model id"])
same_handles = OrderedDict()
nil = None
for i, (row_number, product) in enumerate(products.iterrows()):
	product_specification_str = product["product_specifications"].replace("=>", ":")
	retail_price = product["retail_price"]
	discounted_price = product["discounted_price"]
	images = eval(product["image"])
	brand = product["brand"]
	if product_specification_str != "" and images is not None and brand != "":
		product_specifications = eval(product_specification_str).get("product_specification")
		if product_specifications is not None:
			uid = product["uniq_id"]
			product_name = product["product_name"]
			sku = product["pid"]
			handle = urlparse(product["product_url"]).path.split("/")[1]
			category_tree = categories_till_depth(eval(product["product_category_tree"])[0])
			cad_retail_price = exchange_to_cad(retail_price)
			cad_discounted_price = exchange_to_cad(discounted_price)
			description = clean_description(product["description"], cad_retail_price)
			temp_product = {"id":uid, "name":product_name, "handle":handle, "categories":category_tree, "rp":cad_retail_price, "dp":cad_discounted_price, "image":images[0], "sku":sku, "description": description, "brand":brand}
			variant_options = {}
			model_details = {}
			for specification_obj in product_specifications:
				if type(specification_obj) != str:
					key = specification_obj.get("key")
					val = specification_obj.get("value")
					if key is not None:
						lower_key = key.lower()
						if lower_key != "none" and lower_key in valid_variant_keys:
							val = specification_obj.get("value")
							if lower_key == "model number" or lower_key == "model name" or lower_key == "model id":
								is_existing_model_detail = [val.lower() == model_value.lower() for model_value in model_details.values()]
								if is_existing_model_detail == [] or (is_existing_model_detail != [] and any(is_existing_model_detail) is False):
									model_details[key] = val
							elif len(variant_options) < 3:
								variant_options[key] = val
			temp_product["model_details"] = sorted(model_details.items(), key=lambda item: item[0])
			if len(variant_options) != 0:
				temp_product["variants"] = sorted(variant_options.items(), key= lambda item: item[0])
				add_item_to_dict(same_handles, handle, temp_product)

def write_pkl():
	product_samples = sample(same_handles.items(), 200)
	file = open(os.path.join(data_folder, "200_2.pkl"), "wb")
	pickle.dump(product_samples, file)
	file.close()
	return
def read_pkl():
	file = open(os.path.join(data_folder, "200_2.pkl"), "rb")
	product_samples = OrderedDict(pickle.load(file))
	file.close()
	return product_samples

def append_variants(l, product):
	for j, variant_pair in enumerate(product.get("variants")):
		l.append(variant_pair[0])
		l.append(variant_pair[1])
	for k in range(4 - j):
		l.append("")
		l.append("")
	return

def wrap_content(data):
	return '"' + data + '"'

def compile_list():
	product_samples = read_pkl()
	file_headers = "Handle,Title,Body (HTML),Vendor,Type,Tags,Published,Option1 Name,Option1 Value,Option2 Name,Option2 Value,Option3 Name,Option3 Value,Variant SKU,Variant Grams,Variant Inventory Tracker,Variant Inventory Qty,Variant Inventory Policy,Variant Fulfillment Service,Variant Price,Variant Compare At Price,Variant Requires Shipping,Variant Taxable,Variant Barcode,Image Src,Image Position,Image Alt Text,Gift Card,SEO Title,SEO Description,Google Shopping / Google Product Category,Google Shopping / Gender,Google Shopping / Age Group,Google Shopping / MPN,Google Shopping / AdWords Grouping,Google Shopping / AdWords Labels,Google Shopping / Condition,Google Shopping / Custom Product,Google Shopping / Custom Label 0,Google Shopping / Custom Label 1,Google Shopping / Custom Label 2,Google Shopping / Custom Label 3,Google Shopping / Custom Label 4,Variant Image,Variant Weight Unit,Variant Tax Code,Cost per item,Status\n"
	file = open(os.path.join(data_folder, "contents2.csv"), "w", encoding="utf-8")
	file.write(file_headers)
	for i, (handle, products) in enumerate(product_samples.items()):
		contents = [handle]
		# do the first item (which is the handle)
		for j, product in enumerate(products):
			contents = [handle]
			if j == 0:
				contents.append(wrap_content(product.get("name"))) # title
				contents.append(wrap_content(product.get("description"))) #body
				contents.append(wrap_content(product.get("brand"))) #vendor
				categories = product.get("categories") 
				contents.append(wrap_content(categories[0])) #type
				contents.append("") if len(categories) == 1 else contents.append(wrap_content(categories[0])) # tags
				contents.append("TRUE") #published
				# at most 3 variants
			else:
				for _ in range(6):
					contents.append("")

			for k, variant_pair in enumerate(product.get("variants"), start=1):
				contents.append(variant_pair[0])
				contents.append(wrap_content(variant_pair[1]))
			for _ in range(3 - k):
				contents.append("")
				contents.append("")
			contents.append("") if j == 0 else contents.append(product.get("sku")) # variant sku
			contents.append("100") #variant grams
			contents.append("shopify") #variant tracker
			contents.append("50") #qty
			contents.append("deny") #inv policy
			contents.append("manual") #fullment type
			contents.append(str(product.get("dp"))) # item price
			contents.append(str(product.get("rp"))) # compare at price
			contents.append("TRUE") # requires shipping
			contents.append("TRUE") # variant taxable
			contents.append("") # variant barcode
			contents.append(product.get("image")) # img alt
			contents.append("1") # image pos
			contents.append("") # image alt
			contents.append("FALSE") # gift card 
			for _ in range(16):
				contents.append("")

			contents.append("g") #variant weight type
			contents.append("")
			contents.append("")
			contents.append("active") #status
			content_str = ','.join(contents) + '\n'
			file.write(content_str)
	file.close()
def a():
	counts = 0
	for i, (handle, products) in enumerate(same_handles.items()):
		if len(products) >1 and counts <=10:
			counts +=1
			print(handle)
			print(products)
			print("--------------------")
if __name__ == "__main__":
	compile_list()
	# print(read_pkl())