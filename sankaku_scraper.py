import os
from os import listdir
from os.path import join
import json
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pickle as pkl
import selenium
import argparse
from datetime import datetime
import urllib.parse

class SankakuScraper:
    """
    A scraper for Sankaku Complex that collects images and metadata based on specified tags and ratings.
    """
    def __init__(self, 
                 data_name, 
                 tags=None, 
                 rating=None, 
                 full_image=False, 
                 single_character=False,
                 no_ai=False,
                 ai_only=False,
                 base_dir = "scraped_images",
                 video_flag = 0,
                 base_url="https://chan.sankakucomplex.com"):
        """
        Initializes the SankakuScraper with the given parameters.

        Args:
            data_name (str): The name of the data category to scrape.
            tags (list, optional): List of tags to scrape. Defaults to None.
            rating (list, optional): List of ratings to scrape. Defaults to None.
            full_image (bool, optional): Whether to scrape full images. Defaults to False.
            single_character (bool, optional): Whether to scrape only single character images. Defaults to False.
            no_ai (bool, optional): Whether to exclude AI-created images. Defaults to False.
            ai_only (bool, optional): Whether to include only AI-created images. Defaults to False.
            base_dir (str, optional): Base directory for saving scraped images. Defaults to "scraped_images".
            video_flag (int, optional): Flag to include videos. Defaults to 0.
            base_url (str, optional): Base URL for Sankaku Complex. Defaults to "https://chan.sankakucomplex.com".
        """
        self.base_url = base_url
        self.data_name = data_name
        self.rating_to_scrape = rating
        self.full_image = full_image
        self.single_character = single_character
        self.no_ai = no_ai
        self.ai_only = ai_only
        self.base_dir = base_dir
        
        if video_flag == 0:
            self.allowed_formats = {"jpg", "jpeg", "png", "webp"}
        elif video_flag == 1:
            self.allowed_formats = {"jpg", "jpeg", "png", "webp", 'webm', 'mp4', 'mov'}
        elif video_flag == 2:
            self.allowed_formats = {'webm', 'mp4', 'mov'}

        self.output_dir = join(self.base_dir, data_name)
        if tags is None:
            with open("tags.txt", "r") as file:
                self.tags_list = [line.strip() for line in file.readlines()]
        elif self.single_character:
            self.character_name = tags[0]
            self.tags_list = tags
        else:
            self.tags_list = tags

        if self.rating_to_scrape is not None and len(self.rating_to_scrape) == 1:
            for i in range(len(self.tags_list)):
                self.tags_list[i] = self.tags_list[i] + f'+rating%3A{self.rating_to_scrape[0]}'
        if self.no_ai:
            for i in range(len(self.tags_list)):
                self.tags_list[i] = self.tags_list[i] + '+-ai-created'
        if self.ai_only:
            for i in range(len(self.tags_list)):
                self.tags_list[i] = self.tags_list[i] + '+ai-created'
        for i in range(len(self.tags_list)):
            self.tags_list[i] = self.tags_list[i] + '+-holostars'

        # Ensure output directory exists
        os.makedirs(join(self.output_dir, 'labels'), exist_ok=True)

        # Initialize page number and collected_images
        self.page_num = 1
        self.last_page = 0
        self.clear_pages_count = 0
        self.clear_pages_limit = 3
        self.scrape = True
        self.end_of_page = False
        self.collected_images = []

        # Initialize WebDriver
        self.initialize_webdriver()

    def load_cookies_from_file(self, cookie_file_path):
        """
        Loads cookies from a file.

        Args:
            cookie_file_path (str): Path to the cookie file.

        Returns:
            list: List of cookies.
        """
        cookies = []
        with open(cookie_file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if not line.startswith('#') and len(line.strip()) > 0:
                    # Netscape cookie format: domain, flag, path, secure, expiration, name, value
                    fields = line.strip().split('\t')
                    if len(fields) >= 7:
                        cookie = {
                            'domain': fields[0],
                            'name': fields[5],
                            'value': fields[6],
                            'path': fields[2],
                            'secure': fields[3].lower() == 'true',
                            'expiry': int(fields[4]) if fields[4].isdigit() else None
                        }
                        cookies.append(cookie)
        return cookies

    def add_cookies_to_driver(self, cookies):
        """
        Adds cookies to the WebDriver.

        Args:
            cookies (list): List of cookies to add.
        """
        self.driver.get('https://chan.sankakucomplex.com')

        for cookie in cookies:
            self.driver.add_cookie(cookie)

    def initialize_webdriver(self, cookie_file_path = 'skkc_cookie.txt'):
        """
        Initializes the WebDriver with the specified cookies.

        Args:
            cookie_file_path (str, optional): Path to the cookie file. Defaults to 'skkc_cookie.txt'.
        """
        cookies = self.load_cookies_from_file(cookie_file_path)

        # Headless browser setup
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--enable-unsafe-swiftshader")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-logging")

        # Initialize the WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)

        self.add_cookies_to_driver(cookies)


    def scrape_page(self, max_images):
        """
        Scrapes a page for images and metadata.

        Args:
            max_images (int): Maximum number of images to scrape.
        """
        url = self.search_url.format(page_num=self.page_num)
        header = f" \"{urllib.parse.unquote(self.cur_tag.split('+')[0])}\" page {self.page_num} "
        print(f"\n{'-'*((100-(len(header)))//2)}{header}{'-'*((100-(len(header)))//2)}")
        self.driver.get(url)
        time.sleep(2)  # Allow the page to load

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        posts_containers = soup.find_all("div", class_="posts-container gap-2")

        if not posts_containers:
            self.end_of_page = True
            return

        for posts_container in posts_containers:
            article_elements = posts_container.find_all("article")
            clear_count = 0
            for article in article_elements:
                if len(self.collected_images) >= max_images:
                    return  # Stop scraping if the desired number of images is reached
                link = article.find("a", href=True)
                if link:
                    post_url = self.base_url + link['href']
                    if post_url not in self.collected_images and self.process_post(post_url):
                        self.collected_images.append(post_url)
                        # Save progress to log file
                        pkl.dump([self.collected_images, self.last_page], open(join(self.output_dir, 'log.pkl'), 'wb'))
                        print(f"- Collected {len(self.collected_images)}/{max_images}")
                    else:
                        clear_count += 1
            if clear_count == len(article_elements):
                self.clear_pages_count += 1
            else:
                self.clear_pages_count = 0
                if self.page_num > self.last_page:
                    self.last_page = self.page_num
                    print(f"\n{'*'*100}")
                    print(f"\nNew last page: {self.last_page}")
            if self.clear_pages_count == self.clear_pages_limit:
                header = f" Jumping to page {self.last_page} "
                print(f"\n{'-'*((100-(len(header)))//2)}{header}{'-'*((100-(len(header)))//2)}")
                self.page_num = self.last_page-1

    def process_post(self, post_url):
        """
        Processes a post to extract image and metadata.

        Args:
            post_url (str): URL of the post to process.

        Returns:
            bool: True if the post was processed successfully, False otherwise.
        """
        self.driver.get(post_url)
        time.sleep(2)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        if not self.full_image:
            image = soup.select_one("#image-link img")
        else:
            image = soup.select_one("#highres")
        
        if image and (image.has_attr("src") or image.has_attr("href")):
            image_url = image["src"] if not self.full_image else image["href"]
            
            # Ensure the image URL is complete
            # if not image_url.startswith("http"):
            #     image_url = self.base_url + image_url
            image_url = 'https:' + image_url
            
            original_image_name = image_url.split('?')[0].split("/")[-1]
            image_extension = original_image_name.split("?")[0].split(".")[-1].lower()

            post_id = self.extract_post_id(soup)
            rating = self.extract_rating(soup)
            characters = self.extract_tags(soup, "li.tag-type-character")

            if image_extension not in self.allowed_formats:
                return False
            elif self.single_character:
                for character in characters:
                    if self.character_name not in character:
                        return False
            
            print(f"\n- Processing: {post_url}")

            new_filename = f"{self.cur_tag.split('+')[0]}_{(5-len(str(len(self.collected_images)+1)))*'0'}{len(self.collected_images)+1}"
            # Download the image
            self.download_image(image_url, f"{new_filename}.{image_extension}")

            # Scrape the metadata
            metadata = {
                "post_id": post_id,
                "rating": rating,
                "original_url": post_url,
                "original_filename": original_image_name,
                "tags": {
                    "artist": self.extract_tags(soup, "li.tag-type-artist"),
                    "copyright": self.extract_tags(soup, "li.tag-type-copyright"),
                    "character": characters,
                    "genre": self.extract_tags(soup, "li.tag-type-genre"),
                    "fashion": self.extract_tags(soup, "li.tag-type-fashion"),
                    "anatomy": self.extract_tags(soup, "li.tag-type-anatomy"),
                    "pose": self.extract_tags(soup, "li.tag-type-pose"),
                    "activity": self.extract_tags(soup, "li.tag-type-activity"),
                    "entity": self.extract_tags(soup, "li.tag-type-entity"),
                    "object": self.extract_tags(soup, "li.tag-type-object"),
                    "substance": self.extract_tags(soup, "li.tag-type-substance"),
                    "setting": self.extract_tags(soup, "li.tag-type-setting"),
                    "general": self.extract_tags(soup, "li.tag-type-general"),
                    "meta": self.extract_tags(soup, "li.tag-type-meta"),
                    "automatic": self.extract_tags(soup, "li.tag-type-automatic")
                },
            }

            # Save metadata as JSON
            self.save_metadata(f"{new_filename}.{image_extension}", metadata)
            return True
        return False

    def extract_rating(self, soup):
        """
        Extracts the rating from the parsed HTML document.

        Args:
            soup (BeautifulSoup): Parsed HTML document.

        Returns:
            str: The rating as 'General', 'Questionable', or 'Explicit'.
        """
        # Find the span element below #stats
        rating_span = soup.select_one("#stats span[class^='rating-']")

        if rating_span:
            # Get the class value (assuming only one class related to rating is present)
            rating_class = rating_span.get("class", [None])[0]
            
            # Map the class value to a rating
            rating_mapping = {
                'rating-s': 'General',
                'rating-q': 'Questionable',
                'rating-e': 'Explicit'
            }

            # Return the corresponding rating
            return rating_mapping.get(rating_class, None)
        
        return None
    
    def extract_post_id(self, soup):
        """
        Extracts the post ID from the parsed HTML document.

        Args:
            soup (BeautifulSoup): Parsed HTML document.

        Returns:
            str: The extracted post ID, or None if not found.
        """
        # Find the span element below #stats
        id_span = soup.select_one("#stats span")

        if id_span and id_span.text.startswith("Post ID:"):
            # Extract the text after "Post ID: "
            post_id = id_span.text.split("Post ID: ")[-1].strip()
            return post_id
    
        return None
    
    def extract_info(self, soup, selector):
        """
        Extracts the text after ': ' from the specified element.

        Args:
            soup (BeautifulSoup): Parsed HTML document.
            selector (str): CSS selector for the element.

        Returns:
            str: Extracted text, or None if not found.
        """
        element = soup.select_one(selector)
        if element:
            text = element.get_text().strip()
            return text.split(": ")[-1] if ": " in text else None
        return None

    def extract_source_url(self, soup, selector):
        """
        Extracts the href of the first <a> element inside the specified element.

        Args:
            soup (BeautifulSoup): Parsed HTML document.
            selector (str): CSS selector for the element.

        Returns:
            str: Extracted URL, or None if not found.
        """
        element = soup.select_one(selector)
        if element:
            link = element.find("a", href=True)
            if link:
                return link["href"]
        return None
    
    def extract_tags(self, soup, selector):
        """
        Extracts tags from the specified element.

        Args:
            soup (BeautifulSoup): Parsed HTML document.
            selector (str): CSS selector for the element.

        Returns:
            list: List of extracted tags.
        """
        tag_list = []
        tag_container = soup.select(selector)
        if tag_container:
            tag_list = [li.get_text().strip() for li in tag_container]
        return tag_list

    def download_image(self, image_url, image_name):
        """
        Downloads an image from the specified URL.

        Args:
            image_url (str): URL of the image to download.
            image_name (str): Name to save the downloaded image as.
        """
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            image_path = os.path.join(self.output_dir, image_name)
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"- Image saved: {image_name}")

    def save_metadata(self, image_name, metadata):
        """
        Saves metadata as a JSON file.

        Args:
            image_name (str): Name of the image file.
            metadata (dict): Metadata to save.
        """
        json_name = os.path.splitext(image_name)[0] + ".json"
        json_path = os.path.join(self.output_dir, 'labels', json_name)
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        print(f"- Metadata saved: {json_name}")

    def scrape_sankaku(self, pages=5):
        """
        Scrapes Sankaku Complex for a fixed number of pages.

        Args:
            pages (int, optional): Number of pages to scrape. Defaults to 5.
        """
        for tag in self.tags_list:
            self.cur_tag = tag
            if len(self.tags_list) > 1:
                self.output_dir = join(self.base_dir, self.data_name, self.cur_tag)
            else:
                self.output_dir = join(self.base_dir, self.data_name)
            os.makedirs(join(self.output_dir, 'labels'), exist_ok=True)
            self.page_num = 1
            self.clear_pages_count = 0
            self.scrape = True
            self.end_of_page = False

            self.search_url = f"{self.base_url}/en/posts?page={{page_num}}&tags={tag}"
            files = listdir(self.output_dir)
            header = f" \"{urllib.parse.unquote(tag.split('+')[0])}\" "
            print(f"\n{'='*((100-(len(header)))//2)}{header}{'='*((100-(len(header)))//2)}")
            if 'log.pkl' in files:
                self.collected_images, self.last_page = pkl.load(open(join(self.output_dir, 'log.pkl'), 'rb'))
                print("\n-- Log file found")
                print(f"-- Log last page: {self.last_page}")
            else:
                self.collected_images = []
                self.page_num = 1

            print(f"\n{'*'*100}")
                
            while self.page_num <= pages and not self.end_of_page:
                try:
                    self.scrape_page(max_images=float('inf'))
                    self.page_num += 1
                    print(f"\n{'*'*100}")
                except selenium.common.exceptions.TimeoutException:
                    print(f"Timeout occurred on page {self.page_num}. Restarting WebDriver.")
                    self.restart_webdriver()
                except requests.exceptions.ConnectTimeout:
                    print(f"Timeout occurred on page {self.page_num}. Restarting WebDriver.")
                    self.restart_webdriver()
                except TimeoutError:
                    print(f"Timeout occurred on page {self.page_num}. Restarting WebDriver.")
                    self.restart_webdriver()
                except KeyboardInterrupt:
                    self.scrape = False
                    break
            
            print(f"\n-- Scraping complete for tag \"{tag.split('+')[0]}\"")
            print(f"-- Total images collected: {len(self.collected_images)}")
            print(f"-- Last page: {self.page_num-1}")
            if not self.scrape: break
        print(f"\n{'='*100}")

    def scrape_sankaku_limited_by_images(self, max_images=10):
        """
        Scrapes Sankaku Complex with a limit on the number of images.

        Args:
            max_images (int, optional): Maximum number of images to scrape. Defaults to 10.
        """
        for tag in self.tags_list:
            self.cur_tag = tag
            if len(self.tags_list) > 1:
                self.output_dir = join(self.base_dir, self.data_name, self.cur_tag)
            else:
                self.output_dir = join(self.base_dir, self.data_name)
            os.makedirs(join(self.output_dir, 'labels'), exist_ok=True)
            self.page_num = 1
            self.clear_pages_count = 0
            self.scrape = True
            self.end_of_page = False

            self.search_url = f"{self.base_url}/en/posts?page={{page_num}}&tags={tag}"
            files = listdir(self.output_dir)
            header = f" \"{urllib.parse.unquote(tag.split('+')[0])}\" "
            print(f"\n{'='*((100-(len(header)))//2)}{header}{'='*((100-(len(header)))//2)}")
            if 'log.pkl' in files:
                self.collected_images, self.last_page = pkl.load(open(join(self.output_dir, 'log.pkl'), 'rb'))
                print("\n-- Log file found")
                print(f"-- Log last page: {self.last_page}")
            else:
                self.collected_images = []
                self.page_num = 1

            while len(self.collected_images) < max_images and not self.end_of_page:
                try:
                    self.scrape_page(max_images)
                    self.page_num += 1
                except selenium.common.exceptions.TimeoutException:
                    print(f"Timeout occurred on page {self.page_num}. Restarting WebDriver.")
                    self.restart_webdriver()
                except requests.exceptions.ConnectTimeout:
                    print(f"Timeout occurred on page {self.page_num}. Restarting WebDriver.")
                    self.restart_webdriver()
                except TimeoutError:
                    print(f"Timeout occurred on page {self.page_num}. Restarting WebDriver.")
                    self.restart_webdriver()
                except KeyboardInterrupt:
                    self.scrape = False
                    break

            print(f"\n-- Scraping complete for tag \"{tag.split('+')[0]}\"")
            print(f"-- Total images collected: {len(self.collected_images)}")
            print(f"-- Last page: {self.page_num-1}")
            pkl.dump([self.collected_images, self.page_num-1], open(join(self.output_dir, 'log.pkl'), 'wb'))
            if not self.scrape: break
        print(f"\n{'='*100}")

    def restart_webdriver(self):
        """
        Restarts the WebDriver.
        """
        # Close the current WebDriver
        self.driver.quit()
        time.sleep(5)  # Give some time before restarting
        # Reinitialize the WebDriver
        self.initialize_webdriver()

    def close(self):
        """
        Closes the WebDriver.
        """
        self.driver.quit()


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Sankaku Scraper")
    
    # Argument for data_name with default value None
    parser.add_argument(
        "--data_name", 
        type=str, 
        default=None, 
        help="The name of the data category to scrape (default: None)"
    )
    
    # Argument for tag with default value None
    parser.add_argument(
        "--tag", 
        type=str, 
        default=None, 
        help="A specific tag to scrape (default: None)"
    )
    
    # Argument for rating with default value None
    parser.add_argument(
        "--rating", 
        type=str, 
        default=None, 
        help="A specific rating to scrape (default: None)"
    )
    
    # Argument for rating with default value None
    parser.add_argument(
        "--base_dir", 
        type=str, 
        default='scraped_images', 
        help="Download directory (default: scraped_images)"
    )
    
    # Argument for rating with default value None
    parser.add_argument(
        "--max", 
        type=int, 
        default=99999, 
        help="Maximum number of images to scrape (default: 99999)"
    )
    
    # Boolean flag for sample image scraping
    parser.add_argument(
        "--sample", 
        action='store_true', 
        help="If set, scrape sample image (default: False)"
    )
    
    # Boolean flag for single character only scraping
    parser.add_argument(
        "--single_character", 
        action='store_true', 
        help="If set, scrape only 1 character (default: False)"
    )

    # Boolean flag for full image scraping
    parser.add_argument(
        "--no_ai", 
        action='store_true', 
        help="If set, don't scrape AI-created (default: False)"
    )

    # Boolean flag for full image scraping
    parser.add_argument(
        "--ai_only", 
        action='store_true', 
        help="If set, scrape only AI-created (default: False)"
    )
    
    # Boolean flag for single character only scraping
    parser.add_argument(
        "--with_video", 
        action='store_true', 
        help="If set, also download videos (default: False)"
    )
    
    # Boolean flag for single character only scraping
    parser.add_argument(
        "--video_only", 
        action='store_true', 
        help="If set, download videos only (default: False)"
    )


    args = parser.parse_args()

    # Extract arguments from command-line
    data_name = args.data_name
    tag = urllib.parse.quote(args.tag.replace(' ', '+'))
    rating = [i.lower() for i in args.rating.split(',')] if args.rating else None
    max_img = args.max
    full_image = not args.sample
    single_character = args.single_character
    no_ai = args.no_ai
    ai_only = args.ai_only
    base_dir = args.base_dir
    if args.with_video:
        video_flag = 1
    elif args.video_only:
        video_flag = 2
    else:
        video_flag = 0

    assert (no_ai and not ai_only) or (not no_ai and ai_only) or (not no_ai and not ai_only), 'Choose 1 between "no_ai" or "ai_only"'

    if data_name is not None:
        with open('gen_info.json', 'r') as file:
            # Load the JSON data into a dictionary
            tags = json.load(file)
        dir_name = data_name
    else:
        dir_name = f"sankaku_{args.tag.replace(' ', '+')}"
        if rating is not None: dir_name += f"_{rating}"
        # if full_image: dir_name += '_full'
        if not full_image: dir_name += '_sample'
        if single_character: dir_name += '_single-character'
        if video_flag == 1:
            dir_name += '_with-video'
        if video_flag == 2:
            dir_name += '_video-only'

        if no_ai: 
            dir_name += '/no_ai'
        elif ai_only: 
            dir_name += '/ai_only'

        # elif not no_ai and not ai_only: 
        #     dir_name += '/mixed'

        current_time = datetime.now()
        formatted_time = current_time.strftime('%y-%m-%d_%H-%M-%S')

        # dir_name += f'_{formatted_time}'

        data_name = args.tag.replace(' ', '+')
        tags = {args.tag.replace(' ', '+'): [args.tag.replace(' ', '+')]}
        
    # Create the scraper object
    scraper = SankakuScraper(data_name = dir_name,
                             tags = tags[data_name],
                             rating = rating,
                             full_image = full_image, 
                             single_character = single_character,
                             no_ai = no_ai,
                             ai_only = ai_only,
                             base_dir = base_dir,
                             video_flag = video_flag)
    
    # Scrape with a limit on the number of images for each tag
    scraper.scrape_sankaku_limited_by_images(max_images=max_img)  # Adjust max_images as needed
    
    # Alternatively, scrape a fixed number of pages for each tag
    # scraper.scrape_sankaku(pages=5)  # Adjust the number of pages to scrape as needed
    
    # Close the browser
    scraper.close()
