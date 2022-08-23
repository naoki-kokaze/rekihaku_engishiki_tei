from bs4 import BeautifulSoup as BS

vol = input('巻数は?\n')
output_filename = f'engishiki_v{vol}.xml'

f_input = open(f'../TEI files/{output_filename}', 'rb')
soup = BS(f_input, 'xml')
f_input.close()

paragraphs = soup.select('p[ana]')

for p in paragraphs:
    anchors = p.select('anchor')
    for index, anchor in enumerate(anchors):
        anchor_id = 'app' + p["xml:id"][4:] + str((index // 2) + 1).zfill(2)
        if index % 2 == 0:
            anchor["xml:id"] = anchor_id
        else:
            anchor["xml:id"] = anchor_id + 'e'

f_output = open(f'../途中生成物/appID_{output_filename}', 'w', encoding='utf-8')
f_output.write(str(soup))
f_output.close()
