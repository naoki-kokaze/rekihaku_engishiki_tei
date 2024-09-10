from bs4 import BeautifulSoup as BS
import csv


#作業者が適切なディレクトリを指定する

file_volume = input('読み込む巻を入力してください\n')

input_filename = f'../vol_metadata/metadata_v{file_volume}.tsv'

lang_choice = input('ファイルの種別はどれですか（校訂文→何も入力しない、英訳→_en、現代語訳→_ja）\n')



def generate_TEIheader(output_filename, lang_choice):
    """ヘッダーの記述。校訂文・現代語訳・英訳それぞれのひな形ヘッダーから転記。各ひな形は、マスターファイルのengishiki_header_all.xmlから転記"""
    with open(output_filename, 'w', encoding='utf-8') as output_file:
        with open(f'../TEI編集用/engishiki_header{lang_choice}.xml', 'r', encoding='utf-8') as header_file:
            output_file.write(header_file.read())
    print('TEIヘッダー情報書き込み完了')


# パラレルコーパス用の@corresp属性値をファイルの種別で分けてリストで出力する関数
def lang_corresp(lang_choice, file_volume):
    lang_list = ["", "_en", "_ja"]
    corresp_list = []
    for index, lang in enumerate(lang_list):
        if index != lang_list.index(lang_choice):
            corresp_list.append(f"engishiki_v{file_volume}{lang}.xml")

    return corresp_list

corresp_list = lang_corresp(lang_choice, file_volume)
output_filename = f'../途中生成物/engishiki_v{file_volume}{lang_choice}.xml'


# headerを書き込む
generate_TEIheader(output_filename, lang_choice)
result = open(output_filename, 'r', encoding='utf-8')
soup = BS(result, 'xml')

# <teiHeader>の後、<text><body></text>タグを挿入
root = soup.TEI
t_text = soup.new_tag("text")
t_body = soup.new_tag('body')
root.append(t_text)
t_text.append(t_body)

# https://note.nkmk.me/python-csv-reader-writer/
# CSVリーダーで見出し行のカラム名をキーとする順序付き辞書を取得し、巻のメタデータをリストとして保持
f = open(input_filename, 'r', encoding='utf-8')
reader = csv.DictReader(f, delimiter='\t')
metadata = [row for row in reader]
f.close()
shiki_name = metadata[0]['式名']
shiki_no = metadata[0]['巻']
shiki_order = metadata[0]['式順']

### 全体構造について確認 ###
# 最上位はdivタグのtype="巻"
# その子要素にdivが4つ、それぞれtype="首題", "式名", "尾題", "本奥書"
# type="式名"のdivタグの子要素には、type="式題"のdivがあり、その兄弟要素として本文が条数分だけある

### 参考情報 ###
# BSでxml:id属性値を与える方法について。https://zenn.dev/nakamura196/articles/ed3c614b08b0c4
# https://stackoverflow.com/questions/38379451/using-beautiful-soup-to-create-new-tag-with-attribute-named-name


### メインの処理 ###
# 最上位のdivタグから生成
t_div_maki = soup.new_tag('div', **{"ana":f"{shiki_name}", "xml:id":f"volume{shiki_no}", "n":f"{shiki_no}", "type":"巻", "subtype":"式"})
t_body.append(t_div_maki)

# 5つのdivタグ（首題・式・式題・尾題・本奥書）をその子要素に。それぞれ変数名で区別できるように
shiki_order_id = f"{shiki_no.zfill(2)}{shiki_order}"
t_div_shudai = soup.new_tag('div', **{"type":"首題", "xml:id":f"shudai{shiki_no.zfill(2)}"})
protocol_id = f'protocol{shiki_order_id}'
t_div_shiki = soup.new_tag('div', **{"ana":f"{shiki_name}", "xml:id":f"{protocol_id}", "n":f"{shiki_no}", "type":"式", "subtype":"条", "corresp":f"{corresp_list[0]}#{protocol_id} {corresp_list[1]}#{protocol_id}"})
t_div_shikidai = soup.new_tag('div', **{"type":"式題", "xml:id":f"shikidai{shiki_order_id}"})
t_div_bidai = soup.new_tag('div', **{"type":"尾題", "xml:id":f"bidai{shiki_no.zfill(2)}"})
t_div_okugaki = soup.new_tag('div', **{"type":"本奥書", "xml:id":f"okugaki{shiki_no.zfill(2)}"})

# 首題のdivタグを最上位の子要素にし、自身の子要素にpタグと文字列を挿入。尾題と本奥書についても同様
t_div_maki.append(t_div_shudai)
t_div_shudai.append(soup.new_tag('p', **{"xml:id":f"shudai{shiki_no.zfill(2)}01"}))
t_div_shudai.p.string = '首題'

# 本文を格納する式タグを生成
t_div_maki.append(t_div_shiki)

# 式タグの子要素に、式題のdivタグを挿入
t_div_shiki.append(t_div_shikidai)
t_div_shikidai.append(soup.new_tag('p', **{"xml:id":f"shikidai{shiki_order_id}01"}))
t_div_shikidai.p.string = '式題'

# 尾題
t_div_maki.append(t_div_bidai)
t_div_bidai.append(soup.new_tag('p', **{"xml:id":f"bidai{shiki_no.zfill(2)}01"}))
t_div_bidai.p.string = '尾題'

# 本奥書
t_div_maki.append(t_div_okugaki)
t_div_okugaki.append(soup.new_tag('p', **{"xml:id":f"okugaki{shiki_no.zfill(2)}01"}))
t_div_okugaki.p.string = '本奥書'

### メインの式タグの中身を格納していく
# 条数分だけdivタグを生成する必要があるので、上記で定義した巻のmetadataのリストをすべてforループ
for data in metadata:
    article_id = f'article{protocol_id[-3:]}{data["条"].zfill(3)}'
    t_div_shiki.append(soup.new_tag('div', **{"ana":f"{shiki_name}", "xml:id":f"{article_id}", "n":f"{shiki_no}.{data['条']}", "type":"条", "subtype":"項", "corresp":f"{corresp_list[0]}#{article_id} {corresp_list[1]}#{article_id}"}))
    # ポイントは、ここで末尾のdivを指定しないといけないこと。以下、同様
    t_div_shiki.select('div')[-1].append(soup.new_tag('head', ana=f'{data["新条文名"]}'))
    if lang_choice != "":
        t_div_shiki.select('div')[-1].append(soup.new_tag('note', **{"type":"summary"}))
    
    # 次に、項数文だけpタグを追加
    kous = int(data["項"])
    for kou in range(kous):
        item_id = f'item{article_id[-6:]}{str(kou+1).zfill(2)}'
        t_div_shiki.select('div')[-1].append(soup.new_tag('p', **{"ana":"項", "xml:id":f"{item_id}", "corresp":f"{corresp_list[0]}#{item_id} {corresp_list[1]}#{item_id}"}))
        # t_div_shiki.select('div')[-1].p.string = "本文"

# 項の本文がうまく書き込まれないので、生成したあとに追加する
items = soup.select('p[ana="項"]')
for item in items:
    item.append('本文')

if lang_choice != "":
    summaries = soup.select('note[type="summary"]')
    for summary in summaries:
        summary.append('条文概要')

# すべての結果の書き込み
result = open(output_filename, 'w', encoding='utf-8')
result.write(str(soup))
result.close()




