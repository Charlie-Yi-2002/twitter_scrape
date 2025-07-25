import requests
import os
import json
import time
from datetime import datetime, timedelta

BEARER_TOKEN="AAAAAAAAAAAAAAAAAAAAAKv73AEAAAAAw8TnGr2LodTSfEs31iWaDfiqHDA%3DoU3YNfAxiPTdS6SfOlrPNhmeejB6Sr1oidIgQgqS3w29I7t3V5"
ACCESS_TOKEN="1948845042103451648-4YvZheklhD0DcZvAK3cD7a3jRomgEl"
ACCESS_TOKEN_SECRET="gqs5M4VwQdiVuFRHkLBvuEzDbvA1jRGp3mSjCEbbe3VvN"
USERNAME = "realDonaldTrump"
LOG_FILE = f"{USERNAME}_tweets.jsonl"
MAX_RESULTS = 5
END_TIME = datetime.now() + timedelta(hours=72)



headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

def get_user_id(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()["data"]["id"]
    except Exception as e:
        print(f"[ERROR] Getting user ID failed: {e}")
        time.sleep(300)  # wait 5 min before retrying
        return get_user_id(username)

def get_user_tweets(user_id, max_results=MAX_RESULTS):
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {"max_results": max_results, "tweet.fields": "created_at,id"}
    try:
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 429:
            print("[RATE LIMIT] Sleeping 15 minutes")
            time.sleep(15 * 60)
            return []

        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        print(f"[ERROR] Fetching tweets failed: {e}")
        time.sleep(300)
        return []

def log_tweets(tweets):
    seen_ids = set()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            for line in f:
                try:
                    seen_ids.add(json.loads(line.strip())["id"])
                except:
                    continue

    with open(LOG_FILE, "a") as f:
        for tweet in tweets:
            if tweet["id"] not in seen_ids:
                f.write(json.dumps(tweet) + "\n")

def main():
    print("[START] Script running...")
    user_id = get_user_id(USERNAME)

    while datetime.now() < END_TIME:
        tweets = get_user_tweets(user_id)
        if tweets:
            print(f"[{datetime.now().isoformat()}] Retrieved {len(tweets)} new tweets")
            log_tweets(tweets)
        else:
            print(f"[{datetime.now().isoformat()}] No tweets or rate-limited")
        time.sleep(60)  # Poll once per minute

    print("[COMPLETE] Script ended after weekend window")

if __name__ == "__main__":
    main()