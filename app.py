from streamlit_dash import image_select
from commons.langchain.model import _recommender_chain, _meal_extractor_chain
from commons.langchain.prompt import end_prompt, default_prompt_to_extract_items_from_list, string_to_stream
from commons.generator.image import get_image_object, upload_image
from instagrapi.exceptions import BadPassword, UnknownError
from streamlit_js_eval import streamlit_js_eval
import streamlit as st
import pandas as pd
from PIL import Image 
import requests
import re
import os

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

def main():
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
        if "recommendation_response" not in st.session_state:
            st.session_state.recommendation_response = ""
        if "meal_name" not in st.session_state:
            st.session_state.meal_name = ""
        if "meal_ingredients" not in st.session_state:
            st.session_state.meal_ingredients = ""
        if "meal_steps" not in st.session_state:
            st.session_state.meal_steps = ""

        # Recommend the meal
        messages = [
            ("system", end_prompt),
            ("user", f"Suggest a suitable {st.session_state.meal_preference} meal for a {st.session_state.age}-year-old {'man' if st.session_state.gender == 'Male' else 'woman'} with a current weight of {st.session_state.current_weight} kg, aiming to reach {st.session_state.target_weight} kg.\n\nAdditional preferences: {st.session_state.description}."),
        ]

        st.session_state.recommendation_response = _recommender_chain.invoke(messages)

        # Extract the meal name    
        st.session_state.meal_name = _meal_extractor_chain.invoke(f"Extract the meal name from following text\n{st.session_state.recommendation_response}")

        with st.chat_message("human"):
            st.write(f"What is your recommendation for my {st.session_state.meal_preference} meal?")

        with st.chat_message("assistant"):
            st.write_stream(list(f"Meow! Your purr-fect meal is **{st.session_state.meal_name}** 🐾"))
        
        # Extract the meal ingredients
        messages = [
            ("system", default_prompt_to_extract_items_from_list),
            ("user", f"Extract the ingredients, along with appropriate portion sizes, from following text\n{st.session_state.recommendation_response}")
        ]

        ingredients = st.session_state.recommendation_response.split(r"**Ingredients**")[1].split("\n\n")[0]
        st.session_state.meal_ingredients = re.findall(r"\*\s+(.+)\n", ingredients)
        
        ingredients_query = ''.join(string_to_stream(st.session_state.meal_ingredients, prefix="* ", separator="\n* ", suffix=""))

        with st.chat_message("human"):
            st.write(f"What are the required ingredients for {st.session_state.meal_name}?")

        with st.chat_message("assistant"):
            st.write_stream(list(f"Meowster chef says you need these pawsome ingredients for **{st.session_state.meal_name}** 🐾\n{ingredients_query}"))

        # Extract the meal steps
        messages = [
            ("system", default_prompt_to_extract_items_from_list),
            ("user", f"Extract only the step descriptions from the text, removing step numbers and formatting. Return the result as a list of strings, from following text\n{st.session_state.recommendation_response}")
        ]

        st.session_state.meal_steps = re.findall(r"\*\*Step \d+\*\*: (.+)\n", st.session_state.recommendation_response)
        meal_steps_query = ''.join(string_to_stream(st.session_state.meal_steps, prefix="* ", separator="\n* ", suffix=""))

        with st.chat_message("human"):
            st.write(f"What are the steps to prepare {st.session_state.meal_name}?")

        with st.chat_message("assistant"):
            st.write_stream(list(f"Time to whip up some purr-fection! Here are the steps to make **{st.session_state.meal_name}** with your chosen ingredients 🐾\n{meal_steps_query}"))

        # Nutrition Analysis
        st.subheader("Nutrition Analysis", divider="rainbow")
        
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
        if "ig_username" not in st.session_state:
            st.session_state.ig_username = ""
        if "ig_password" not in st.session_state:
            st.session_state.ig_password = ""
        if "temp_image" not in st.session_state:
            st.session_state.temp_image = ""
        if "image_caption" not in st.session_state:
            st.session_state.image_caption = ""
                
        message = st.empty() # Placeholder after user input username and password
        if not st.session_state.posting_complete:
            refresh_button = st.empty()
        
        _, col, _ = st.columns([1, 2, 1])
        with col:
            with st.form("my_form"):
                st.session_state.ig_username = st.text_input("Username", value="")
                st.session_state.ig_password = st.text_input("Password", type="password", value="")

                submitted = st.form_submit_button("Submit")

        temp_file_path = f"temp_file_{st.session_state.ig_username}.jpg"

        if st.session_state.ig_username and os.path.exists(st.session_state.temp_image): # and (st.session_state.temp_image != temp_file_path):
            os.remove(st.session_state.temp_image)

        if not os.path.exists(temp_file_path):
            try:
                meal_image = get_image_object(query=st.session_state.meal_name)

            except IndexError:
                st.session_state.analysis_complete = False
                main()

        else:
            meal_image = Image.open(temp_file_path)

        if not st.session_state.image_caption:
            st.session_state.image_caption = _recommender_chain.invoke(f"Provide a single, straightforward Instagram post caption that tells the audience the content creator is starting a healthy life.\n\nContext:\n{st.session_state.recommendation_response}")
        
        if st.session_state.ig_username and st.session_state.ig_password and not st.session_state.posting_complete:
            try:
                message.warning(f"If you believe the Instagram username exists but the submission is still processing, please visit https://www.instagram.com/{st.session_state.ig_username}/ to verify the user.\n\nPlease click the button below after confirming that the account belongs to you.")
                refresh_button.button("Refresh", on_click=main)
                upload_image(username=st.session_state.ig_username, 
                            password=st.session_state.ig_password, 
                            image_obj=meal_image, 
                            image_file_path=temp_file_path,
                            caption=st.session_state.image_caption)
            
            except UnknownError:
                message.error(f"Username {st.session_state.ig_username} doesn't exist.")

            except BadPassword:
                message.error("Wrong Password. Please try again.")

            else:
                st.session_state.posting_complete = True
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

            finally:     
                st.session_state.temp_image = temp_file_path
        
        else:
            if not st.session_state.posting_complete:
                message.info("Enter your Instagram username and password so we can automatically post content through your account.")

        if st.session_state.posting_complete:
            message.success("Upload photo completed.")
        
        if not st.session_state.posting_complete:
            st.subheader("Post", divider="rainbow")
            st.write(meal_image)

            st.subheader("Caption", divider="rainbow")
            st.write(st.session_state.image_caption)

        else:
            if st.button("Restart", type="primary"):
                streamlit_js_eval(js_expressions="parent.window.location.reload()")

if __name__ == "__main__":
    main()