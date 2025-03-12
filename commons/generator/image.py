import os
import random
import numpy as np
import requests

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

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=chrome_options, service=service)
    
    return driver

def get_image_url(query):
    driver = init_chromedriver()
    driver.get(f"https://id.pinterest.com/search/pins/?q={query.lower().replace(' ', '%20')}")

    image_urls = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@role='list']//div/img")))
    image_url = random.choice(image_urls).get_attribute("src")
    driver.quit()

    return image_url

def get_image_with_high_resolution(query):
    image_url = get_image_url(query)
    image = Image.open(requests.get(image_url, stream=True).raw)

    # Resize image using opencv
    image_cv = np.array(image)
    resized_image = image_cv.copy() # cv2.resize(image_cv, (700, 650), interpolation=cv2.INTER_AREA)

    img = Image.fromarray(resized_image)
    return img

def upload_image(username, password, image, caption):
    cl = Client()
    cl.login(username=username, password=password)

    # Load and resize the image
    temp_image_path = f"temp_image_{username}.jpg"
    image.save(temp_image_path)

    # Prepare the image
    prepare_image(temp_image_path)

    # Upload the image with the specified caption
    cl.photo_upload(temp_image_path, 
                    caption=caption,
                    extra_data={"custom_accessibility_caption": "alt text example",
                                "like_and_view_counts_disabled": 1,
                                "disable_comments": 1,})

    # Clean up temporary files
    os.remove(temp_image_path)

    

    
    