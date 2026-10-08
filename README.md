# NovaCart — DSA Product Search Website

A full-stack Flask + SQLite website based on the original ProductSearchSystem C++ project.

## New features
- 100 additional demo products (107 total including the original 7)
- SQLite persistent database
- Add / Edit / Delete products
- Trie prefix/name search
- Exact Product ID search
- Merge Sort low-to-high and high-to-low pricing
- Category filtering
- Wishlist stored in SQLite
- Personalized recommendation system based on wishlist categories and ratings
- Animated, colorful responsive GUI
- Shop / Wishlist / For You navigation

## Run
```bat
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000

If you already have an older `products.db`, the application uses `INSERT OR IGNORE`, so the 100 new products will be added without deleting your existing products.
