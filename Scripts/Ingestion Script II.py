import os
import time
import requests
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv(override=True)

API_KEY = os.getenv("API_KEY")  # confirm this matches the exact casing in your .env file
URL = "https://api.hasdata.com/scrape/zillow/listing"
HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY,
}


def get_listings(zipcode, listing_type="forSale", page=1):
    params = {
        "keyword": zipcode,   # zip code, city, or address all work here
        "type": listing_type,  # forSale | forRent | sold
        "page": page,
    }
    resp = requests.get(URL, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()


def get_all_listings(zipcode, listing_type="forSale", max_pages=20):
    """Pull every page of results for a given zip code."""
    all_listings = []
    page = 1
    while page <= max_pages:
        data = get_listings(zipcode, listing_type=listing_type, page=page)
        # First run: print(data.keys()) to confirm the real key name
        listings = data.get("properties") or data.get("listings") or []
        if not listings:
            break
        all_listings.extend(listings)
        page += 1
        time.sleep(0.5)  # small delay to avoid hammering the API / hitting rate limits
    return all_listings


def get_listings_for_zipcodes(zipcodes, listing_type="forSale", max_pages=20, delay_between_zips=1.0):
    """Pull listings for multiple zip codes. Returns a dict: {zipcode: [listings]}."""
    results = {}
    for i, zipcode in enumerate(zipcodes):
        print(f"Fetching zip {zipcode} ({i + 1}/{len(zipcodes)})...")
        try:
            listings = get_all_listings(zipcode, listing_type=listing_type, max_pages=max_pages)
        except requests.HTTPError as e:
            print(f"  Failed on {zipcode}: {e}")
            listings = []
        print(f"  Got {len(listings)} listings for {zipcode}")
        results[zipcode] = listings
        if i < len(zipcodes) - 1:
            time.sleep(delay_between_zips)  # extra courtesy delay between zip codes
    return results


def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("dbname"),
        user=os.getenv("dbuser"),       # avoid bare "user"/"password" as var names
        password=os.getenv("dbpassword"),
        host=os.getenv("host"),
        port=os.getenv("port"),
    )


def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS housing_raw_data (
                id SERIAL PRIMARY KEY,
                housing_data JSONB
            )
        """)
    conn.commit()


def store_housing_data(conn, listings):
    """Insert a list of listing dicts using a single open connection.
    Tags each row with the zipcode it came from (if provided).
    """
    with conn.cursor() as cur:
        for listing in listings:
            cur.execute(
                "INSERT INTO housing_raw_data (housing_data) VALUES (%s)",
                (Json(listing),)
            )
    conn.commit()


if __name__ == "__main__":
    # Add as many zip codes as you want here
    ZIPCODES = [ "14150", "14223","14217"]

    zip_results = get_listings_for_zipcodes(ZIPCODES)

    conn = get_db_connection()
    try:
        ensure_table(conn)
        total = 0
        for zipcode, listings in zip_results.items():
            store_housing_data(conn, listings)
            total += len(listings)
            print(f"Stored {len(listings)} listings for {zipcode}.")
        print(f"Done. Stored {total} listings total across {len(ZIPCODES)} zip codes.")
    finally:
        conn.close()