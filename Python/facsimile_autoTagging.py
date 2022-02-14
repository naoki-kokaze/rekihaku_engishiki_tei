from bs4 import BeautifulSoup as BS
import json

vol = input('巻数は?\n')
output_filename = f'engishiki_v{vol}.xml'

f_input = open(output_filename, 'rb')
soup = BS(f_input, 'xml')
f_input.close()

# BS4のnew_tag()メソッドやappend()メソッドを用いる
"""構造は以下の通り
</text>
<facsimile source="https://khirin-
a.rekihaku.ac.jp/iiif/rekihaku/H-743-74-17/manifest.json">
  <surface
source="https://khirin-a.rekihaku.ac.jp/iiif/2/engishiki%2FH-743-74-17/page4404" xml:id="page4404">
    <graphic
url="https://khirin-a.rekihaku.ac.jp/iiif/2/engishiki%2FH-743-74-17%2F00001.tif/full/full/0/default.jpg"/>
  </surface>
<surface
source="https://khirin-a.rekihaku.ac.jp/iiif/2/engishiki%2FH-743-74-17/page4405" xml:id="page4405">
    <graphic
url="https://khirin-a.rekihaku.ac.jp/iiif/2/engishiki%2FH-743-74-17%2F00002.tif/full/full/0/default.jpg"/>
  </surface>
</facsimile>
</TEI>
"""
# cf. https://github.com/KU-ORCAS/manyoshuTEI/blob/main/manyo_hirose_v02_85_140a.xml


f_output = open(output_filename, 'w', encoding='utf-8')
f_output.write(str(soup))
f_output.close()
