import os
from bs4 import BeautifulSoup

def update_files_from_source(source_file, folder_path):
    # 1. 元のファイルから<p ana="全体">の内容を取得
    with open(source_file, "r", encoding="utf-8") as f:
        source_soup = BeautifulSoup(f, "xml")
    
    # <editorialDecl ana="校訂文凡例"> 内の最初の <p ana="全体"> を取得
    source_editorial_decl = source_soup.find("editorialDecl", {"ana": "校訂文凡例"})
    if source_editorial_decl is None:
        print("Error: <editorialDecl ana='校訂文凡例'> not found in source file.")
        return
    
    source_p = source_editorial_decl.find("p", {"ana": "全体"})
    if source_p is None:
        print("Error: <p ana='全体'> not found in source file.")
        return
    
    # 2. 同じフォルダ内の_ja、_enの付いていないファイルを探索
    for filename in os.listdir(folder_path):
        if filename.endswith("_ja.xml") or filename.endswith("_en.xml"):
            continue
        
        file_path = os.path.join(folder_path, filename)
        
        if file_path == source_file:
            continue
        
        # 3. ターゲットファイルの内容を更新
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                target_soup = BeautifulSoup(f, "xml")
            
            # ターゲットファイルの <editorialDecl> を探す
            target_editorial_decl = target_soup.find("editorialDecl")
            
            if target_editorial_decl is not None:
                # <editorialDecl> に ana="校訂文凡例" を追加
                target_editorial_decl['ana'] = "校訂文凡例"

                # ターゲットファイルの <p ana="全体"> を探す
                target_p = target_editorial_decl.find("p")
                
                if target_p is not None:
                    # ターゲットファイルの <p ana="全体"> を更新
                    target_p.replace_with(source_p)
                    
                    # ファイルを保存
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(str(target_soup))
                    
                    print(f"Updated: {filename}")
                else:
                    print(f"Error: <p ana='全体'> not found in {filename}")
            else:
                print(f"Error: <editorialDecl> not found in {filename}")
        except Exception as e:
            print(f"Error updating {filename}: {e}")

# 使用例
source_file = "../TEI編集用/engishiki_header_all.xml"  # 元データファイル
folder_path = "../TEI編集用"  # Pythonフォルダと同階層にあるTEI編集用フォルダのパス

update_files_from_source(source_file, folder_path)
