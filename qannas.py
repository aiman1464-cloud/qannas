import csv, json, os, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import date

THRESHOLD = 40
GIVING_PCT = 10
UA = {"User-Agent": "Mozilla/5.0 Qannas"}

KEYWORDS = {
    "grant": 25, "prize": 25, "hackathon": 20, "free": 10, "bounty": 25,
    "freelance": 20, "contract": 15, "remote": 15, "pricing error": 30,
    "price error": 30, "mistake price": 30, "discount": 10, "tender": 25,
    "urgent": 10, "paid": 15, "reward": 15, "referral": 10,
    "منحة": 25, "جائزة": 25, "مناقصة": 25, "مطلوب": 15, "تخفيض": 10,
}
QUERIES = [
    "grant applications open", "hackathon prize", "pricing error deal",
    "bug bounty program new", "freelance project needed", "مناقصة جديدة",
]


def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=20).read()


def from_rss(url, source):
    out = []
    try:
        root = ET.fromstring(get(url))
        for it in root.iter("item"):
            out.append((source, (it.findtext("title") or "").strip(),
                        (it.findtext("link") or "").strip()))
    except Exception as e:
        print("فشل", source, e)
    return out


def remoteok():
    out = []
    try:
        for j in json.loads(get("https://remoteok.com/api"))[1:]:
            out.append(("RemoteOK", f'{j.get("position","")} - {j.get("company","")}',
                        j.get("url", "")))
    except Exception as e:
        print("فشل RemoteOK", e)
    return out


def collect():
    items = remoteok()
    items += from_rss("https://weworkremotely.com/remote-jobs.rss", "WWR")
    for q in QUERIES:
        u = "https://news.google.com/rss/search?q=" + urllib.parse.quote(q)
        items += from_rss(u, "Google:" + q)
    return items


def score(title):
    t = title.lower()
    return min(100, sum(w for k, w in KEYWORDS.items() if k in t))


def notify(text):
    token, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print(text)
        return
    data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{token
