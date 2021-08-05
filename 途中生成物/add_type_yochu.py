# 巻5・17の標注（index noteと訳す）にtype属性を付与する

import bs4, re

f_input = open(f'engishiki_v5_17.xml', 'rb')
soup = bs4.BeautifulSoup(f_input, 'xml')
f_input.close()

lems = soup.select('lem')
index_notes = []
index_patterns = re.compile(r"[「」弘イ貞延]+")

for lem in lems:
    if index_patterns.search(lem.text):
        index_notes.append(lem)

for note in index_notes:
    note.parent['type'] = '標注'

f_output = open(f'new_engishiki_v5_17.xml', 'w', encoding='utf-8')
f_output.write(str(soup))
f_output.close()
