import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import sys

def content_based_filtering(ingredients, diet, meal_type, recipes):
    # Convert recipes to DataFrame
    df = pd.DataFrame(recipes)
    # Combine relevant features (ingredients, diet, meal type)
    df['features'] = df['usedIngredients'].apply(lambda x: ' '.join([i['name'] for i in x])) + ' ' + df['title']
    if diet:
        df['features'] += ' ' + diet
    if meal_type:
        df['features'] += ' ' + meal_type
    
    # Apply TF-IDF vectorization
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['features'])
    user_input = ' '.join(ingredients.split(',')) + f' {diet} {meal_type}'
    user_vector = tfidf.transform([user_input])
    
    # Calculate similarity scores
    from sklearn.metrics.pairwise import cosine_similarity
    scores = cosine_similarity(user_vector, tfidf_matrix).flatten()
    df['score'] = scores
    
    # Sort and return top 10 recipes
    top_recipes = df.sort_values('score', ascending=False).head(10)
    return top_recipes[['id', 'title', 'score']].to_dict('records')

if __name__ == '__main__':
    # Read input from Node.js
    input_data = json.loads(sys.argv[1])
    ingredients = input_data.get('ingredients', '')
    diet = input_data.get('diet', '')
    meal_type = input_data.get('mealType', '')
    recipes = input_data.get('recipes', [])
    
    # Get recommendations
    recommendations = content_based_filtering(ingredients, diet, meal_type, recipes)
    print(json.dumps(recommendations))

def collaborative_filtering(user_id, recipes):
    # Placeholder for future implementation using Surprise library
    pass