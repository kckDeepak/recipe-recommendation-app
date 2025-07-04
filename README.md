# Recipe Recommendation App

A web application that recommends personalized recipes based on user-input ingredients and dietary preferences, using a hybrid recommendation system (content-based and collaborative filtering). The app integrates with the Spoonacular API for recipe data, caches results in MySQL, and provides a responsive frontend for user interaction. The target is to achieve 92.5% recommendation accuracy.

## Tech Stack
- **Backend**: Python, Flask, MySQL, Spoonacular API, scikit-learn, scikit-surprise, NumPy (1.26.4)
- **Frontend**: HTML, CSS (Tailwind CSS via CDN), JavaScript
- **Environment**: `.env` for sensitive data (API key)

## Project Structure
```
recipe-recommendation-app/
├── backend/
│   ├── app.py              # Flask backend with API endpoints
│   ├── db_config.py        # MySQL configuration
│   ├── models.py           # Recommendation logic (content-based, collaborative)
│   ├── test_backend.py     # Unit tests for backend
│   ├── .env                # Environment variables (API key)
│   ├── .gitignore          # Ignore .env and other sensitive files
│   └── requirements.txt    # Python dependencies
├── frontend/
│   └── index.html          # Frontend with HTML, CSS, JavaScript
└── README.md               # Project documentation
```

## Features
- **Backend**:
  - `POST /api/recommend`: Recommends recipes based on ingredients, diet, and user ratings.
  - `POST /api/rate`: Saves user ratings to improve collaborative filtering.
  - `GET /`: Confirms server status.
  - Hybrid recommendation: Combines content-based (TF-IDF) and collaborative filtering (SVD via scikit-surprise).
  - MySQL caching to reduce Spoonacular API calls.
- **Frontend**:
  - Input form for ingredients and dietary preferences.
  - Displays recipe cards with title, ingredients, instructions, and nutrition.
  - Allows rating recipes (1–5 stars).
  - Responsive design using Tailwind CSS.

