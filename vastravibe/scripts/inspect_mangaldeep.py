with open(r'C:\Users\vedant patil\.gemini\antigravity-ide\brain\e4e8f1e7-56f7-4bbf-b9ec-33139bc9a075\.system_generated\steps\303\content.md', 'r', encoding='utf-8') as f:
    text = f.read()

from bs4 import BeautifulSoup
soup = BeautifulSoup(text, 'html.parser')

print('Title:', soup.title.string if soup.title else '')

# Navigation
nav = soup.find('header') or soup.find('nav')
print('\nHeader/Nav text preview:')
if nav:
    for a in nav.find_all('a'):
        txt = a.get_text(strip=True)
        href = a.get('href', '')
        if txt:
            print(f'  {txt} -> {href}')

# Headings / Sections
print('\nMain H1 / H2 Headings:')
for h in soup.find_all(['h1', 'h2', 'h3'])[:20]:
    print(f'  [{h.name}] {h.get_text(strip=True)}')

# Images / banners
print('\nKey Banner/Collection Images:')
for img in soup.find_all('img')[:15]:
    src = img.get('src') or img.get('data-src') or ''
    alt = img.get('alt', '')
    if 'logo' in src.lower() or 'banner' in src.lower() or 'collection' in src.lower() or alt:
        print(f'  IMG: {alt} -> {src[:80]}...')
