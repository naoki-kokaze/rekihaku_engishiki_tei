import os
import re
import copy
import tkinter as tk
from tkinter import ttk
from bs4 import BeautifulSoup


# =========================================================
# 固定パス・定数
# =========================================================
SOURCE_FILE = "../TEI編集用/engishiki_header_all.xml"
TAX_SO_SOURCE_FILE = "../TEI編集用/engishiki_taxonomy_standoff_master.xml"
INPUT_FOLDER = "../TEI編集用"
OUTPUT_FOLDER = "../途中生成物"

ANA_MAP = {
    "無印": "校訂文凡例",
    "_ja": "現代語訳凡例",
    "_en": "英訳凡例",
    "XML": "XML"
}
ANA_ORDER = ["校訂文凡例", "現代語訳凡例", "英訳凡例"]


# =========================================================
# ログ操作
# =========================================================
def log(text: str):
    """GUIログに1行追加"""
    log_text.insert(tk.END, text + "\n")
    log_text.see(tk.END)


def clear_log():
    """GUIログを全消去"""
    log_text.delete("1.0", tk.END)


# =========================================================
# XML 操作ユーティリティ
# =========================================================
def split_tei_xml(xml_text: str):
    """
    TEI XML を
      pre   : <TEI> ～ <teiHeader> 直前
      header: <teiHeader>...</teiHeader>
      post  : </teiHeader> 以降
    に安全分割
    """
    m = re.search(
        r"(.*?<TEI[^>]*>\s*)(<teiHeader\b[^>]*>.*?</teiHeader>)(.*)$",
        xml_text,
        flags=re.DOTALL
    )
    if not m:
        return None, None, None
    return m.group(1), m.group(2), m.group(3)


def is_header_file(filename: str) -> bool:
    """
    header 系ファイルかどうかを file_kind に基づいて判定する。
    header_all は含まない。
    """
    return file_kind(filename) in {"body_header", "header"}


def insert_after(parent, new_node, after_tag):
    """
    parent 内の <after_tag> 直後に new_node を挿入
    見つからなければ末尾に追加
    """
    children = list(parent.children)
    for i, child in enumerate(children):
        if getattr(child, "name", None) == after_tag:
            parent.insert(i + 1, new_node)
            return
    parent.append(new_node)


# =========================================================
# ファイル種別・巻番号ユーティリティ
# =========================================================

def file_kind(filename: str) -> str:
    """
    engishiki 系 XML ファイルの役割（性格）を、
    ファイル名の命名規則に基づいて分類する。

    本関数は「処理対象かどうか」を判断せず、
    あくまでファイルの種類（世界観）を一意に返すための
    判定専用ユーティリティである。

    戻り値は以下のいずれか：

    - "body":
        巻番号を持つ本文ファイル。
        処理①・処理③の対象。
        例：
          engishiki_v1.xml
          engishiki_v1_ja.xml
          engishiki_v1_en.xml

    - "body_header":
        巻番号を持つ header 専用ファイル。
        処理①・処理②の対象。
        例：
          engishiki_v1_header.xml

    - "header":
        巻番号を持たない通常の header ファイル。
        処理①の対象。
        例：
          engishiki_header.xml
          engishiki_header_ja.xml
          engishiki_header_en.xml

    - "header_all":
        すべての header / 本文に反映される
        唯一の絶対基準 header ファイル。
        本ファイル自体は処理対象としない。
        例：
          engishiki_header_all.xml

    - "other":
        上記いずれにも該当しないファイル。
        想定外、または処理対象外。

    注意：
    - 巻番号は v1 ～ v99 を想定している。
    - v01 などのゼロ埋め表記は現時点では想定しない。
    """

    # ① 絶対基準 header（最優先）
    if filename == "engishiki_header_all.xml":
        return "header_all"

    # ② 巻別 header 専用ファイル
    if re.fullmatch(r"engishiki_v\d{1,2}_header\.xml", filename):
        return "body_header"

    # ③ 巻別本文（無印 / ja / en）
    if re.fullmatch(r"engishiki_v\d{1,2}(_ja|_en)?\.xml", filename):
        return "body"

    # ④ 巻番号を持たない通常 header（ja / en 含む）
    if re.fullmatch(r"engishiki_header(_ja|_en)?\.xml", filename):
        return "header"

    # ⑤ その他
    return "other"


def extract_volume(filename: str):
    """file_kind() の命名規則に基づき、巻番号（int）を取得する"""
    m = re.search(r"_v(\d{1,2})", filename)
    return int(m.group(1)) if m else None


