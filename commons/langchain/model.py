from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser, CommaSeparatedListOutputParser
import streamlit as st

_recommender = init_chat_model("gemini-2.0-flash", 
                               model_provider="google_genai",
                               temperature=1,
                               top_p=1,
                               google_api_key=st.secrets["GOOGLE_API_KEY"])

_recommender_chain = _recommender | StrOutputParser()

_extractor = init_chat_model("gemini-2.0-flash", 
                                        model_provider="google_genai",
                                        temperature=0.1,
                                        top_p=0.4,
                                        google_api_key=st.secrets["GOOGLE_API_KEY"])

_ingredient_extractor_chain = _extractor | CommaSeparatedListOutputParser()
_meal_extractor_chain = _extractor | StrOutputParser()