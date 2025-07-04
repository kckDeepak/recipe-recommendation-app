const express = require('express');
const axios = require('axios');
const router = express.Router();

// Spoonacular API base URL
const API_BASE_URL = 'https://api.spoonacular.com';
const API_KEY = process.env.SPOONACULAR_API_KEY;

const winston = require('winston');
const logger = winston.createLogger({
  level: 'error',
  format: winston.format.json(),
  transports: [new winston.transports.File({ filename: 'error.log' })]
});

// Endpoint to search recipes by ingredients
router.get('/search', async (req, res) => {
  try {
    const { ingredients, diet, mealType } = req.query; // e.g., ?ingredients=chicken,tomatoes&diet=vegan&mealType=dinner
    const response = await axios.get(`${API_BASE_URL}/recipes/findByIngredients`, {
      params: {
        apiKey: API_KEY,
        ingredients: ingredients || '',
        diet: diet || '',
        type: mealType || '',
        number: 10, // Limit to 10 results
        includeNutrition: true
      }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching recipes:', error.message);
    res.status(500).json({ error: 'Failed to fetch recipes' });
  }
});

// Endpoint to get detailed recipe information
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const response = await axios.get(`${API_BASE_URL}/recipes/${id}/information`, {
      params: {
        apiKey: API_KEY,
        includeNutrition: true
      }
    });
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching recipe details:', error.message);
    res.status(500).json({ error: 'Failed to fetch recipe details' });
  }
});

const { PythonShell } = require('python-shell');

router.get('/recommend', async (req, res) => {
  try {
    const { ingredients, diet, mealType } = req.query;
    // Fetch recipes from Spoonacular
    const response = await axios.get(`${API_BASE_URL}/recipes/findByIngredients`, {
      params: {
        apiKey: API_KEY,
        ingredients: ingredients || '',
        diet: diet || '',
        type: mealType || '',
        number: 50 // Fetch more for filtering
      }
    });
    const recipes = response.data;

    // Run Python script
    let options = {
      mode: 'text',
      pythonOptions: ['-u'],
      scriptPath: '../models',
      args: [JSON.stringify({ ingredients, diet, mealType, recipes })]
    };

    PythonShell.run('recommendation.py', options, (err, results) => {
      if (err) {
        logger.error('Python script error:', err);
        return res.status(500).json({ error: 'Recommendation failed' });
      }
      res.json(JSON.parse(results[0]));
    });
  } catch (error) {
    logger.error('Error in recommend endpoint:', error);
    res.status(500).json({ error: 'Failed to generate recommendations' });
  }
});

const connectDB = require('../db');

router.get('/search', async (req, res) => {
  try {
    const { ingredients, diet, mealType } = req.query;
    const db = await connectDB();
    const cacheKey = `${ingredients}_${diet}_${mealType}`;
    const cached = await db.collection('recipes').findOne({ cacheKey });

    if (cached) {
      return res.json(cached.recipes);
    }

    const response = await axios.get(`${API_BASE_URL}/recipes/findByIngredients`, {
      params: {
        apiKey: API_KEY,
        ingredients: ingredients || '',
        diet: diet || '',
        type: mealType || '',
        number: 10,
        includeNutrition: true
      }
    });

    await db.collection('recipes').insertOne({
      cacheKey,
      recipes: response.data,
      timestamp: new Date()
    });

    res.json(response.data);
  } catch (error) {
    logger.error('Error fetching recipes:', error);
    res.status(500).json({ error: 'Failed to fetch recipes' });
  }
});

router.post('/user', async (req, res) => {
  try {
    const { userId, preferences } = req.body;
    const db = await connectDB();
    await db.collection('users').updateOne(
      { userId },
      { $set: { preferences, updatedAt: new Date() } },
      { upsert: true }
    );
    res.json({ message: 'User profile saved' });
  } catch (error) {
    logger.error('Error saving user profile:', error);
    res.status(500).json({ error: 'Failed to save profile' });
  }
});

module.exports = router;
