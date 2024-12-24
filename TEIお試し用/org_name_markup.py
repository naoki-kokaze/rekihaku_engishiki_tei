import lxml.etree as ET
import csv
import re
from html import unescape
import os

def load_tsv(tsv_path):
    """TSVを読み込み、変換ルールをリストで返す"""
    with open(tsv_path, 'r', encoding='utf-8') as file:
        return [(row[0], row[1]) for row in csv.reader(file, delimiter='\t')][1:]  # ヘッダーをスキップ

def update_p_tag_text(element, replacements):
    """<p>タグ内のテキスト（入れ子のテキストも含む）を置換する"""
    namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    for p in element.xpath('.//tei:p', namespaces=namespaces):  # <p>タグを対象に
        for child in p.iter():  # <p>タグ内のテキストを対象に
            # <placeName>タグが付いている部分はスキップ
            if child.tag != '{http://www.tei-c.org/ns/1.0}orgName' and child.text:
                # 置換処理
                child.text = unescape(replace_text(child.text, replacements))
            if child.tag != '{http://www.tei-c.org/ns/1.0}orgName' and child.tail:  # tailも同様に処理
                # 置換処理
                child.tail = unescape(replace_text(child.tail, replacements))

def replace_text(text, replacements):
    """テキストの置換を行う"""
    for old, new in replacements:
        text = re.sub(re.escape(old), new, text)
    return text

def main():
    """ユーザー入力からファイルパスを取得し、XMLを読み込み、変換を実行し、ファイルを保存する"""
    
    # 入力XMLファイルのパスをユーザーから取得
    xml_path = input("入力XMLファイルのパス（拡張子は自動追加されます）: ").strip()
    
    # 拡張子が指定されていない場合、.xmlを追加
    if not xml_path.lower().endswith('.xml'):
        xml_path += '.xml'
    
    # 入力TSVファイルのパスをユーザーから取得
    tsv_path = input("TSVファイルのパス: ").strip()
    
    # 拡張子が指定されていない場合、.tsvを追加
    if not tsv_path.lower().endswith('.tsv'):
        tsv_path += '.tsv'
    
    # 出力ファイルのパス（拡張子は自動追加される）
    output_path = xml_path.replace('.xml', '_org.xml')

    try:
        # XMLの読み込み
        tree = ET.parse(xml_path, parser=ET.XMLParser(recover=True))
        root = tree.getroot()
    except ET.XMLSyntaxError as e:
        print(f"XMLのパースに失敗しました: {e}")
        return

    # TSVから変換ルールを読み込み
    replacements = load_tsv(tsv_path)
    
    # <p>タグ内のテキストを置換
    update_p_tag_text(root, replacements)

    # XML全体をエスケープされた文字を元に戻す
    xml_string = unescape(ET.tostring(root, encoding='unicode'))

    # 結果を保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_string)
    
    print(f"変換後のXMLを{output_path}に保存しました。")

if __name__ == "__main__":
    main()
