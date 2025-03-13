import os
import cv2
import random
import numpy as np
import requests
import streamlit as st
import matplotlib.pyplot as plt

from PIL import Image
from instagrapi import Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from instagrapi.image_util import prepare_image
from selenium.webdriver.chrome.service import Service
from webdriver_manager.core.os_manager import ChromeType
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def init_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(options=chrome_options, service=service)
    
    return driver

@st.cache_data
def get_image_url(query):
    driver = init_chromedriver()
    driver.get(f"https://id.pinterest.com/search/pins/?q={query.lower().replace(' ', '%20')}")

    image_urls = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@role='list']//div/img")))
    
    chosen_idx = random.randint(0, min(len(image_urls), 3))
    image_url = image_urls[chosen_idx].get_attribute("src")

    driver.quit()

    return image_url

@st.cache_data
def get_image_with_high_resolution(query):
    image_url = get_image_url(query)
    image = Image.open(requests.get(image_url, stream=True).raw)

    # Resize image using opencv
    image_cv = np.array(image)
    img = Image.fromarray(image_cv)
    
    return img

@st.cache_resource
def upload_image(username, password, image_obj, caption, image_file_path):
    image_arr = np.array(image_obj)
    
    # Load and resize the image
    fig, ax = plt.subplots(figsize=(image_arr.shape[1] / 100, image_arr.shape[0] / 100))
    ax.imshow(image_arr)
    ax.axis("off")
    fig.savefig(image_file_path, format="jpg", dpi=1200, bbox_inches="tight", pad_inches=0)

    # Prepare the image
    prepare_image(image_file_path, save_path=image_file_path)

    cl = Client()
    cl.login(username=username, password=password)

    # Upload the image with the specified caption
    cl.photo_upload(image_file_path, 
                    caption=caption,
                    extra_data={"custom_accessibility_caption": "alt text example",
                                "like_and_view_counts_disabled": 1,
                                "disable_comments": 1,})