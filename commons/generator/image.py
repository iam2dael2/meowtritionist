import random
import numpy as np
import requests
import streamlit as st
import matplotlib.pyplot as plt

from PIL import Image
from instagrapi import Client
from selenium import webdriver
from selenium.webdriver.common.by import By
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

    # Choose one photo
    image_elements = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@role='list']//div/img[@src]")))

    chosen_idx = random.randint(0, min(len(image_elements), 5))
    image_element = image_elements[chosen_idx]

    driver.execute_script("arguments[0].click();", image_element)

    # closeup_image_elements = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@data-test-id, 'closeup-image')]//img")))
    # closeup_image_urls = [image.get_attribute("src") for image in closeup_image_elements]
    # closeup_image_url = max(closeup_image_urls)
    # print(f"Images URLs: {closeup_image_urls}")

    closeup_image_element = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//div//img[contains(@src, 'https://i.pinimg.com/736')]")))
    closeup_image_url = closeup_image_element.get_attribute("src")

    driver.quit()
    
    return closeup_image_url

@st.cache_data
def get_image_object(query):
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
    resize_image_for_instagram(image_file_path)

    cl = Client()
    cl.login(username=username, password=password)

    # Upload the image with the specified caption
    cl.photo_upload(image_file_path, 
                    caption=caption,
                    extra_data={"custom_accessibility_caption": "alt text example",
                                "like_and_view_counts_disabled": 1,
                                "disable_comments": 1,})
    
def resize_image_for_instagram(input_path, output_path=None, target_size=(1080, 1080)):
    if not output_path:
        output_path = input_path

    img = Image.open(input_path)
    
    # Resize by using Lanczos method
    img = img.resize(target_size, Image.LANCZOS)

    # Save a photo with high quality
    img.save(output_path, "JPEG", quality=95)