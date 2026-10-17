import urllib.request
from bs4 import BeautifulSoup
import json

url = 'https://mangaldeep.co.in/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')

soup = BeautifulSoup(html, 'html.parser')

data = {}

# Title
data['title'] = soup.title.string if soup.title else ''

# Announcement
ann = soup.find(class_=lambda x: x and 'announcement' in x)
data['announcement'] = ann.get_text(separator=' ', strip=True) if ann else ''

# Navigation
nav = soup.find('header') or soup.find('nav')
nav_items = []
if nav:
    for a in nav.find_all('a'):
        t = a.get_text(strip=True)
        h = a.get('href', '')
        if t and len(t) < 50:
            nav_items.append({'text': t, 'href': h})
data['nav_items'] = nav_items

# Headings
data['headings'] = []
for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
    txt = h.get_text(strip=True)
    if txt:
        data['headings'].append({'level': h.name, 'text': txt})

# Banners / Sliders / Promo Cards
data['banners'] = []
for img in soup.find_all('img'):
    src = img.get('src') or img.get('data-src') or ''
    alt = img.get('alt', '')
    if any(k in src.lower() or k in alt.lower() for k in ['banner', 'hero', 'slide', 'collection', 'promo']):
        data['banners'].append({'alt': alt, 'src': src})

# Collections listed on homepage
collections = []
for el in soup.find_all(class_=lambda x: x and ('collection' in x.lower() or 'category' in x.lower() or 'card' in x.lower())):
    txt = el.get_text(separator=' ', strip=True)
    if txt and len(txt) < 80 and txt not in [c['text'] for c in collections]:
        collections.append({'class': el.get('class'), 'text': txt})
data['collections'] = collections[:30]

with open('scripts/mangaldeep_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Analysis written to scripts/mangaldeep_analysis.json')
