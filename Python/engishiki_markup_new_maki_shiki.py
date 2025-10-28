from bs4 import BeautifulSoup as BS
import csv

# ユーザー入力
file_volume = input('読み込む巻を入力してください: ')
input_filename = f'../vol_metadata/metadata_v{file_volume}.tsv'
lang_choice = input('ファイルの種別はどれですか（校訂文→何も入力しない、英訳→_en、現代語訳→_ja）: ')
add_shiki_order = input('式順をn属性に含めますか？（はい→y、いいえ→n）: ').lower() == 'y'  # ← ユーザー選択を追加

# ヘッダー生成関数
def generate_TEIheader(output_filename, lang_choice):
    with open(output_filename, 'w', encoding='utf-8') as output_file:
        with open(f'../TEI編集用/engishiki_header{lang_choice}.xml', 'r', encoding='utf-8') as header_file:
            output_file.write(header_file.read())
    print('TEIヘッダー情報書き込み完了')

# corresp属性リスト作成関数
def lang_corresp(lang_choice, file_volume):
    lang_list = ["", "_en", "_ja"]
    return [f"engishiki_v{file_volume}{lang}.xml" for lang in lang_list if lang != lang_choice]

corresp_list = lang_corresp(lang_choice, file_volume)
output_filename = f'../途中生成物/engishiki_v{file_volume}{lang_choice}.xml'

generate_TEIheader(output_filename, lang_choice)

# XMLベース構築
soup = BS(open(output_filename, 'r', encoding='utf-8'), 'xml')
root = soup.TEI
t_text = soup.new_tag("text")
t_body = soup.new_tag('body')
root.append(t_text)
t_text.append(t_body)

# TSV読み込み
with open(input_filename, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    metadata = [row for row in reader]

shiki_name = metadata[0]['式名']
shiki_no = metadata[0]['巻']
shiki_order = metadata[0]['式順']
shiki_order_id = f"{shiki_no.zfill(2)}{shiki_order}"
protocol_id = f"protocol{shiki_order_id}"

# `n`属性のベース設定関数（式順を含めるかどうかで変化）
def make_n_attr(shiki_no, shiki_order, jyou=None):
    if add_shiki_order:
        if jyou:
            return f"{shiki_no}-{shiki_order}.{jyou}"
        else:
            return f"{shiki_no}-{shiki_order}"
    else:
        if jyou:
            return f"{shiki_no}.{jyou}"
        else:
            return shiki_no

# 巻div生成
t_div_maki = soup.new_tag('div', **{
    "ana": shiki_name,
    "xml:id": f"volume{shiki_no}",
    "n": shiki_no,
    "type": "巻",
})
t_body.append(t_div_maki)

# 子要素div生成
t_div_shudai = soup.new_tag('div', **{"type": "首題", "xml:id": f"shudai{shiki_no.zfill(2)}"})
t_div_shudai.append(soup.new_tag('p', **{"xml:id": f"shudai{shiki_no.zfill(2)}01"}))
t_div_shudai.p.string = "首題"

# 式div生成（ここで@nを関数で制御）
t_div_shiki = soup.new_tag('div', **{
    "ana": shiki_name,
    "xml:id": protocol_id,
    "n": make_n_attr(shiki_no, shiki_order),
    "type": "式",
    "corresp": f"{corresp_list[0]}#{protocol_id} {corresp_list[1]}#{protocol_id}"
})

t_div_shikidai = soup.new_tag('div', **{"type": "式題", "xml:id": f"shikidai{shiki_order_id}"})
t_div_shikidai.append(soup.new_tag('p', **{"xml:id": f"shikidai{shiki_order_id}01"}))
t_div_shikidai.p.string = "式題"

t_div_bidai = soup.new_tag('div', **{"type": "尾題", "xml:id": f"bidai{shiki_no.zfill(2)}"})
t_div_bidai.append(soup.new_tag('p', **{"xml:id": f"bidai{shiki_no.zfill(2)}01"}))
t_div_bidai.p.string = "尾題"

t_div_okugaki = soup.new_tag('div', **{"type": "本奥書", "xml:id": f"okugaki{shiki_no.zfill(2)}"})
t_div_okugaki.append(soup.new_tag('p', **{"xml:id": f"okugaki{shiki_no.zfill(2)}01"}))
t_div_okugaki.p.string = "本奥書"

# 挿入
t_div_maki.append(t_div_shudai)
t_div_maki.append(t_div_shiki)
t_div_shiki.append(t_div_shikidai)
t_div_maki.append(t_div_bidai)
t_div_maki.append(t_div_okugaki)

# 条・項をループ処理で生成
for data in metadata:
    jyou = data['条']
    article_id = f"article{shiki_order_id[-3:]}{jyou.zfill(3)}"
    t_div_article = soup.new_tag('div', **{
        "ana": shiki_name,
        "xml:id": article_id,
        "n": make_n_attr(shiki_no, shiki_order, jyou),  # ← 式順あり/なしを切り替え
        "type": "条",
        "corresp": f"{corresp_list[0]}#{article_id} {corresp_list[1]}#{article_id}"
    })
    t_div_article.append(soup.new_tag('head', ana=data["新条文名"]))

    if lang_choice != "":
        t_div_article.append(soup.new_tag('note', **{"type": "summary"}))

    for kou in range(int(data["項"])):
        item_id = f"item{article_id[-6:]}{str(kou+1).zfill(2)}"
        t_div_article.append(soup.new_tag('p', **{
            "ana": "項",
            "xml:id": item_id,
            "corresp": f"{corresp_list[0]}#{item_id} {corresp_list[1]}#{item_id}"
        }))

    t_div_shiki.append(t_div_article)

# 本文挿入
for item in soup.select('p[ana="項"]'):
    item.append('本文')

if lang_choice:
    for summary in soup.select('note[type="summary"]'):
        summary.append('条文概要')

# 整形出力
with open(output_filename, 'w', encoding='utf-8') as result:
    result.write(soup.prettify().replace('    ', '      '))

print("XMLファイル生成が完了しました。")
