import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
try:
    from surprise import SVD, Dataset, Reader
    from surprise.model_selection import train_test_split
    SURPRISE_AVAILABLE = True
except ImportError:
    SURPRISE_AVAILABLE = False

def train_content_based(recipes):
    if not recipes:
        return None, None
    tfidf = TfidfVectorizer(stop_words='english')
    recipe_texts = []
    for r in recipes:
        ingredients_list = json.loads(r.get('ingredients', '[]')) if isinstance(r.get('ingredients'), str) else r.get('ingredients', [])
        text = f"{r['title']} {' '.join(ingredients_list)}"
        recipe_texts.append(text)
    try:
        tfidf_matrix = tfidf.fit_transform(recipe_texts)
        return tfidf, tfidf_matrix
    except Exception as e:
        print(f"Error training content-based model: {e}")
        return None, None

def recommend_content_based(tfidf, tfidf_matrix, ingredients, recipes):
    if not recipes or not ingredients or tfidf is None or tfidf_matrix is None:
        return recipes[:5] if recipes else []
    try:
        user_input = ' '.join(ingredients)
        user_vector = tfidf.transform([user_input])
        similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()
        if similarities.size == 0 or np.any(np.isnan(similarities)):
            return recipes[:5] if recipes else []
        ranked_indices = similarities.argsort()[::-1]
        return [recipes[i] for i in ranked_indices[:5]]
    except Exception as e:
        print(f"Error in content-based recommendation: {e}")
        return recipes[:5] if recipes else []

def train_collaborative_filtering(ratings_data):
    if not SURPRISE_AVAILABLE or not ratings_data:
        print("Surprise unavailable or no ratings; skipping collaborative filtering training")
        return None
    try:
        df = pd.DataFrame(ratings_data, columns=['user_id', 'recipe_id', 'rating'])
        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(df, reader)
        trainset, _ = train_test_split(data, test_size=0.2)
        model = SVD()
        model.fit(trainset)
        return model
    except Exception as e:
        print(f"Error training collaborative model: {e}")
        return None

def recommend_collaborative(model, user_id, recipes):
    if not SURPRISE_AVAILABLE or not recipes or model is None:
        print("Collaborative filtering unavailable; returning input recipes")
        return recipes[:5] if recipes else []
    try:
        predictions = []
        for recipe in recipes:
            pred = model.predict(user_id, recipe['id']).est
            predictions.append((recipe, pred))
        predictions.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in predictions[:5]]
    except Exception as e:
        print(f"Error in collaborative recommendation: {e}")
        return recipes[:5] if recipes else []