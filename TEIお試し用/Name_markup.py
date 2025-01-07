import lxml.etree as ET
import csv
import re
from html import unescape
import os

def load_tsv(tsv_path):
    """TSVを読み込み、変換ルールをリストで返す"""
    with open(tsv_path, 'r', encoding='utf-8') as file:
        return [(row[0], row[1]) for row in csv.reader(file, delimiter='\t')][1:]  # ヘッダーをスキップ

def update_p_tag_text_in_text(element, replacements, tag_name):
    """<text>タグ内に限定した<p>タグのテキストを置換する"""
    namespaces = {'tei': 'http://www.tei-c.org/ns/1.0'}

    # <text>タグを探索
    for text_element in element.xpath('.//tei:text', namespaces=namespaces):
        # <text>タグ内の<p>タグを探索
        for p in text_element.xpath('.//tei:p', namespaces=namespaces):
            for child in p.iter():  # <p>タグ内のテキストを対象に
                # <orgName>または<placeName>タグのtextはスキップ
                if child.tag != f'{{http://www.tei-c.org/ns/1.0}}{tag_name}' and child.text:
                    original_text = child.text
                    replaced_text = replace_text(original_text, replacements)
                    if original_text != replaced_text:
                        child.text = replaced_text
                
                # tail部分は指定されたタグに関係なく置換を適用
                if child.tail:
                    original_tail = child.tail
                    replaced_tail = replace_text(original_tail, replacements)
                    if original_tail != replaced_tail:
                        child.tail = replaced_tail


def replace_text(text, replacements):
    """テキストの置換を行う"""
    for old, new in replacements:
        text = re.sub(re.escape(old), new, text)
    return text

def main():
    """ユーザー入力からファイルパスを取得し、XMLを読み込み、変換を実行し、ファイルを保存する"""
    
    # 入力XMLファイルのパスをユーザーから取得
    xml_path = input("入力XMLファイルのパス（拡張子は自動追加されます）: ").strip()
    if not xml_path.lower().endswith('.xml'):
        xml_path += '.xml'

    # 入力ファイル名からベース名を取得（拡張子を除く）
    base_name = os.path.splitext(os.path.basename(xml_path))[0]
    
    # 処理するTSVファイルの種類を選択（orgまたはplace）
    file_type = input("処理するTSVファイルの種類を選んでください（官司名なら'o'、地名なら'p'を入力）: ").strip()
    if file_type == "o":
        tsv_type = "官司名"
        tsv_numbers = ["1", "2", "3", "4"]
        tag_name = "orgName"
        suffix = "org"
    elif file_type == "p":
        tsv_type = "地名"
        tsv_numbers = ["1", "2"]
        tag_name = "placeName"
        suffix = "place"
    else:
        print("無効な入力です。終了します。")
        return

    # 中間ファイルの初期設定（ベース名に基づく）
    intermediate_xml_path = f"{base_name}_{suffix}.xml"

    try:
        # 初回のXMLファイルを読み込む
        tree = ET.parse(xml_path, parser=ET.XMLParser(recover=True))
        root = tree.getroot()

        for tsv_number in tsv_numbers:
            tsv_path = f"{tsv_type}_{tsv_number}.tsv"
            print(f"{tsv_path} を適用中...")

            if not os.path.exists(tsv_path):
                print(f"{tsv_path} が見つかりません。スキップします。")
                continue

            # 置換ルールを読み込み
            replacements = load_tsv(tsv_path)

            # 置換処理を適用
            update_p_tag_text_in_text(root, replacements, tag_name)

            # 中間結果を保存
            xml_string = unescape(ET.tostring(root, encoding='unicode'))
            with open(intermediate_xml_path, 'w', encoding='utf-8') as f:
                f.write(xml_string)

            # 次の処理のために保存したXMLを再読み込み
            tree = ET.parse(intermediate_xml_path, parser=ET.XMLParser(recover=True))
            root = tree.getroot()

        print(f"最終的なXMLを {intermediate_xml_path} に保存しました。")

    except ET.XMLSyntaxError as e:
        print(f"XMLのパースに失敗しました: {e}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
