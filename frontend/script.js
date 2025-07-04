const API_BASE_URL = 'http://localhost:5000';
const recommendBtn = document.getElementById('recommend-btn');
const ingredientsInput = document.getElementById('ingredients');
const dietSelect = document.getElementById('diet');
const errorMessage = document.getElementById('error-message');
const recipesSection = document.getElementById('recipes');

recommendBtn.addEventListener('click', async () => {
    errorMessage.classList.add('hidden');
    recipesSection.innerHTML = '';

    const ingredients = ingredientsInput.value.trim().split(',').map(i => i.trim()).filter(i => i);
    const diet = dietSelect.value;

    if (ingredients.length === 0) {
        showError('Please enter at least one ingredient.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ingredients,
                diet: diet || undefined,
                user_id: 1
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.error || 'Failed to fetch recommendations.');
            return;
        }

        if (data.length === 0) {
            showError('No recipes found for the given ingredients.');
            return;
        }

        displayRecipes(data);
    } catch (error) {
        showError('An error occurred while fetching recommendations.');
        console.error('Fetch error:', error);
    }
});

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function displayRecipes(recipes) {
    recipesSection.innerHTML = '';
    recipes.forEach(recipe => {
        const card = document.createElement('div');
        card.className = 'bg-white p-6 rounded-lg shadow-md';
        card.innerHTML = `
            <h3 class="text-xl font-semibold mb-2">${recipe.title}</h3>
            <p class="text-gray-700 mb-2"><strong>Ingredients:</strong> ${recipe.ingredients.join(', ')}</p>
            <p class="text-gray-700 mb-2"><strong>Instructions:</strong> ${recipe.instructions || 'No instructions available'}</p>
            <p class="text-gray-700 mb-4"><strong>Nutrition:</strong> ${formatNutrition(recipe.nutrition)}</p>
            <div class="flex items-center">
                <label class="text-sm font-medium text-gray-700 mr-2">Rate:</label>
                <select id="rating-${recipe.id}" class="p-1 border border-gray-300 rounded-md">
                    <option value="0">Select</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                    <option value="4">4</option>
                    <option value="5">5</option>
                </select>
                <button onclick="submitRating(${recipe.id})" class="ml-2 bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700">Submit</button>
            </div>
        `;
        recipesSection.appendChild(card);
    });
}

function formatNutrition(nutrition) {
    if (!nutrition || !nutrition.nutrients) return 'No nutritional data available';
    return nutrition.nutrients.map(n => `${n.name}: ${n.amount}${n.unit}`).join(', ');
}

async function submitRating(recipeId) {
    const rating = document.getElementById(`rating-${recipeId}`).value;
    if (rating === '0') {
        showError('Please select a rating.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/rate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: 1,
                recipe_id: recipeId,
                rating: parseInt(rating)
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.error || 'Failed to submit rating.');
            return;
        }

        alert('Rating submitted successfully!');
    } catch (error) {
        showError('An error occurred while submitting the rating.');
        console.error('Rating error:', error);
    }
}
