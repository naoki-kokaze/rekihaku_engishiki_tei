from bs4 import BeautifulSoup as BS
import csv

def generate_TEIheader(output_filename, header_file_path):
    with open(output_filename, 'w', encoding='utf-8') as output_file:
        with open(header_file_path, 'r', encoding='utf-8') as header_file:
            output_file.write(header_file.read())
    print('TEIヘッダー情報書き込み完了')

def lang_corresp(lang_choice, file_volume):
    lang_list = ["", "_en", "_ja"]
    return [f"engishiki_v{file_volume}{lang}.xml" for lang in lang_list if lang != lang_choice]

def make_n_attr(shiki_no, shiki_order, jyou=None, add_shiki_order=False):
    if add_shiki_order:
        return f"{shiki_no}-{shiki_order}.{jyou}" if jyou else f"{shiki_no}-{shiki_order}"
    else:
        return f"{shiki_no}.{jyou}" if jyou else shiki_no

def reset_text_body(soup):
    """<text> を全削除し、新しい <text><body> を作り、body を返す"""
    root = soup.TEI

    # 既存 text 削除
    for old_text in soup.find_all("text"):
        old_text.decompose()

    # 新しい text/body 生成
    t_text = soup.new_tag("text")
    t_body = soup.new_tag("body")
    t_text.append(t_body)
    root.append(t_text)

    return t_body

def handle_fanrei_mode(file_volume):
    output_filename = f'../途中生成物/engishiki_v{file_volume}_header.xml'
    header_file_path = '../TEI編集用/engishiki_header.xml'  # 校訂文ヘッダーを流用

    generate_TEIheader(output_filename, header_file_path)
    soup = BS(open(output_filename, 'r', encoding='utf-8'), 'xml')

    t_body = reset_text_body(soup)

    # <div><p/></div> の追加
    t_div = soup.new_tag("div")
    t_p = soup.new_tag("p")
    t_body.append(t_p)

    # 整形して書き込み
    with open(output_filename, 'w', encoding='utf-8') as result:
        result.write(soup.prettify())

    print("凡例ファイルのXML生成が完了しました。")

def handle_honbun_mode(file_volume):
    input_filename = f'../vol_metadata/metadata_v{file_volume}.tsv'
    lang_choice = input('ファイルの種別（校訂文→[Enter]、英訳→_en、現代語訳→_ja）: ')
    add_shiki_order = input('式順をn属性に含めますか？（はい→y、いいえ→n）: ').lower() == 'y'
    output_filename = f'../途中生成物/engishiki_v{file_volume}{lang_choice}.xml'
    header_file_path = f'../TEI編集用/engishiki_header{lang_choice}.xml'

    generate_TEIheader(output_filename, header_file_path)
    soup = BS(open(output_filename, 'r', encoding='utf-8'), 'xml')

    t_body = reset_text_body(soup)

    with open(input_filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        metadata = [row for row in reader]

    shiki_name = metadata[0]['式名']
    shiki_no = metadata[0]['巻']
    shiki_order = metadata[0]['式順']
    shiki_order_id = f"{shiki_no.zfill(2)}{shiki_order}"
    protocol_id = f"protocol{shiki_order_id}"
    corresp_list = lang_corresp(lang_choice, file_volume)

    # 巻・首題・式div
    t_div_maki = soup.new_tag('div', ana=shiki_name, **{
        "xml:id": f"volume{shiki_no}", "n": shiki_no, "type": "巻"})
    t_body.append(t_div_maki)

    t_div_shudai = soup.new_tag('div', type="首題", **{"xml:id": f"shudai{shiki_no.zfill(2)}"})
    t_div_shudai.append(soup.new_tag('p', **{"xml:id": f"shudai{shiki_no.zfill(2)}01"}))
    t_div_shudai.p.string = "首題"

    t_div_shiki = soup.new_tag('div', ana=shiki_name, **{
        "xml:id": protocol_id,
        "n": make_n_attr(shiki_no, shiki_order, add_shiki_order=add_shiki_order),
        "type": "式",
        "corresp": f"{corresp_list[0]}#{protocol_id} {corresp_list[1]}#{protocol_id}"
    })

    t_div_shikidai = soup.new_tag('div', type="式題", **{"xml:id": f"shikidai{shiki_order_id}"})
    t_div_shikidai.append(soup.new_tag('p', **{"xml:id": f"shikidai{shiki_order_id}01"}))
    t_div_shikidai.p.string = "式題"

    t_div_bidai = soup.new_tag('div', type="尾題", **{"xml:id": f"bidai{shiki_no.zfill(2)}"})
    t_div_bidai.append(soup.new_tag('p', **{"xml:id": f"bidai{shiki_no.zfill(2)}01"}))
    t_div_bidai.p.string = "尾題"

    t_div_okugaki = soup.new_tag('div', type="本奥書", **{"xml:id": f"okugaki{shiki_no.zfill(2)}"})
    t_div_okugaki.append(soup.new_tag('p', **{"xml:id": f"okugaki{shiki_no.zfill(2)}01"}))
    t_div_okugaki.p.string = "本奥書"

    t_div_maki.append(t_div_shudai)
    t_div_maki.append(t_div_shiki)
    t_div_shiki.append(t_div_shikidai)
    t_div_maki.append(t_div_bidai)
    t_div_maki.append(t_div_okugaki)

    # 条・項ループ
    for data in metadata:
        jyou = data['条']
        article_id = f"article{shiki_order_id[-3:]}{jyou.zfill(3)}"
        t_div_article = soup.new_tag('div', ana=shiki_name, **{
            "xml:id": article_id,
            "n": make_n_attr(shiki_no, shiki_order, jyou, add_shiki_order),
            "type": "条",
            "corresp": f"{corresp_list[0]}#{article_id} {corresp_list[1]}#{article_id}"
        })
        t_div_article.append(soup.new_tag('head', ana=data["新条文名"]))
        if lang_choice:
            t_div_article.append(soup.new_tag('note', type="summary"))
        for kou in range(int(data["項"])):
            item_id = f"item{article_id[-6:]}{str(kou+1).zfill(2)}"
            t_div_article.append(soup.new_tag('p', ana="項", **{
                "xml:id": item_id,
                "corresp": f"{corresp_list[0]}#{item_id} {corresp_list[1]}#{item_id}"
            }))
        t_div_shiki.append(t_div_article)

    # 本文挿入
    for item in soup.select('p[ana="項"]'):
        item.string = '本文'
    if lang_choice:
        for summary in soup.select('note[type="summary"]'):
            summary.string = '条文概要'

    with open(output_filename, 'w', encoding='utf-8') as result:
        result.write(soup.prettify())

    print("本文ファイルのXML生成が完了しました。")

def main():
    file_volume = input('読み込む巻を入力してください: ')
    mode = input('本文（1）か凡例（2）かを選択してください: ').strip()
    if mode == '2':
        handle_fanrei_mode(file_volume)
    else:
        handle_honbun_mode(file_volume)

if __name__ == "__main__":
    main()