# =========================================================
# 処理① 本文・header 凡例／共通部 更新
# =========================================================
def update_files():
    clear_log()

    selected_plain = check_plain.get()
    selected_ja = check_ja.get()
    selected_en = check_en.get()
    selected_xml = check_xml.get()

    if not (
        selected_plain or selected_ja or selected_en or selected_xml
        or check_filedesc.get()
        or check_tagsdecl.get()
        or check_unitdecl.get()
    ):
        log("【エラー】処理対象が選択されていません。")
        return

    # --- 基準ファイル読み込み ---
    try:
        with open(SOURCE_FILE, encoding="utf-8") as f:
            source_soup = BeautifulSoup(f, "xml")
    except Exception as e:
        log(f"【エラー】基準ファイルの読み込みに失敗しました: {e}")
        return

    # --- editorialDecl <p> テンプレ ---
    p_templates = {}
    for ana in ANA_MAP.values():
        decl = source_soup.find("editorialDecl", {"ana": ana})
        if not decl:
            log(f"【警告】基準ファイルに editorialDecl ana='{ana}' が見つかりません。")
            continue

        p = decl.find("p", {"ana": "全体"}) or decl.find("p")
        if not p:
            log(f"【警告】基準ファイル {ana} に <p> が見つかりません。")
            continue

        p_templates[ana] = copy.deepcopy(p)

    # --- 共通部テンプレ ---
    common_templates = {}
    if check_filedesc.get():
        tag = source_soup.find("fileDesc")
        if tag:
            common_templates["fileDesc"] = copy.deepcopy(tag)

    if check_tagsdecl.get():
        tag = source_soup.find("tagsDecl")
        if tag:
            common_templates["tagsDecl"] = copy.deepcopy(tag)

    if check_unitdecl.get():
        tag = source_soup.find("unitDecl")
        if tag:
            common_templates["unitDecl"] = copy.deepcopy(tag)

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # --- 対象ファイル処理 ---
    for filename in os.listdir(INPUT_FOLDER):

        if filename == os.path.basename(SOURCE_FILE):
            continue
        if not filename.endswith(".xml"):
            continue

        try:
            xml_text = open(os.path.join(INPUT_FOLDER, filename), encoding="utf-8").read()
        except Exception as e:
            log(f"【エラー】{filename} の読み込み失敗: {e}")
            continue

        pre, header_xml, post = split_tei_xml(xml_text)
        if not header_xml:
            log(f"【エラー】{filename}: teiHeader 分離失敗")
            continue

        soup = BeautifulSoup(header_xml, "xml")
        updated = False

        kind = file_kind(filename)

        if kind not in {"body", "body_header", "header"}:
            log(f"【情報】{filename}: 処理①対象外（{kind}）")
            continue
        
        ana_targets = []

        # --- 凡例適用判定 ---
        if kind in {"header", "body_header"}:
            # header 系：複数凡例が入りうる
            if selected_plain:
                ana_targets.append(ANA_MAP["無印"])
            if selected_ja:
                ana_targets.append(ANA_MAP["_ja"])
            if selected_en:
                ana_targets.append(ANA_MAP["_en"])

        elif kind == "body":
            # 本文：自分の言語に対応する凡例のみ
            if filename.endswith("_ja.xml") and selected_ja:
                ana_targets.append(ANA_MAP["_ja"])
            elif filename.endswith("_en.xml") and selected_en:
                ana_targets.append(ANA_MAP["_en"])
            elif selected_plain:
                ana_targets.append(ANA_MAP["無印"])

        # XML凡例は header / 本文どちらにも入る
        if selected_xml:
            ana_targets.append(ANA_MAP["XML"])

        # --- editorialDecl 置換 ---
        for ana in ana_targets:
            if ana not in p_templates:
                continue

            decl = soup.find("editorialDecl", {"ana": ana})
            if not decl:
                log(f"{filename}: editorialDecl ana='{ana}' が存在しません")
                continue

            old_p = decl.find("p")
            if not old_p or old_p.get("ana", "全体") != "全体":
                log(f"{filename}: {ana} は <p ana='全体'> でないためスキップ")
                continue

            old_p.replace_with(copy.deepcopy(p_templates[ana]))
            updated = True

        # --- 共通部置換 ---
        for tag_name, tmpl in common_templates.items():
            old = soup.find(tag_name)
            if old:
                old.replace_with(copy.deepcopy(tmpl))
                updated = True
            else:
                log(f"{filename}: <{tag_name}> が存在しません")

        # --- 保存 ---
        if updated:
            outname = f"{os.path.splitext(filename)[0]}_凡例等更新.xml"
            open(os.path.join(OUTPUT_FOLDER, outname), "w", encoding="utf-8").write(
                pre + str(soup.teiHeader) + post
            )
            log(f"✔ {filename} → {outname}")
        else:
            log(f"【情報】{filename}: 差し替え対象なし")


