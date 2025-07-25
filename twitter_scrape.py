import requests
import os
import json
import time
from datetime import datetime, timedelta

# === CONFIGURATION ===
BEARER_TOKEN="AAAAAAAAAAAAAAAAAAAAAKv73AEAAAAAw8TnGr2LodTSfEs31iWaDfiqHDA%3DoU3YNfAxiPTdS6SfOlrPNhmeejB6Sr1oidIgQgqS3w29I7t3V5"
ACCESS_TOKEN="1948845042103451648-4YvZheklhD0DcZvAK3cD7a3jRomgEl"
ACCESS_TOKEN_SECRET="gqs5M4VwQdiVuFRHkLBvuEzDbvA1jRGp3mSjCEbbe3VvN"
USERNAME = "SpeakerPelosi"       
MAX_RESULTS = 100                  
LOG_FILE = f"{USERNAME}_tweets.jsonl"
END_TIME = datetime.now() + timedelta(hours=72) 
SLEEP_BETWEEN_PAGES = 60           

# === HEADERS ===
headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

def get_user_id(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    while True:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 429:
                print("[RATE LIMIT] Getting user ID. Sleeping 15 minutes...")
                time.sleep(15 * 60)
                continue
            response.raise_for_status()
            return response.json()["data"]["id"]
        except Exception as e:
            print(f"[ERROR] get_user_id: {e}")
            time.sleep(300)  # Retry in 5 minutes

def load_seen_ids():
    seen = set()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            for line in f:
                try:
                    seen.add(json.loads(line.strip())["id"])
                except:
                    continue
    return seen

def log_tweets(tweets, seen_ids):
    with open(LOG_FILE, "a") as f:
        for tweet in tweets:
            if tweet["id"] not in seen_ids:
                f.write(json.dumps(tweet) + "\n")
                seen_ids.add(tweet["id"])

def scrape_all_tweets(user_id):
    seen_ids = load_seen_ids()
    pagination_token = None
    page_count = 0

    while datetime.now() < END_TIME:
        url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        params = {
            "max_results": MAX_RESULTS,
            "tweet.fields": "created_at,id"
        }
        if pagination_token:
            params["pagination_token"] = pagination_token

        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 429:
                print("[RATE LIMIT] Sleeping 15 minutes...")
                time.sleep(15 * 60)
                continue

            response.raise_for_status()
            data = response.json()
            tweets = data.get("data", [])
            meta = data.get("meta", {})

            if not tweets:
                print(f"[{datetime.now().isoformat()}] No tweets returned. Stopping.")
                break

            new_count = sum(1 for t in tweets if t["id"] not in seen_ids)
            print(f"[{datetime.now().isoformat()}] Page {page_count + 1}: Retrieved {len(tweets)} tweets ({new_count} new)")
            log_tweets(tweets, seen_ids)

            pagination_token = meta.get("next_token")
            if not pagination_token:
                print("✅ Reached end of timeline (no next_token).")
                break

            page_count += 1
            time.sleep(SLEEP_BETWEEN_PAGES)

        except Exception as e:
            print(f"[ERROR] scrape_all_tweets: {e}")
            time.sleep(300)  # Wait 5 min and retry

    print(f"[DONE] Scraping completed after {page_count} pages.")

def main():
    print("[START] Ingestion started")
    user_id = get_user_id(USERNAME)
    scrape_all_tweets(user_id)
    print("[FINISH] Script exiting")

if __name__ == "__main__":
    main()
