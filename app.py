from streamlit_dash import image_select
from commons.langchain.model import _recommender_chain, _ingredient_extractor_chain, _meal_extractor_chain
from commons.langchain.prompt import end_prompt, default_prompt_to_extract_items_from_list
from commons.generator.image import get_image_with_high_resolution, upload_image
from instagrapi.exceptions import BadPassword, UnknownError
from streamlit_js_eval import streamlit_js_eval
import streamlit as st
import pandas as pd
import requests

st.set_page_config("Meowtritionist", page_icon='😹')
st.title("Meow-tritionist")

if "meal_preference" not in st.session_state:
    st.session_state.meal_preference = ""
if "finish_choosing_meal_preference" not in st.session_state:
    st.session_state.finish_choosing_meal_preference = False
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "posting_complete" not in st.session_state:
    st.session_state.posting_complete = False

def finish_choosing_meal_preference():
    st.session_state.finish_choosing_meal_preference = True

def complete_setup():
    st.session_state.setup_complete = True

def complete_analysis():
    st.session_state.analysis_complete = True

#################################################################################

if not st.session_state.finish_choosing_meal_preference:
    st.markdown(
        "\"Meow~ Welcome, hooman! 🐾\""
        "\n\nI am Meow, your purr-sonal nutritionist! 😺 Here to guide you on a healthy and pawsome journey while making sure you still enjoy delicious treats—just like how a cat enjoys the finest tuna. 🐟✨"
    )
    st.subheader("Choose your Meal Preference", divider="rainbow")

    image_selected = image_select(
        label="",
        images=["images/breakfast.jpeg", "images/lunch.jpeg", "images/dinner.jpeg"],
        captions=["Breakfast", "Lunch", "Dinner"],
    )
    
    if len(image_selected) == 1:
        st.session_state.meal_preference = image_selected[0].lstrip("images/").rstrip(".jpeg")
        st.button('Paws up', on_click=finish_choosing_meal_preference)

    elif len(image_selected) > 1:
        st.error("""Pick just one meal purr-eference, hooman! One choice, one delicious feast! 🍽️🐱""")

if st.session_state.finish_choosing_meal_preference and not st.session_state.setup_complete:
    st.info("""Purr~lease fill in your info, hooman! 🐾 This will help me understand you better and fetch the purr-fect meal recommendations! 🍽️🐱""")
    st.subheader("Personal Information", divider="rainbow")

    if "gender" not in st.session_state:
        st.session_state.gender = "Male"
    if "age" not in st.session_state:
        st.session_state.age = 25
    if "description" not in st.session_state:
        st.session_state.description = ""
    if "current_weight" not in st.session_state:
        st.session_state.current_weight = 60
    if "target_weight" not in st.session_state:
        st.session_state.target_weight = 50

    col1, col2 = st.columns([1, 4])
    with col1:
        st.session_state.gender = st.radio("Gender", options=["Male", "Female"])
        st.session_state.age = st.number_input("Age", min_value=0, step=1, value=st.session_state.age)

    with col2:
        st.session_state.description = st.text_area("Dietary Preferences", max_chars=200, help="Additional information, possibly regarding food restrictions or any specific foods you’re interested in.", height=134, value=st.session_state.description)

    st.subheader("Weight Goals", divider="rainbow")
    col1, col2 = st.columns([1, 4])
    with col1:
        st.session_state.current_weight = st.number_input(label="Current Weight", min_value=0, help="Enter your current weight (in kg unit) as the nearest whole number.", step=1, value=st.session_state.current_weight)

    col1, col2 = st.columns([1, 4])
    with col1:
        st.session_state.target_weight = st.number_input(label="Target Weight", min_value=0, help="Enter your target weight (in kg unit) as the nearest whole number.", step=1, value=st.session_state.target_weight)

    st.markdown(f"**Your description**: Find good {st.session_state.meal_preference} meal for {st.session_state.age}-year-old {'man' if st.session_state.gender == 'Male' else 'woman'}.")
    st.button("Pick Your Meal!", icon="🐾", on_click=complete_setup)

