# -*- coding: utf-8 -*-
"""
scripts/generate_mock_data.py
Generates all mock CSV files and loads structured data into SQLite.
Called automatically by setup.py - can also be re-run standalone.
"""

import csv, random, sqlite3, os
from datetime import date, timedelta

random.seed(42)

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR  = os.path.join(BASE, "data", "csvs")
DB_PATH  = os.path.join(BASE, "data", "db", "insights.db")

os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

GENRES    = ["Action","Drama","Comedy","Sci-Fi","Thriller","Romance","Documentary"]
CITIES    = ["Mumbai","Delhi","Bangalore","Chennai","Hyderabad","Kolkata","Pune","Ahmedabad"]
PLATFORMS = ["Web","iOS","Android","Smart TV"]
REGIONS   = ["North","South","East","West","Central"]

MOVIES = [
    ("Stellar Run",      "Sci-Fi",      2024, 8.4, 45_000_000),
    ("Dark Orbit",       "Action",      2024, 7.9, 62_000_000),
    ("Last Kingdom",     "Drama",       2024, 8.1, 38_000_000),
    ("Laugh Riot",       "Comedy",      2025, 6.2, 15_000_000),
    ("Phantom Code",     "Thriller",    2025, 7.5, 29_000_000),
    ("Love in Monsoon",  "Romance",     2025, 7.8, 22_000_000),
    ("The Algorithm",    "Sci-Fi",      2025, 8.7, 55_000_000),
    ("City Beats",       "Documentary", 2025, 8.0, 10_000_000),
    ("Night Chase",      "Action",      2025, 7.2, 40_000_000),
    ("Comic Chaos",      "Comedy",      2025, 5.9, 12_000_000),
    ("Neon Dreams",      "Sci-Fi",      2025, 8.5, 48_000_000),
    ("Family First",     "Drama",       2025, 7.6, 30_000_000),
]

VIEWERS = [{
    "viewer_id":    f"V{str(i).zfill(5)}",
    "name":         f"User {i}",
    "city":         random.choice(CITIES),
    "age":          random.randint(18, 65),
    "platform":     random.choice(PLATFORMS),
    "subscription": random.choice(["Free","Standard","Premium"]),
    "joined_date":  str(date(2022,1,1) + timedelta(days=random.randint(0,900))),
} for i in range(1, 5001)]

def rand_date():
    start = date(2024,1,1)
    end   = date(2025,12,31)
    return str(start + timedelta(days=random.randint(0,(end-start).days)))

def write_csv(name, rows, fields):
    path = os.path.join(CSV_DIR, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"  OK  {name}  ({len(rows)} rows)")

# movies.csv
movie_rows = [{"movie_id":f"M{str(i+1).zfill(3)}","title":t,"genre":g,
               "release_year":y,"rating":r,"budget":b}
              for i,(t,g,y,r,b) in enumerate(MOVIES)]
write_csv("movies.csv", movie_rows, ["movie_id","title","genre","release_year","rating","budget"])

# viewers.csv
write_csv("viewers.csv", VIEWERS, ["viewer_id","name","city","age","platform","subscription","joined_date"])

# watch_activity.csv
watch_rows = []
for _ in range(20_000):
    m = random.choice(movie_rows); v = random.choice(VIEWERS)
    watch_rows.append({
        "activity_id":   f"A{str(len(watch_rows)+1).zfill(6)}",
        "viewer_id":     v["viewer_id"],
        "movie_id":      m["movie_id"],
        "watch_date":    rand_date(),
        "watch_minutes": random.randint(5, 145),
        "completed":     random.choice([True,False,True,True]),
        "device":        v["platform"],
    })
write_csv("watch_activity.csv", watch_rows,
          ["activity_id","viewer_id","movie_id","watch_date","watch_minutes","completed","device"])

