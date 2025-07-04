require('dotenv').config();
const express = require('express');
const recipeRoutes = require('./routes/recipes');
const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());
app.use('/api/recipes', recipeRoutes);

app.get('/', (req, res) => {
  res.send('Recipe Recommendation App Backend');
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});