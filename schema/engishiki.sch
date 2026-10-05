<?xml version="1.0" encoding="UTF-8"?>
<!--
  延喜式TEI プロジェクト固有のチェック規則（Schematron）

  tei_all.rng は TEI として正しい形かどうかしか見ない。
  ここでは「延喜式のデータとして壊れていないか」を見る。

  role="error"   … 直すまで PR を通さないもの
  role="warning" … 表示はするが PR は止めないもの（扱いが未決定のもの）

  対象: TEI編集用/ の XML。チェックのしかたは schema/README.md を参照。
-->
<schema xmlns="http://purl.oclc.org/dsdl/schematron"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
        queryBinding="xslt2">

  <ns prefix="tei" uri="http://www.tei-c.org/ns/1.0"/>

  <!-- 全巻で共有する ID の定義元。同じフォルダにあるものを読む -->
  <let name="dir" value="replace(base-uri(/), '[^/]+$', '')"/>
  <let name="shared"
       value="(doc(concat($dir, 'engishiki_standOff.xml')),
               doc(concat($dir, 'engishiki_taxonomy_standoff_master.xml')),
               doc(concat($dir, 'engishiki_header_all.xml')))"/>
  <!-- engishiki_v39_en.xml などは、本文 engishiki_v39.xml の ID を指す -->
  <let name="volFile"
       value="replace(base-uri(/), '^.*/(engishiki_v\d+)_[a-z]+\.xml$', '$1.xml')"/>
  <let name="vol"
       value="if (matches($volFile, '^engishiki_v\d+\.xml$') and doc-available(concat($dir, $volFile)))
              then doc(concat($dir, $volFile)) else ()"/>
  <let name="sharedIds" value="distinct-values($shared//@xml:id)"/>
  <let name="isShared" value="base-uri(/) = (for $d in $shared return base-uri($d))"/>
  <let name="knownIds" value="distinct-values((//@xml:id, $shared//@xml:id, $vol//@xml:id))"/>

  <pattern id="pointer">
    <title>「#」で始まる参照の行き先が存在するか</title>
    <rule context="tei:*[@corresp | @target | @wit | @sameAs | @source]">
      <let name="bad"
           value="for $t in tokenize(normalize-space(string-join((@corresp, @target, @wit, @sameAs, @source), ' ')), ' ')
                  return if (starts-with($t, '#') and not(substring($t, 2) = $knownIds)) then $t else ()"/>
      <assert test="empty($bad)" role="error">
        <name/> の参照先 <value-of select="string-join($bad, ' ')"/> が見つかりません。
        綴りの誤りか、standOff / taxonomy への登録漏れです。
      </assert>
    </rule>
  </pattern>

  <pattern id="ana">
    <title>@ana の「#」参照（扱いが未決定のため警告のみ）</title>
    <rule context="tei:*[@ana]">
      <let name="bad"
           value="for $t in tokenize(normalize-space(@ana), ' ')
                  return if (starts-with($t, '#') and not(substring($t, 2) = $knownIds)) then $t else ()"/>
      <assert test="empty($bad)" role="warning">
        <name/> の ana="<value-of select="string-join($bad, ' ')"/>" に対応する定義がありません。
      </assert>
    </rule>
  </pattern>

  <pattern id="shared-id">
    <title>本文で、共有ファイルと同じ xml:id を定義していないか</title>
    <!-- teiHeader は header_all の写しを各ファイルが持つ決まりなので対象外 -->
    <rule context="tei:text//tei:*[@xml:id] | tei:standOff//tei:*[@xml:id]">
      <report test="not($isShared) and @xml:id = $sharedIds" role="error">
        xml:id="<value-of select="@xml:id"/>" は standOff / taxonomy / header_all でも定義されています。
        どちらを指しているのか分からなくなるので、別の ID にしてください。
      </report>
    </rule>
  </pattern>

  <pattern id="image-url">
    <title>画像の URL が歴博 IIIF サーバを指しているか</title>
    <rule context="tei:graphic[@url] | tei:pb[@facs and not(starts-with(@facs, '#'))]">
      <let name="u" value="(@url, @facs)[1]"/>
      <assert test="starts-with($u, 'https://iiif.rekihaku.ac.jp/')" role="error">
        画像の URL が https://iiif.rekihaku.ac.jp/ で始まっていません（<value-of select="$u"/>）。
        旧サーバ（khirin-a など）の URL は使えません。
      </assert>
    </rule>
  </pattern>

</schema>
