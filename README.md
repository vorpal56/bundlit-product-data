# Bundl.it Product Data
Used for CP340 Shopify website available at [https://bundl-it.myshopify.com/](https://bundl-it.myshopify.com/) until the end of Fall 2020.

### Running the code
```
git clone https://github.com/vorpal56/bundlit-product-data.git
python -m venv venv
./venv/Scripts/activate.bat
pip install -r requirements.txt
python src/main.py  # To run the main merging and transformation of data to Shopify
python src/product_recommendation.py  # To run the product recommendation system
deactivate 
```