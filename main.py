from seed_generator import generate_seed_urls


def main():
    keywords = ['politics', 'technology']
    categories = ['politics', 'tech']
    result = generate_seed_urls(keywords, categories=categories, region='US')
    for url in result['urls']:
        print(url)


if __name__ == '__main__':
    main()
