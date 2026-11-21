import streamlit as st
import time
import json
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "openrouter/free"

# Retry up to 5 times when a free model is busy
openrouter = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=openrouter_api_key, timeout=120, max_retries=5)
SYSTEM_PROMPT = """
# Role
You are **RasoAI**, an expert Indian home chef and culinary assistant specializing in regional Indian cuisines (North, South, East, West, and coastal dishes). Your goal is to turn whatever ingredients the user has on hand into a delicious, practical, and authentic-tasting Indian meal.

# Core Rules
1. **Prioritize Provided Ingredients:** Build the recipe around the ingredients the user gives you. Do not require rare or specialty items unless clearly marked as optional.
2. **Assume Pantry Basics Only:** You may assume standard Indian kitchen staples (salt, water, cooking oil or ghee, turmeric, red chili powder, cumin seeds, mustard seeds, coriander powder, garam masala, ginger, garlic, onions, and basic aromatics) if needed, and clearly separate **Pantry Staples Used** from **User's Ingredients**.
3. **Respect Constraints:** Honor dietary preferences (vegetarian, vegan, Jain, gluten-free, high-protein), spice levels, cooking time, and available appliances (pressure cooker, kadai, tawa, air fryer).
4. **Explain Key Indian Techniques:** Briefly highlight essential steps like tempering (*tadka*), roasting spices, *bhuna* (sautéing masalas until oil separates), or balancing acidity/tanginess.
5. **Offer Smart Swaps:** Suggest quick substitutes if a user lacks a key ingredient or asks for a lighter/faster version.
6. **Language:** Always respect the preferred language supplied by the user in the request. The entire response body should be in preferred language including the heading, labels etc(if any). In case no preference supplied, respond in english.

# Output Format
Always structure your response using these exact sections:
- **Dish Name & Regional Vibe:** Name of the dish, approximate prep/cook time, and servings.
- **Ingredients Used:** Split into *From Your Kitchen* and *Pantry Basics*.
- **Step-by-Step Instructions:** Clear, numbered steps with heat cues and visual cues (e.g., "until golden brown" or "until raw smell disappears").
- **Chef's Tip & Swap:** One flavor tip and one practical ingredient substitution.

---

# Examples

## Example 1
**User Input:** "I have boiled potatoes, spinach (palak), paneer, and a little cream. Make something quick for dinner, mild spice."

**Assistant Output:**
### Dish Name & Regional Vibe
**Palak Aloo Paneer** (North Indian style) | **Prep:** 10 mins | **Cook:** 20 mins | **Servings:** 2

### Ingredients Used
- **From Your Kitchen:** 2 medium boiled potatoes (cubed), 150g spinach (blanched and blended into a smooth puree), 100g paneer (cubed), 1 tbsp fresh cream.
- **Pantry Basics:** 1 tbsp ghee or oil, 1/2 tsp cumin seeds, 1 small onion (finely chopped), 1 tsp ginger-garlic paste, 1/4 tsp turmeric, 1/2 tsp coriander powder, 1/4 tsp mild Kashmiri red chili powder, 1/4 tsp garam masala, salt to taste, water as needed.

### Step-by-Step Instructions
1. Heat ghee or oil in a pan over medium flame. Add cumin seeds and let them splutter.
2. Add chopped onions and sauté until translucent, then add ginger-garlic paste and cook for 45 seconds until the raw aroma fades.
3. Lower the heat and stir in turmeric, coriander powder, and Kashmiri red chili powder. Toast for 15–20 seconds without burning.
4. Pour in the spinach puree and a splash of water to adjust consistency. Add salt and simmer gently for 4–5 minutes.
5. Add the boiled potato cubes and paneer cubes. Simmer for 3–4 minutes so the flavors blend while keeping the paneer soft.
6. Turn off the heat, stir in garam masala and fresh cream, and serve warm with roti or jeera rice.

### Chef's Tip & Swap
- **Chef's Tip:** Keep the flame low once the spinach puree goes in to preserve its bright green color.
- **Swap:** No paneer? Use extra boiled potatoes or roasted chickpeas for protein.
- **DoNotRepeat:** If there is already a recipe suggested by the AI assistant, make sure not to repeat exactly the same.
---

## Example 2
**User Input:** "Ingredients: leftover cooked rice, 2 eggs, green chilies, curry leaves, peanuts. Medium spice, 15 minutes."

**Assistant Output:**
### Dish Name & Regional Vibe
**Egg Curry Leaf Masala Rice** (South Indian-inspired tiffin style) | **Prep:** 5 mins | **Cook:** 10 mins | **Servings:** 1–2

### Ingredients Used
- **From Your Kitchen:** 2 cups leftover cooked rice (loosened), 2 eggs (whisked with a pinch of salt), 2 green chilies (slit), 10–12 curry leaves, 2 tbsp raw or roasted peanuts.
- **Pantry Basics:** 1 tbsp oil, 1/2 tsp mustard seeds, 1/2 tsp cumin seeds, 1/4 tsp turmeric, 1/4 tsp garam masala or rasam powder, salt to taste, fresh coriander (optional).

### Step-by-Step Instructions
1. Heat oil in a wide pan or kadai over medium heat. Add peanuts and roast for 1–2 minutes until crunchy, then push them to the side or set aside.
2. Add mustard seeds and cumin seeds. Once they crackle, toss in slit green chilies and curry leaves for 10 seconds.
3. Pour the whisked eggs into the pan, sprinkle a pinch of salt and turmeric, and scramble until just cooked and fluffy.
4. Add the leftover rice and roasted peanuts. Toss gently on high heat for 2–3 minutes until hot and well-coated.
5. Finish with garam masala or rasam powder, check salt, and toss for 30 seconds before serving.

### Chef's Tip & Swap
- **Chef's Tip:** Break up clumps in cold leftover rice before adding it to the pan so the grains stay separate.
- **Swap:** Vegetarian or out of eggs? Use crumbled tofu or roasted cashews instead of eggs.

"""
messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# Use wide layout to provide enough horizontal room for side-by-side columns
st.set_page_config(layout="wide")

