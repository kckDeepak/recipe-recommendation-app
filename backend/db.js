const { MongoClient } = require('mongodb');

const uri = process.env.MONGODB_URI;

async function connectDB() {
  if (!uri) {
    throw new Error('MONGODB_URI is not defined in .env file');
  }

  const client = new MongoClient(uri, {
    useNewUrlParser: true,
    useUnifiedTopology: true
  });

  try {
    await client.connect();
    console.log('Connected to MongoDB');
    return client.db('recipe_app');
  } catch (error) {
    console.error('MongoDB connection error:', error);
    throw error;
  }
}

module.exports = connectDB;