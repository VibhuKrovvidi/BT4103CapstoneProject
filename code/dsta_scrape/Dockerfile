FROM python:3.7.3-stretch
WORKDIR /scrape
COPY requirements.txt /scrape
COPY . /scrape
RUN pip install -r requirements.txt

EXPOSE 5000
CMD python dsta_scraper.py