if st.session_state.setup_complete and not st.session_state.analysis_complete:
    # Meal Recommendation
    messages = [
        ("system", end_prompt),
        ("user", f"Suggest a suitable {st.session_state.meal_preference} meal for a {st.session_state.age}-year-old {'man' if st.session_state.gender == 'Male' else 'woman'} with a current weight of {st.session_state.current_weight} kg, aiming to reach {st.session_state.target_weight} kg.\n\nAdditional preferences: {st.session_state.description}."),
    ]

    recommendation_stream = _recommender_chain.stream(messages)

    if "recommendation_response" not in st.session_state:
        st.session_state.recommendation_response = ""

    with st.chat_message("assistant"):
        st.session_state.recommendation_response = st.write_stream(recommendation_stream)

    # Extract the meal name
    if "meal_name" not in st.session_state:
        st.session_state.meal_name = ""
    
    st.session_state.meal_name = _meal_extractor_chain.invoke(f"Extract the meal name from following text\n{st.session_state.recommendation_response}")
    
    # Nutrition Analysis
    st.subheader("Nutrition Analysis", divider="rainbow")

    messages = [
        ("system", default_prompt_to_extract_items_from_list),
        ("user", f"Extract the ingredients, along with appropriate portion sizes, from following text\n{st.session_state.recommendation_response}")
    ]

    ingredients = _ingredient_extractor_chain.invoke(messages)
    ingredients_query = ", ".join(ingredients)
    
    # Extract the nutrition of given ingredients
    api_url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {"x-app-id": st.secrets["NUTRITIONIX_APP_ID"],
               "x-app-key": st.secrets["NUTRITIONIX_API_KEY"],
               "Content-Type": "application/json"}

    api_response = requests.post(api_url, json={"query": ingredients_query}, headers=headers)

    if api_response.status_code == 200:
        api_response_json = api_response.json()
        api_response_df = pd.DataFrame(api_response_json["foods"])
        columns_of_interest = ['food_name', 'serving_qty', 'serving_unit', 
                               'serving_weight_grams', 'nf_calories', 'nf_total_fat',
                               'nf_saturated_fat', 'nf_cholesterol', 'nf_sodium',
                               'nf_total_carbohydrate', 'nf_dietary_fiber', 'nf_sugars', 
                               'nf_protein', 'nf_potassium', 'nf_p']
        
        st.write(api_response_df[columns_of_interest])
        st.info("Click here if you optionally want to post content on Instagram.")
        st.button("Paw me up!", on_click=complete_analysis)

    else:
        raise requests.exceptions.RequestException("Error:", api_response.status_code, api_response.text)
    
if st.session_state.analysis_complete:
    meal_image = get_image_with_high_resolution(query=st.session_state.meal_name)

    if "ig_username" not in st.session_state:
        st.session_state.ig_username = ""
    if "ig_password" not in st.session_state:
        st.session_state.ig_password = ""
            
    message = st.empty() # Placeholder after user input username and password
    
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("my_form"):
            st.session_state.ig_username = st.text_input("Username", value="")
            st.session_state.ig_password = st.text_input("Password", type="password", value="")

            submitted = st.form_submit_button("Submit")

    if st.session_state.ig_username and st.session_state.ig_password and not st.session_state.posting_complete:
        try:
            upload_image(username=st.session_state.ig_username, 
                         password=st.session_state.ig_password, 
                         image=meal_image, 
                         caption=st.session_state.recommendation_response)
        
        except UnknownError:
            message.error(f"Username {st.session_state.ig_username} doesn't exist.")

        except BadPassword:
            message.error("Wrong Password. Please try again.")

        else:
            st.session_state.posting_complete = True
    
    else:
        if not st.session_state.posting_complete:
            message.info("Enter your Instagram username and password so we can automatically post content through your account.")

    if st.session_state.posting_complete:
        message.success("Upload photo completed.")
    
    if not st.session_state.posting_complete:
        st.subheader("Post", divider="rainbow")
        st.write(meal_image)

        st.subheader("Caption", divider="rainbow")
        st.write(st.session_state.recommendation_response)

    else:
        if st.button("Restart", type="primary"):
            streamlit_js_eval(js_expressions="parent.window.location.reload()")