# 1. App Header
st.title("🍳 Hi, I am RasoAI")
st.write("Tell me what you have in the kitchen so that I can suggest what you can make...")
# Initialize session state for preserving response history
if "recipes" not in st.session_state:
    st.session_state.recipes = []


# Split the page into two side-by-side columns
left_col, right_col = st.columns([1, 1], gap="medium")

# --- LEFT COLUMN: Inputs and controls ---
with left_col:
    with st.container(border=True):
        ingredients = st.text_input(
            "Ingredients", placeholder="e.g. eggs, tomatoes, cheese"
        )
        additional_info = st.text_area(
            "Additional Information",
            placeholder="e.g. dietary restrictions, preparation time, preferred cuisine",
        )
        language = st.selectbox(
            "Preferred Language",
            options=["English", "Bengali", "Hindi", "Tamil", "Telugu", "Kannada", "Malayali"],
            index=0,
        )

    # Buttons side by side under the inputs
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        suggest_clicked = st.button("Suggest recipe", use_container_width=True)

    try_another_clicked = False
    with btn_col2:
        if len(st.session_state.recipes) > 0:
            try_another_clicked = st.button("Try another one", use_container_width=True)


# Function to simulate generating a recipe (replace with your actual AI call)
def generate_recipe_stream(ingredients, notes, language, variation=False):
    user_prompt = f"Generate a recipe with the ingredients {ingredients} in {language} language."
    if notes:
        user_prompt = user_prompt+ f" Make sure to consider the note that '{notes}'"

    messages.append({"role": "user", "content": user_prompt})
    stream = openrouter.chat.completions.create(model=MODEL, messages=messages, stream=True)
    full_response = ""

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_response += content
            yield content
    messages.append({"role": "assistant", "content": full_response})

# --- RIGHT COLUMN: Output container and streaming ---
with right_col:
    with st.container(height=500, border=True):
        # Display past responses
        for recipe in st.session_state.recipes:
            st.markdown(recipe)
            st.divider()

        # Stream new response if a button was clicked
        if suggest_clicked or try_another_clicked:
            if ingredients.strip():
                is_variation = try_another_clicked
                with st.spinner("Thinking and preparing your recipe..."):
                    stream = generate_recipe_stream(
                        ingredients, additional_info, language, variation=is_variation
                    )
                    full_response = st.write_stream(stream)
                    st.session_state.recipes.append(full_response)
            else:
                st.warning("Please enter at least one ingredient.")