# 巻5・17のメタデータ（巻・式名・式順・条番号・新条文名）を取得する

import bs4, csv

n = input('巻数は?\n')
f_input = open(f'metadata_v{n}.tsv', 'r', encoding='utf-8')
reader = csv.DictReader(f_input, delimiter='\t')
#f_input.close()

l = [row for row in reader]
print(l)

