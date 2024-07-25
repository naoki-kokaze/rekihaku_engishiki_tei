from bs4 import BeautifulSoup as BS

vol = input('英訳の巻数は?\n')
output_filename = f'engishiki_v{vol}_en.xml'

f_input = open(f'../TEI編集用/{output_filename}', 'rb')
soup = BS(f_input, 'xml')
f_input.close()

paragraphs = soup.select('p[ana]')

for p in paragraphs:
    segs = p.select('seg')
    for index, seg in enumerate(segs):
        seg_id = 'footnote' + p["xml:id"][4:] + str(index + 1).zfill(2)
        seg["xml:id"] = seg_id

f_output = open(f'../途中生成物/segID_{output_filename}', 'w', encoding='utf-8')
f_output.write(str(soup))
f_output.close()
