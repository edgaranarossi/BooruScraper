import argparse
from danbooru_scraper import DanbooruScraper
from sankaku_scraper import SankakuScraper

def main():
    parser = argparse.ArgumentParser(description="BooruScraper")
    parser.add_argument('--site', choices=['danbooru', 'sankakucomplex'], required=True, help="The site to scrape")
    parser.add_argument('--tags', required=True, help="Tags to search for")
    parser.add_argument('--limit', type=int, default=100, help="Number of images to download")
    parser.add_argument('--rating', choices=['safe', 'questionable', 'explicit'], help="Filter images by rating")
    args = parser.parse_args()

    if args.site == 'danbooru':
        scraper = DanbooruScraper()
    elif args.site == 'sankakucomplex':
        scraper = SankakuScraper()

    scraper.scrape(tags=args.tags, limit=args.limit, rating=args.rating, output=args.output)

if __name__ == "__main__":
    main()
