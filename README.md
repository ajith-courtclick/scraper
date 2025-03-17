# Web Scraping Framework

A robust and scalable web scraping framework built with Python, supporting MySQL database, proxy rotation, and rate limiting.

## Features

- Robust request handling with retry logic and rate limiting
- MySQL database integration
- Proxy rotation capability
- CAPTCHA handling support
- Parallel processing with Dask
- Comprehensive logging
- User agent rotation
- Progress tracking for bulk scraping

## Prerequisites

- Python 3.8+
- MySQL Server

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd scraper
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```env
# Database Settings
DB_HOST=localhost
DB_PORT=3306
DB_NAME=scraper_db
DB_USER=root
DB_PASSWORD=your_password

# Proxy Settings
PROXY_ENABLED=False
PROXY_API_KEY=your_proxy_api_key
```

## Project Structure

```
scraper/
├── config/
│   └── settings.py
├── src/
│   ├── base_scraper.py
│   └── database.py
├── data/
├── logs/
└── requirements.txt
```

## Usage

1. Create a new scraper by inheriting from the BaseScraper class:

```python
from src.base_scraper import BaseScraper
from src.database import DatabaseHandler

class MyScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.db = DatabaseHandler()
        
    def parse_page(self, response):
        # Implement your parsing logic here
        soup = self.parse_html(response.text)
        # Extract data
        return data
        
    def run(self, urls):
        # Connect to database
        self.db.connect()
        
        # Scrape data
        results = self.scrape_urls(urls, self.parse_page)
        
        # Store results
        self.db.insert_data('my_table', results)
        
        # Close connection
        self.db.close_connection()
```

2. Run your scraper:

```python
scraper = MyScraper()
urls = ['https://example.com/page1', 'https://example.com/page2']
scraper.run(urls)
```

## Best Practices

1. **Rate Limiting**: Respect websites' robots.txt and implement appropriate delays between requests.
2. **Error Handling**: Always implement proper error handling and logging.
3. **Data Validation**: Validate and clean scraped data before storage.
4. **Proxy Usage**: Use rotating proxies for large-scale scraping to avoid IP bans.
5. **Session Management**: Reuse sessions when possible to reduce overhead.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 