# reviews.csv
review_rows = []
for movie in movie_rows:
    for _ in range(random.randint(80,200)):
        v = random.choice(VIEWERS)
        review_rows.append({
            "review_id":   f"R{str(len(review_rows)+1).zfill(5)}",
            "movie_id":    movie["movie_id"],
            "viewer_id":   v["viewer_id"],
            "score":       round(random.gauss(movie["rating"],1.2),1),
            "sentiment":   random.choices(["positive","neutral","negative"],[60,25,15])[0],
            "review_date": rand_date(),
        })
write_csv("reviews.csv", review_rows, ["review_id","movie_id","viewer_id","score","sentiment","review_date"])

# marketing_spend.csv
channels = ["Digital","OOH","TV","Influencer","Email"]
mkt_rows = []
for movie in movie_rows:
    for ch in channels:
        mkt_rows.append({
            "movie_id":       movie["movie_id"],
            "channel":        ch,
            "spend_inr":      random.randint(500_000, 10_000_000),
            "impressions":    random.randint(200_000, 5_000_000),
            "clicks":         random.randint(5_000, 200_000),
            "conversions":    random.randint(200, 10_000),
            "campaign_month": random.choice(["2024-Q3","2024-Q4","2025-Q1","2025-Q2"]),
        })
write_csv("marketing_spend.csv", mkt_rows,
          ["movie_id","channel","spend_inr","impressions","clicks","conversions","campaign_month"])

# regional_performance.csv
reg_rows = []
for movie in movie_rows:
    for region in REGIONS:
        reg_rows.append({
            "movie_id":      movie["movie_id"],
            "region":        region,
            "city":          random.choice(CITIES),
            "views":         random.randint(5_000, 300_000),
            "avg_watch_pct": round(random.uniform(0.4,0.95),2),
            "revenue_inr":   random.randint(100_000, 5_000_000),
            "month":         random.choice(["2025-03","2025-04","2025-05"]),
        })
write_csv("regional_performance.csv", reg_rows,
          ["movie_id","region","city","views","avg_watch_pct","revenue_inr","month"])

# ── Load into SQLite ──────────────────────────────────────────────────
print(f"\n  Loading into SQLite -> {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
conn.executescript("""
CREATE TABLE IF NOT EXISTS movies (
    movie_id TEXT PRIMARY KEY, title TEXT, genre TEXT,
    release_year INTEGER, rating REAL, budget INTEGER);
CREATE TABLE IF NOT EXISTS viewers (
    viewer_id TEXT PRIMARY KEY, name TEXT, city TEXT,
    age INTEGER, platform TEXT, subscription TEXT, joined_date TEXT);
CREATE TABLE IF NOT EXISTS watch_activity (
    activity_id TEXT PRIMARY KEY, viewer_id TEXT, movie_id TEXT,
    watch_date TEXT, watch_minutes INTEGER, completed INTEGER, device TEXT);
CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY, movie_id TEXT, viewer_id TEXT,
    score REAL, sentiment TEXT, review_date TEXT);
""")

def load_table(table, csv_name, fields):
    path = os.path.join(CSV_DIR, csv_name)
    with open(path) as f:
        rows = list(csv.DictReader(f))
    ph = ",".join("?"*len(fields)); cols = ",".join(fields)
    conn.executemany(
        f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({ph})",
        [tuple(r[c] for c in fields) for r in rows])
    print(f"  OK  {table} ({len(rows)} rows)")

load_table("movies",         "movies.csv",        ["movie_id","title","genre","release_year","rating","budget"])
load_table("viewers",        "viewers.csv",        ["viewer_id","name","city","age","platform","subscription","joined_date"])
load_table("watch_activity", "watch_activity.csv", ["activity_id","viewer_id","movie_id","watch_date","watch_minutes","completed","device"])
load_table("reviews",        "reviews.csv",        ["review_id","movie_id","viewer_id","score","sentiment","review_date"])
conn.commit(); conn.close()
print("\n  All data generated and loaded successfully.")
