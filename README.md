# BooruScraper

## Introduction
BooruScraper is a tool designed to scrape images from various Booru-style image boards. It allows users to download images based on tags and other criteria.

## Features
- Supports Danbooru and SankakuComplex
- Download images based on tags
- Filter images by rating and other metadata
- Command-line interface for easy usage

## Installation
To use BooruScraper, clone the repository and install the dependencies:
```bash
git clone https://github.com/yourusername/BooruScraper.git
cd BooruScraper
pip install -r requirements.txt
```

## Usage
To scrape Danbooru, run the following command:
```bash
python danbooru_scraper.py --tags "tag1 tag2" --limit 100
```
Replace `tag1` and `tag2` with the tags you want to search for, and `100` with the number of images you want to download.

To scrape SankakuComplex, run the following command:
```bash
python sankaku_scraper.py --tags "tag1 tag2" --limit 100
```
Replace `tag1` and `tag2` with the tags you want to search for, and `100` with the number of images you want to download.

## License
This project is licensed under the MIT License. See the LICENSE file for details.