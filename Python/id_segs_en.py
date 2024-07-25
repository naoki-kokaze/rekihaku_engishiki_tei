from bs4 import BeautifulSoup as BS

vol = input('英訳の巻数は?\n')
output_filename = f'engishiki_v{vol}_en.xml'

f_input = open(f'../TEI編集用/{output_filename}', 'rb')
soup = BS(f_input, 'xml')
f_input.close()

articles = soup.select('div[type="条"]')

for article in articles:
    note_tag = article.find('note')
    p_tag = article.find('p')    
    
    note_segs = note_tag.select('seg')
    p_segs = p_tag.select('seg')

    for index, note_seg in enumerate(note_segs):
        note_seg_id = 'footnote' + article["xml:id"][7:] + '00' + str(index + 1).zfill(2)
        note_seg["xml:id"] = note_seg_id

    for index, p_seg in enumerate(p_segs):
        p_seg_id = 'footnote' + p_tag["xml:id"][4:] + str(index + 1).zfill(2)
        p_seg["xml:id"] = p_seg_id

f_output = open(f'../途中生成物/segID_{output_filename}', 'w', encoding='utf-8')
f_output.write(str(soup))
f_output.close()
