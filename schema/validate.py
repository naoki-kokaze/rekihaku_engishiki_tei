#!/usr/bin/env python3
"""TEI編集用/ の XML を検証し、問題をファイル名・行番号つきで表示する。

  1. tei_all.rng（TEI として正しい形か）            … jing
  2. schema/engishiki.sch（延喜式のデータとして正しいか） … SchXslt

使い方:
  python3 schema/validate.py                  # TEI編集用/ の全ファイル
  python3 schema/validate.py engishiki_v8.xml # 指定したファイルだけ
  python3 schema/validate.py --changed-from <commit>  # そのコミット以降に変わったファイルだけ

必要なもの: Java、jing.jar、schxslt-cli.jar、Python の lxml。
jar の場所は環境変数 JING_JAR / SCHXSLT_JAR で渡す（CI では workflow が用意する）。

終了コード: error が 1 件でもあれば 1。warning だけなら 0。
GITHUB_ACTIONS が設定されていれば、PR の差分画面に出る注釈の形式でも出力する。
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
TEI_DIR = ROOT / "TEI編集用"
SCH = ROOT / "schema" / "engishiki.sch"
# 作業者のエディタ（xml-model の参照先）と同じ版に揃える。版を上げるときは workflow の sha256 も更新する
TEI_VERSION = "4.12.0"
RNG = os.environ.get("TEI_ALL_RNG",
                     f"https://www.tei-c.org/Vault/P5/{TEI_VERSION}/xml/tei/custom/schema/relaxng/tei_all.rng")
JAVA = os.environ.get("JAVA", "java")
JING_JAR = os.environ.get("JING_JAR")
SCHXSLT_JAR = os.environ.get("SCHXSLT_JAR")

# これらが変わると他の全ファイルの参照に影響するので、全件を検証する
SHARED = {"engishiki_standOff.xml", "engishiki_taxonomy_standoff_master.xml",
          "engishiki_header_all.xml"}

# teiHeader だけの断片で、単体では TEI として完結しないため RNG 検証から外す
RNG_SKIP = {"engishiki_header_ja.xml", "engishiki_header_en.xml"}

SVRL = {"svrl": "http://purl.oclc.org/dsdl/svrl"}
GHA = bool(os.environ.get("GITHUB_ACTIONS"))


def emit(level, path, line, msg):
    rel = path.relative_to(ROOT)
    msg = " ".join(msg.split())
    print(f"{rel}:{line or '?'}: {level}: {msg}")
    if GHA:
        kind = "error" if level == "error" else "warning"
        print(f"::{kind} file={rel},line={line or 1}::{msg}")


def run_jing(files):
    targets = [f for f in files if f.name not in RNG_SKIP]
    if not targets:
        return 0
    r = subprocess.run([JAVA, "-jar", JING_JAR, RNG, *map(str, targets)],
                       capture_output=True, text=True)
    n = 0
    for out in r.stdout.splitlines():
        m = re.match(r"^(.*?):(\d+):\d+: (error|warning): (.*)$", out)
        if m:
            emit(m.group(3), Path(m.group(1)), m.group(2), "[TEI] " + m.group(4))
            n += m.group(3) == "error"
    return n


def location_to_line(tree, loc):
    # SVRL の位置は /Q{ns}TEI[1]/Q{ns}text[1]/... の形。lxml で引ける形に直す
    xp = re.sub(r"Q\{http://www\.tei-c\.org/ns/1\.0\}", "tei:", loc)
    try:
        hit = tree.xpath(xp, namespaces={"tei": "http://www.tei-c.org/ns/1.0"})
    except etree.XPathError:
        return None
    return hit[0].sourceline if hit and hasattr(hit[0], "sourceline") else None


def run_schematron(path):
    with tempfile.NamedTemporaryFile(suffix=".svrl") as out:
        subprocess.run([JAVA, "-jar", SCHXSLT_JAR, "-s", str(SCH), "-d", str(path),
                        "-o", out.name], capture_output=True, check=True)
        svrl = etree.parse(out.name)
    tree = etree.parse(str(path))
    errors = warnings = 0
    grouped = {}  # 同じ文面の warning はまとめて 1 行にする（数千件で error が埋もれないように）
    for node in svrl.xpath("//svrl:failed-assert | //svrl:successful-report", namespaces=SVRL):
        text = " ".join("".join(node.xpath("svrl:text//text()", namespaces=SVRL)).split())
        line = location_to_line(tree, node.get("location", ""))
        if node.get("role") == "warning":
            grouped.setdefault(text, []).append(line)
            warnings += 1
        else:
            emit("error", path, line, text)
            errors += 1
    for text, lines in grouped.items():
        more = f"（ほか {len(lines) - 1} か所）" if len(lines) > 1 else ""
        emit("warning", path, lines[0], text + more)
    return errors, warnings


def changed_files(base):
    out = subprocess.run(["git", "diff", "--name-only", "-z", f"{base}...HEAD"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    names = {Path(p).name for p in out.split("\0") if p}
    if names & SHARED or any(p.startswith("schema/") for p in out.split("\0")):
        return sorted(TEI_DIR.glob("*.xml"))
    return sorted(f for f in TEI_DIR.glob("*.xml") if f.name in names)


def main(argv):
    if not (JING_JAR and SCHXSLT_JAR):
        sys.exit("JING_JAR と SCHXSLT_JAR を設定してください（schema/README.md 参照）")
    if argv[:1] == ["--changed-from"]:
        files = changed_files(argv[1])
    elif argv:
        files = [TEI_DIR / a for a in argv]
    else:
        files = sorted(TEI_DIR.glob("*.xml"))
    if not files:
        print("検証対象の XML の変更はありません")
        return 0
    errors = run_jing(files)
    warnings = 0
    for f in files:
        e, w = run_schematron(f)
        errors += e
        warnings += w
    print(f"\n{len(files)} ファイル: error {errors} 件 / warning {warnings} 件")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
