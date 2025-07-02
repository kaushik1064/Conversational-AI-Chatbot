import os
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Google Search API setup
os.environ["GOOGLE_CSE_ID"] = "d462d158ef7f54c92"
os.environ["GOOGLE_API_KEY"] = "AIzaSyDkTFp6AkzIUJOI9oux6vBOzcimKgKtUv0"

search = GoogleSearchAPIWrapper()

def top5_results(query):
    return search.results(query, 1)

tool = Tool(
    name="Google Search Snippets",
    description="Search Google for recent results.",
    func=top5_results,
)

# Selenium setup
def create_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scrape_headings_paragraphs(url):
    driver = create_webdriver()  # Create WebDriver instance
    try:
        driver.get(url)
        headings = []
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            elements = driver.find_elements(By.TAG_NAME, tag)
            headings.extend([elem.text for elem in elements if elem.text.strip() != ''])
        paragraphs = [elem.text for elem in driver.find_elements(By.TAG_NAME, 'p') if elem.text.strip() != '']
        return headings, paragraphs
    finally:
        driver.quit()  # Ensure WebDriver is properly closed

def search_and_scrape(query):
    results = tool.run(query)
    links = [result['link'] for result in results if 'link' in result]  # Extract the links from the results

    all_headings = []
    all_paragraphs = []

    for url in links:
        if isinstance(url, str) and url.startswith("http"):  # Ensure that the URL is a valid string
            headings, paragraphs = scrape_headings_paragraphs(url)
            all_headings.extend(headings)
            all_paragraphs.extend(paragraphs)
        else:
            print(f"Invalid URL: {url}")

    return links, all_headings, all_paragraphs
