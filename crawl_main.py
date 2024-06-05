from functions import crawl_index_page
from settings import START_URL


def main():
    try:
        crawl_index_page(START_URL)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