## Prerequisites
- Python 3.10+
- MySQL Server
- Spoonacular API key (sign up at https://spoonacular.com/food-api)
- Node.js (optional, for alternative frontend serving)
- Git (for cloning and managing repository)

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd recipe-recommendation-app
```

### 2. Backend Setup
1. **Navigate to Backend Directory**:
   ```bash
   cd backend
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   If `requirements.txt` is missing, install manually:
   ```bash
   pip install flask flask-cors requests mysql-connector-python scikit-learn pandas scikit-surprise numpy==1.26.4 python-dotenv
   ```

3. **Set Up MySQL Database**:
   - Start MySQL server.
   - Create the database and tables:
     ```sql
     CREATE DATABASE recipe_app;
     USE recipe_app;
     CREATE TABLE users (
         id INT AUTO_INCREMENT PRIMARY KEY,
         username VARCHAR(50) UNIQUE,
         preferences TEXT
     );
     CREATE TABLE recipes (
         id INT PRIMARY KEY,
         title VARCHAR(100),
         instructions TEXT,
         nutritional_data MEDIUMTEXT,
         ingredients TEXT
     );
     CREATE TABLE ratings (
         user_id INT,
         recipe_id INT,
         rating INT,
         PRIMARY KEY (user_id, recipe_id)
     );
     ```

4. **Configure MySQL**:
   - Edit `backend/db_config.py` with your MySQL credentials:
     ```python
     db_config = {
         'host': 'localhost',
         'user': 'your_username',
         'password': 'your_password',
         'database': 'recipe_app'
     }
     ```

5. **Set Up Environment Variables**:
   - Create `backend/.env`:
     ```plaintext
     SPOONACULAR_API_KEY=your_actual_api_key_here
     ```
   - Get your API key from https://spoonacular.com/food-api/console#Dashboard.
   - Ensure `.env` is included in `backend/.gitignore`.

6. **Run the Backend**:
   ```bash
   python app.py
   ```
   - The server runs at `http://localhost:5000`.
   - Test the root endpoint: `curl http://localhost:5000` (expect `{"message": "Recipe Recommendation App Backend is Running!"}`).

### 3. Frontend Setup
1. **Navigate to Frontend Directory**:
   ```bash
   cd frontend
   ```

2. **Serve the Frontend**:
   - Use Python’s HTTP server:
     ```bash
     python -m http.server 8000
     ```
   - Or use VS Code’s Live Server (port 5500).
   - Open `http://localhost:8000` (or `http://127.0.0.1:5500` for Live Server).

### 4. Usage
1. **Access the App**:
   - Open the frontend in a browser (`http://localhost:8000` or `http://127.0.0.1:5500`).
   - Enter ingredients (e.g., `chicken, tomatoes`) and select a dietary preference (optional).
   - Click "Get Recommendations" to view recipe cards.
   - Rate recipes (1–5 stars) and submit to save ratings.

2. **API Endpoints**:
   - **Recommend**: `POST /api/recommend`
     ```bash
     curl -X POST -H "Content-Type: application/json" -d '{"ingredients": ["chicken", "tomatoes"], "diet": "gluten-free", "user_id": 1}' http://localhost:5000/api/recommend
     ```
   - **Rate**: `POST /api/rate`
     ```bash
     curl -X POST -H "Content-Type: application/json" -d '{"user_id": 1, "recipe_id": 123, "rating": 4}' http://localhost:5000/api/rate
     ```

### 5. Testing
- **Run Backend Tests**:
  ```bash
  cd backend
  python test_backend.py
  ```
  - Requires a valid `SPOONACULAR_API_KEY` in `.env`.
  - Tests root endpoint, recommendation, rating, and API connectivity.

- **Manual Testing**:
  - Verify frontend displays recipes and submits ratings.
  - Check Flask terminal for API request logs.
  - Use browser console (`Ctrl+Shift+J`) for frontend errors.

### Troubleshooting
- **CORS Errors**:
  - Ensure `flask-cors` is installed and `CORS(app)` is in `app.py`.
  - Check browser console for details.
- **API 401 Unauthorized**:
  - Verify `SPOONACULAR_API_KEY` in `.env`.
  - Test the key:
    ```python
    import requests
    from dotenv import load_dotenv
    import os
    load_dotenv()
    url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients=chicken,tomatoes&number=1&apiKey={os.getenv('SPOONACULAR_API_KEY')}"
    print(requests.get(url).status_code)
    ```
- **MySQL Errors**:
  - Confirm MySQL server is running: `mysqladmin -u your_username -p status`.
  - Verify `nutritional_data` is `MEDIUMTEXT`:
    ```sql
    DESCRIBE recipes;
    ```
- **No Recipes Displayed**:
  - Check Flask terminal for API or MySQL errors.
  - Ensure valid ingredients and API key.
- **Environment Variable Issues**:
  - Verify `.env` exists and `python-dotenv` is installed.
  - Test loading:
    ```python
    from dotenv import load_dotenv
    import os
    load_dotenv()
    print(os.getenv("SPOONACULAR_API_KEY"))
    ```

### Notes
- **Spoonacular API**: Free tier has a 150 requests/day limit. MySQL caching reduces API usage.
- **Recommendation System**: Uses content-based (TF-IDF) and collaborative filtering (SVD via scikit-surprise, with fallback if unavailable).
- **User ID**: Hardcoded as `1` for testing; implement authentication for production.
- **Security**: `.env` is excluded from version control via `.gitignore`.

### Future Improvements
- Add user authentication (e.g., JWT).
- Include recipe images from Spoonacular API.
- Implement search history or saved recipes.
- Deploy to Heroku (backend) and Netlify (frontend).
- Evaluate recommendation accuracy against 92.5% goal using user feedback.

### License
MIT License © 2025