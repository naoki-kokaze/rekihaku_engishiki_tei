import os

def generate_TEIheader(output_filename):
    """ ヘッダーの記述
    既存のTEIヘッダーの記述を新規ファイルに出力する（モード 'w'）
    地理情報なども入れると良い"""

    output_file = open(output_filename, 'w', encoding='utf-8')

    header_file = open('engishiki_header.xml', 'r', encoding='utf-8')
    header = header_file.read()
    header_file.close()
    
    output_file.write(header)

    output_file.close()

    print('TEIヘッダー情報書き込み完了')

######################################################################
################### 読み込み＆書き出しファイルの指定 ########################
######################################################################



#os.chdir('/Users/kokaze/Documents/延喜式引継ぎ/対照コーパス/基礎データ/項目数')
#作業者が適切なディレクトリを指定する

file_volume = input('読み込む巻を入力してください\n')

input_filename = f'metadata_v{file_volume}.tsv'
# 巻11.csv
output_filename = f'engishiki_v{file_volume}.xml'
# engishiki_v11.xml


# headerを書き込む
generate_TEIheader(output_filename)
# 関数は別ファイルとして保存してある
result = open(output_filename, 'a', encoding='utf-8')
# 書き出しファイルを作る

result.write(f'<text><body>\n')



with open(input_filename, 'r', encoding='utf-8') as f:
    contents_list = f.readlines()
    
contents_list2 = []
for content_line in contents_list[1:]:
    content = content_line.split('\t')
    contents_list2.append(content)
    content_rstrip = content[-1].rstrip()
    content.pop(-1)
    content.append(content_rstrip)
    
# bodyを書き込む
# 1. フレームの式<div ana="斎宮" n="5" subtype="条" type="式"><head>斎宮</head>
shiki_name = contents_list2[0][1]
shiki_no = contents_list2[0][0]
result.write(f'<div ana="{shiki_name}" n="{shiki_no}" subtype="条" type="式"><head>{shiki_name}</head>\n')

for content in contents_list2:
    # 2. その下に条の構造を作る (ここはループする)
    '''
    <div ana="斎宮" n="5.1" subtype="項" type="条">
                    <head ana="定斎王"/>
                    <p ana="項" corresp="engishiki_ja.xml#item05100101 engishiki_en.xml#item05100101"
                        xml:id="item05100101"> 凡天皇即位者、定伊勢大神宮斎王、仍簡内親王未嫁者卜之、〈<span type="割書"/>〉訖即遣勅使於彼家、
                            告示事由、神祇祐已上一人、率僚下随勅使共向、卜部解除、神部以木綿着賢木、立殿四面及内外門、〈<span type="割書"/>〉
                            其後択日時、百官為大祓、〈<span type="割書"/>〉<lb/>
                    </p>
                </div>
    '''
    jou_no_raw = content[3]
    jou_no = f'{shiki_no}.{jou_no_raw}'
    jou_name = content[4] #新条文名
    result.write(f'<div ana="{shiki_name}" n="{jou_no}" subtype="項" type="条"><head ana="{jou_name}"/>')
    
    kous = int(content[-1])
    for kou in range(kous):    
        item_id = f'item{shiki_no.zfill(2)}{content[2]}{jou_no_raw.zfill(3)}{str(kou+1).zfill(2)}'
        result.write(f'<p ana="項" corresp="engishiki_ja.xml#{item_id} engishiki_en.xml#{item_id}" xml:id="{item_id}">本文</p>')
    result.write(f'</div>')
result.write('</div></body></text></TEI>')
print('body書き込み完了')
result.close()