# =========================================================
# 処理② 各巻 header 凡例追加
# =========================================================
def add_editorial_decls():
    clear_log()

    targets = []
    if add_koutei.get():   targets.append("校訂文凡例")
    if add_gendaigo.get(): targets.append("現代語訳凡例")
    if add_eiyaku.get():   targets.append("英訳凡例")

    if not targets:
        log("【エラー】凡例種別が未選択です。")
        return

    vols = re.findall(r"\d{1,2}", vol_entry.get())
    if not vols:
        log("【エラー】巻番号が不正です。")
        return

    src = BeautifulSoup(open(SOURCE_FILE, encoding="utf-8"), "xml")
    decl_templates = {
        ana: copy.deepcopy(src.find("editorialDecl", {"ana": ana}))
        for ana in targets if src.find("editorialDecl", {"ana": ana})
    }

    for v in vols:
        fname = f"engishiki_v{int(v)}_header.xml"
        path = os.path.join(INPUT_FOLDER, fname)

        if not os.path.exists(path):
            log(f"【エラー】{fname} が存在しません。")
            continue

        xml_text = open(path, encoding="utf-8").read()
        pre, header_xml, post = split_tei_xml(xml_text)
        if not header_xml:
            log(f"{fname}: teiHeader 分離失敗")
            continue

        soup = BeautifulSoup(header_xml, "xml")
        enc = soup.find("encodingDesc")
        if not enc:
            log(f"{fname}: encodingDesc 不在")
            continue

        existing = {d.get("ana") for d in enc.find_all("editorialDecl", recursive=False)}
        updated = False

        for ana in ANA_ORDER:
            if ana in targets and ana not in existing:
                enc.append(copy.deepcopy(decl_templates.get(ana)))
                updated = True

        if updated:
            out = f"{fname[:-4]}_凡例追加.xml"
            open(os.path.join(OUTPUT_FOLDER, out), "w", encoding="utf-8").write(
                pre + str(soup.teiHeader) + post
            )
            log(f"✔ {fname}: 凡例追加完了")


# =========================================================
# 処理③ taxonomy / standOff 追加
# =========================================================
def resolve_target_files():
    files = [
        f for f in os.listdir(INPUT_FOLDER)
        if f.endswith(".xml")
    ]

    # --- 巻指定 ---
    if taxonomy_single_var.get():
        vols = {
            int(v) for v in re.findall(r"\d{1,2}", taxonomy_volume_entry.get())
        }
        if not vols:
            log("【エラー】巻番号が不正です。")
            return []

        targets = []
        for f in files:
            if file_kind(f) != "body":
                continue

            vol = extract_volume(f)
            if vol in vols:
                targets.append(f)

        return sorted(targets)

    # --- 全巻 ---
    if taxonomy_all_var.get():
        return sorted([
            f for f in files
            if file_kind(f) == "body"
        ])

    log("【エラー】巻指定 / 全巻 が未選択です。")
    return []


def add_header_extras():
    clear_log()

    if not (taxonomy_var.get() or standoff_var.get()):
        log("【エラー】taxonomy / standOff が未選択です。")
        return

    targets = resolve_target_files()
    if not targets:
        return

    src = BeautifulSoup(open(TAX_SO_SOURCE_FILE, encoding="utf-8"), "xml")
    src_classDecl = src.find("classDecl")
    src_standOff = src.find("standOff")

    for fname in targets:
        path = os.path.join(INPUT_FOLDER, fname)
        if not os.path.exists(path):
            log(f"【エラー】{fname} 不在")
            continue

        xml_text = open(path, encoding="utf-8").read()
        pre, header_xml, post = split_tei_xml(xml_text)
        if not header_xml:
            continue

        soup = BeautifulSoup(header_xml, "xml")
        modified = False

        if taxonomy_var.get():
            enc = soup.find("encodingDesc")
            if enc and not enc.find("classDecl") and src_classDecl:
                enc.append(copy.deepcopy(src_classDecl))
                log(f"✔ {fname}: taxonomy 追加")
                modified = True

        if standoff_var.get():
            if not re.search(r"<standOff\b", post) and src_standOff:
                post = str(copy.deepcopy(src_standOff)) + post
                log(f"✔ {fname}: standOff 追加")
                modified = True

        if modified:
            suffix = []
            if taxonomy_var.get(): suffix.append("tax")
            if standoff_var.get(): suffix.append("so")
            out = f"{fname[:-4]}_{'_'.join(suffix)}.xml"
            open(os.path.join(OUTPUT_FOLDER, out), "w", encoding="utf-8").write(
                pre + str(soup.teiHeader) + post
            )
            log(f"✔ {fname}: 保存完了 → {out}")
        else:
            log(f"【情報】{fname}: 変更なし")


# =========================================================
# GUI 定義
# =========================================================
root = tk.Tk()
root.title("凡例等更新・追加ツール")
root.geometry("750x600")
root.configure(bg="#F0F8FF")

