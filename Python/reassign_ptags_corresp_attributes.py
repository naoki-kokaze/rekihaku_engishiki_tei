import os
import glob
import re
from bs4 import BeautifulSoup

# 編集するフォルダのパスを指定
folder_path = '../TEIお試し用'

# 指定フォルダ内のすべてのXMLファイルを取得し、「header」を含むファイルは除外
xml_files = [f for f in glob.glob(os.path.join(folder_path, '*.xml')) if 'header' not in os.path.basename(f)]

# corresp属性を修正する関数
def update_corresp(tag, version_str):
    """
    corresp属性を持つタグに対して、"engishiki_" の後にバージョン番号を追加する。
    
    :param tag: 処理対象のタグ (<div>または<p>)
    :param version_str: "_v{version_number}" の形式のバージョン文字列
    """
    if tag.has_attr('corresp'):
        corresp_value = tag['corresp']

        if '_v' not in corresp_value:
            # 正規表現で "engishiki_" の後にバージョン番号を追加
            corrected_corresp = re.sub(r'engishiki(_(ja|en|xml))?', f'engishiki{version_str}\\1', corresp_value)
        
            # 修正後のcorrespを設定
            tag['corresp'] = corrected_corresp

# 各XMLファイルに対して処理を実行
for xml_file in xml_files:
    # XMLファイルを読み込み
    with open(xml_file, 'r', encoding='utf-8') as file:
        xml_data = file.read()

    # BeautifulSoupでXMLを解析
    soup = BeautifulSoup(xml_data, "xml")

    # <div>タグの中で@n属性を持つものだけを取得
    div_tags_with_n = soup.find_all('div', attrs={'n': True})
    
    # 各<div>タグに対して処理
    for div in div_tags_with_n:
        # <div>タグの@n属性を使ってversion_numberを定義
        n_attr = div.get('n', '')
        if '.' in n_attr:
            version_number = n_attr.split('.')[0]  # ピリオドがある場合
        else:
            version_number = n_attr  # ピリオドがない場合はそのまま

        version_str = f"_v{version_number}"

        # (1) <div>タグが@correspを持つ場合
        update_corresp(div, version_str)

        # (2) <p>タグが@correspを持つ場合、その親の<div>タグのn属性を使う
        p_tags = div.find_all('p')  # <div>タグ内の全ての<p>タグを取得
        for p in p_tags:
            update_corresp(p, version_str)

    # 修正後のXMLデータを元のファイルに書き戻す
    with open(xml_file, 'w', encoding='utf-8') as file:
        file.write(soup.prettify())
    
    print(f"{xml_file} の処理が完了しました。")
