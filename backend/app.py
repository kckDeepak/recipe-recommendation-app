from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import mysql.connector
from mysql.connector import Error
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()
# Attempt to import surprise, with fallback
try:
    from surprise import SVD, Dataset, Reader
    from surprise.model_selection import train_test_split
    SURPRISE_AVAILABLE = True
except ImportError as e:
    print(f"Failed to import surprise: {e}. Falling back to content-based filtering only.")
    SURPRISE_AVAILABLE = False

from db_config import db_config

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

API_KEY = os.getenv("SPOONACULAR_API_KEY")
if not API_KEY:
    raise ValueError("SPOONACULAR_API_KEY not found in .env file")

# MySQL connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Initialize TF-IDF vectorizer
tfidf = TfidfVectorizer(stop_words='english')

# Cache recipes in MySQL
def cache_recipes(recipes):
    connection = get_db_connection()
    if not connection:
        return
    cursor = connection.cursor()
    for recipe in recipes:
        try:
            used_ingredients = [ing['name'] for ing in recipe.get('usedIngredients', [])]
            missed_ingredients = [ing['name'] for ing in recipe.get('missedIngredients', [])]
            all_ingredients = used_ingredients + missed_ingredients
            nutritional_data = json.dumps(recipe.get('nutrition', {}))[:16777215]  # Truncate to MEDIUMTEXT limit
            cursor.execute("""
                INSERT INTO recipes (id, title, instructions, nutritional_data, ingredients)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE title=%s, instructions=%s, nutritional_data=%s, ingredients=%s
            """, (recipe['id'], recipe['title'], recipe.get('instructions', ''),
                  nutritional_data, json.dumps(all_ingredients),
                  recipe['title'], recipe.get('instructions', ''),
                  nutritional_data, json.dumps(all_ingredients)))
            connection.commit()
        except Error as e:
            print(f"Error caching recipe: {e}")
    cursor.close()
    connection.close()

# Fetch recipes from Spoonacular API
def fetch_recipes(ingredients, diet=None):
    try:
        url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={','.join(ingredients)}&number=10&apiKey={API_KEY}"
        if diet:
            url += f"&diet={diet}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            recipes = response.json()
            for recipe in recipes:
                try:
                    details_url = f"https://api.spoonacular.com/recipes/{recipe['id']}/information?apiKey={API_KEY}"
                    nutrition_url = f"https://api.spoonacular.com/recipes/{recipe['id']}/nutritionWidget.json?apiKey={API_KEY}"
                    details_response = requests.get(details_url, timeout=5)
                    nutrition_response = requests.get(nutrition_url, timeout=5)
                    if details_response.status_code == 200:
                        recipe['instructions'] = details_response.json().get('instructions', '') or 'No instructions available'
                    if nutrition_response.status_code == 200:
                        recipe['nutrition'] = nutrition_response.json()
                    else:
                        recipe['nutrition'] = {}
                except requests.RequestException as e:
                    print(f"Error fetching details for recipe {recipe['id']}: {e}")
                    recipe['instructions'] = 'No instructions available'
                    recipe['nutrition'] = {}
            cache_recipes(recipes)
            return recipes
        else:
            print(f"API error: {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"Error fetching recipes: {e}")
        return []

# Content-based filtering using TF-IDF
def content_based_filtering(ingredients, recipes):
    if not recipes or not ingredients:
        return []
    recipe_texts = []
    for r in recipes:
        ingredients_list = json.loads(r.get('ingredients', '[]')) if isinstance(r.get('ingredients'), str) else r.get('ingredients', [])
        text = f"{r['title']} {' '.join(ingredients_list)}"
        recipe_texts.append(text)
    try:
        tfidf_matrix = tfidf.fit_transform(recipe_texts)
        user_input = ' '.join(ingredients)
        user_vector = tfidf.transform([user_input])
        similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()
        if similarities.size == 0 or np.any(np.isnan(similarities)):
            return recipes[:5] if recipes else []
        ranked_indices = similarities.argsort()[::-1]
        return [recipes[i] for i in ranked_indices[:5]]
    except Exception as e:
        print(f"Error in content-based filtering: {e}")
        return recipes[:5] if recipes else []

# Collaborative filtering using Surprise (if available)
def collaborative_filtering(user_id, recipes):
    if not SURPRISE_AVAILABLE or not recipes:
        print("Collaborative filtering unavailable or no recipes; returning input recipes")
        return recipes[:5] if recipes else []
    connection = get_db_connection()
    if not connection:
        return recipes[:5] if recipes else []
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT user_id, recipe_id, rating FROM ratings")
        ratings_data = cursor.fetchall()
        if not ratings_data:
            return recipes[:5] if recipes else []
        df = pd.DataFrame(ratings_data, columns=['user_id', 'recipe_id', 'rating'])
        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(df, reader)
        trainset, _ = train_test_split(data, test_size=0.2)
        model = SVD()
        model.fit(trainset)
        predictions = []
        for recipe in recipes:
            pred = model.predict(user_id, recipe['id']).est
            predictions.append((recipe, pred))
        predictions.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in predictions[:5]]
    except Exception as e:
        print(f"Error in collaborative filtering: {e}")
        return recipes[:5] if recipes else []
    finally:
        cursor.close()
        connection.close()

# Root route for testing
@app.route('/')
def home():
    return jsonify({"message": "Recipe Recommendation App Backend is Running!"})

# API endpoint for recommendations
@app.route('/api/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400
        ingredients = data.get('ingredients', [])
        diet = data.get('diet', None)
        user_id = data.get('user_id', 1)

        if not ingredients:
            return jsonify({"error": "Ingredients are required"}), 400

        connection = get_db_connection()
        recipes = []
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id, title, instructions, nutritional_data, ingredients FROM recipes")
            cached = cursor.fetchall()
            cursor.close()
            connection.close()
            recipes = [{'id': r[0], 'title': r[1], 'instructions': r[2], 
                        'nutrition': json.loads(r[3]), 'ingredients': json.loads(r[4])} for r in cached]

        if not recipes:
            recipes = fetch_recipes(ingredients, diet)

        if not recipes:
            return jsonify({"error": "No recipes found"}), 404

        content_recipes = content_based_filtering(ingredients, recipes)
        final_recipes = collaborative_filtering(user_id, content_recipes)
        return jsonify(final_recipes)
    except Exception as e:
        print(f"Error in recommend endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

# API endpoint to save user rating
@app.route('/api/rate', methods=['POST'])
def rate_recipe():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400
        user_id = data.get('user_id', 1)
        recipe_id = data.get('recipe_id')
        rating = data.get('rating')
        if not all([recipe_id, rating]):
            return jsonify({"error": "Missing required fields"}), 400
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO ratings (user_id, recipe_id, rating)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE rating=%s
            """, (user_id, recipe_id, rating, rating))
            connection.commit()
            cursor.close()
            connection.close()
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error saving rating: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)