# --- Style ---
style = ttk.Style()
style.theme_use("default")
style.configure("TButton", foreground="white", background="#4682B4", font=("Meiryo", 10, "bold"))
style.configure("TLabel", background="#F0F8FF", font=("Meiryo", 10))
style.configure("TCheckbutton", background="#F0F8FF", font=("Meiryo", 10))
style.configure("TLabelframe", background="#F0F8FF", font=("Meiryo", 10, "bold"))
style.configure("TLabelframe.Label", background="#F0F8FF", font=("Meiryo", 10, "bold"))
style.configure("TFrame", background="#F0F8FF")

# --- BooleanVars ---
check_plain = tk.BooleanVar()
check_ja = tk.BooleanVar()
check_en = tk.BooleanVar()
check_xml = tk.BooleanVar()
check_filedesc = tk.BooleanVar()
check_tagsdecl = tk.BooleanVar()
check_unitdecl = tk.BooleanVar()

add_koutei = tk.BooleanVar()
add_gendaigo = tk.BooleanVar()
add_eiyaku = tk.BooleanVar()

taxonomy_single_var = tk.BooleanVar()
taxonomy_all_var = tk.BooleanVar()
taxonomy_var = tk.BooleanVar()
standoff_var = tk.BooleanVar()


# =========================================================
# GUI 部品配置
# =========================================================

# ----- 本文+header 更新 -----
frame = ttk.LabelFrame(root, text="全体凡例 / 共通部分 更新 （対象：各巻本文・header、各header）")
frame.pack(fill="x", padx=10, pady=5)

ttk.Checkbutton(frame, text="校訂文凡例", variable=check_plain).pack(side="left")
ttk.Checkbutton(frame, text="現代語訳凡例", variable=check_ja).pack(side="left")
ttk.Checkbutton(frame, text="英訳凡例", variable=check_en).pack(side="left")
ttk.Checkbutton(frame, text="XML凡例", variable=check_xml).pack(side="left")
ttk.Checkbutton(frame, text="fileDesc", variable=check_filedesc).pack(side="left")
ttk.Checkbutton(frame, text="tagsDecl", variable=check_tagsdecl).pack(side="left")
ttk.Checkbutton(frame, text="unitDecl", variable=check_unitdecl).pack(side="left")

ttk.Button(root, text="凡例等更新", command=update_files).pack(pady=10)


# ----- 各巻 header 凡例追加 -----
add_frame = ttk.LabelFrame(root, text="凡例追加 （対象：各巻header）")
add_frame.pack(fill="x", padx=10, pady=5)

# 1行目：凡例種別
row1 = ttk.Frame(add_frame)
row1.pack(fill="x", pady=2)

ttk.Checkbutton(row1, text="校訂文", variable=add_koutei).pack(side="left", padx=5)
ttk.Checkbutton(row1, text="現代語訳", variable=add_gendaigo).pack(side="left", padx=5)
ttk.Checkbutton(row1, text="英訳", variable=add_eiyaku).pack(side="left", padx=5)

# 2行目：巻番号入力
row2 = ttk.Frame(add_frame)
row2.pack(fill="x", pady=2)

ttk.Label(row2, text="巻番号（カンマ区切り）:").pack(side="left", padx=5)
vol_entry = ttk.Entry(row2, width=20)
vol_entry.pack(side="left", padx=5)

# 実行ボタン
ttk.Button(root, text="凡例追加", command=add_editorial_decls).pack(pady=10)


# ----- taxonomy / standOff 追加 -----
extras_frame = ttk.LabelFrame(root, text="taxonomy / standOff 追加 （対象：各巻本文）")
extras_frame.pack(fill="x", padx=10, pady=5)

# 1行目：taxonomy / standOff
row1 = ttk.Frame(extras_frame)
row1.pack(fill="x", pady=2)

ttk.Checkbutton(row1, text="taxonomy", variable=taxonomy_var).pack(side="left", padx=5)
ttk.Checkbutton(row1, text="standOff", variable=standoff_var).pack(side="left", padx=5)

# 2行目：巻指定 / 巻番号 / 全巻
row2 = ttk.Frame(extras_frame)
row2.pack(fill="x", pady=2)

ttk.Checkbutton(row2, text="巻指定", variable=taxonomy_single_var).pack(side="left", padx=5)
ttk.Label(row2, text="巻番号（カンマ区切り）:").pack(side="left")
taxonomy_volume_entry = ttk.Entry(row2, width=15)
taxonomy_volume_entry.pack(side="left", padx=5)

ttk.Checkbutton(row2, text="全巻", variable=taxonomy_all_var).pack(side="left", padx=10)

# 実行ボタン
ttk.Button(root, text="情報追加", command=add_header_extras).pack(pady=10)


# ----- ログエリア -----
log_text = tk.Text(root, height=15)
log_text.pack(fill="both", padx=10, pady=10, expand=True)

root.mainloop()
