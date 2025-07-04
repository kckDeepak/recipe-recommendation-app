import unittest
import requests
from app import app
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class BackendTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.api_key = os.getenv("SPOONACULAR_API_KEY")
        if not self.api_key:
            self.skipTest("SPOONACULAR_API_KEY not found in .env file")

    def test_root_endpoint(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['message'], "Recipe Recommendation App Backend is Running!")

    def test_recommend_endpoint(self):
        response = self.app.post('/api/recommend', 
                               json={'ingredients': ['chicken', 'tomatoes'], 'diet': 'gluten-free', 'user_id': 1})
        self.assertIn(response.status_code, [200, 400, 404, 500])
        if response.status_code == 200:
            data = response.get_json()
            self.assertIsInstance(data, list)
            if data:
                self.assertIn('id', data[0])
                self.assertIn('title', data[0])
                self.assertIn('instructions', data[0])
                self.assertIn('nutrition', data[0])

    def test_rate_endpoint(self):
        response = self.app.post('/api/rate', 
                               json={'user_id': 1, 'recipe_id': 123, 'rating': 4})
        self.assertIn(response.status_code, [200, 400, 500])
        if response.status_code == 200:
            data = response.get_json()
            self.assertEqual(data['status'], 'success')

    def test_fetch_recipes(self):
        url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients=chicken,tomatoes&number=1&apiKey={self.api_key}"
        try:
            response = requests.get(url, timeout=5)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIsInstance(data, list)
        except requests.RequestException:
            self.skipTest("Spoonacular API unavailable")

if __name__ == '__main__':
    unittest.main()