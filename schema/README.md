# TEI の自動チェック

`TEI編集用/` の XML は、プルリクエスト（PR）を出すと GitHub 上で自動的にチェックされます。
問題があると、PR の画面に赤い ✗ が付きます。

## 何をチェックしているか

1. **TEI として正しい形か**（TEI 公式の `tei_all.rng`、版 4.12.0）
2. **延喜式のデータとして壊れていないか**（このフォルダの `engishiki.sch`）
   - `corresp` `target` `wit` `sameAs` `source` の `#…` が、実在する `xml:id` を指しているか。
     探す範囲は、そのファイル自身、`engishiki_standOff.xml`、`engishiki_taxonomy_standoff_master.xml`、
     `engishiki_header_all.xml` です。`_en` / `_ja` のファイルでは、同じ巻の本文ファイルも探します。
   - 本文（`text`）の中で、standOff などと同じ `xml:id` を使っていないか
   - 画像の URL（`graphic/@url`、`pb/@facs`）が `https://iiif.rekihaku.ac.jp/` で始まっているか
   - `facsimile` に、その巻の IIIF マニフェスト（`source="https://iiif.rekihaku.ac.jp/api/manifests/shiryo/H-743-74-<巻>"`）が書かれているか。
     無いと、サイトでその巻の画像が一枚も表示されません
   - `facsimile` に、その巻の IIIF マニフェスト（`source`）が書かれているか
   - 物品（`commodity`）が taxonomy の ID（`#noun…`）で書かれていて、その ID が taxonomy にあるか。
     統合・削除した ID を使い続けている巻も、ここで分かります
   - taxonomy に、名前も読み（ひらがな）も同じ物品が二つ以上ないか。
     名前が同じでも読みが違うもの（粱米・麩など）は、別の物品として扱うので対象外です
   - `relation` の `active` `passive` `mutual` の `#…` が、実在する `xml:id` を指しているか（**警告のみ**）
   - `ana` の `#…` が定義されているか（扱いが決まっていないため、**警告のみ**。✗ にはなりません）

PR では、その PR で変更したファイルだけをチェックします。
ただし standOff・taxonomy・header_all を変更したときは、全ファイルをチェックします。

## ✗ が付いたら

PR の「Checks」タブ →「validate TEI」を開くと、次のような行が出ています。

```
TEI編集用/engishiki_v39.xml:2598: error: orgName の参照先 #内侍司 が見つかりません。
```

`2598` が行番号です。Oxygen でそのファイルを開き、行へ移動（Ctrl/⌘ + L）して直してください。
直して push し直すと、もう一度チェックされます。

## Oxygen で、PR を出す前に確かめる

1. チェックしたいファイルを開く
2. メニューの Document → Validate → Validate with… を選ぶ
3. スキーマに、このフォルダの `engishiki.sch` を指定する

結果は画面下の一覧に出ます。

## 手元のコマンドで確かめる（任意）

Java と Python（lxml）が必要です。jar は workflow（`.github/workflows/validate.yml`）と同じものを使います。

```
JING_JAR=<jing.jar の場所> SCHXSLT_JAR=<schxslt の cli jar の場所> python3 schema/validate.py engishiki_v8.xml
```

ファイル名を省くと全ファイルをチェックします。

## 規則を足すとき

`engishiki.sch` に `<pattern>` を足します。文面は作業者が読んで直せるように、日本語で書いてください。
すぐに直せない規則は `role="warning"` にして、データが揃ってから `error` に上げます。
