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
        xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:local="urn:engishiki:local"
        queryBinding="xslt2">

  <ns prefix="tei" uri="http://www.tei-c.org/ns/1.0"/>
  <ns prefix="local" uri="urn:engishiki:local"/>

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
  <let name="taxIds" value="distinct-values(doc(concat($dir, 'engishiki_taxonomy_standoff_master.xml'))//@xml:id)"/>
  <let name="isShared" value="base-uri(/) = (for $d in $shared return base-uri($d))"/>
  <let name="knownIds" value="distinct-values((//@xml:id, $shared//@xml:id, $vol//@xml:id))"/>

  <!-- 物品の名前と読み（ひらがな）。同名・同読みの検出に使う -->
  <xsl:function name="local:reading" as="xs:string">
    <xsl:param name="t" as="element()"/>
    <xsl:sequence select="normalize-space(string(($t/tei:desc//tei:orth[@type = 'ひらがな'])[1]))"/>
  </xsl:function>
  <xsl:function name="local:nameReading" as="xs:string">
    <xsl:param name="t" as="element()"/>
    <xsl:sequence select="concat(normalize-space($t/tei:desc/tei:name), '|', local:reading($t))"/>
  </xsl:function>
  <xsl:key name="tax-name-reading" match="tei:taxonomy[tei:desc/tei:name]" use="local:nameReading(.)"/>
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

  <pattern id="manifest">
    <title>facsimile にその巻の IIIF マニフェストが書かれているか</title>
    <!-- サイトの画像ビューアは facsimile/@source のマニフェストを読む。
         無いと、その巻の画像が一枚も表示されない（巻8・36 で発生） -->
    <rule context="tei:facsimile">
      <let name="n" value="replace(base-uri(/), '^.*/engishiki_v(\d+)\.xml$', '$1')"/>
      <let name="expected" value="concat('https://iiif.rekihaku.ac.jp/api/manifests/shiryo/H-743-74-', $n)"/>
      <assert test="@source" role="error">
        facsimile に source（IIIF マニフェストの URL）がありません。
        画像が表示されなくなります。例: &lt;facsimile source="<value-of select="$expected"/>"&gt;
      </assert>
      <assert test="not(@source) or not(matches(base-uri(/), 'engishiki_v\d+\.xml$')) or @source = $expected" role="error">
        facsimile の source が巻の番号と合っていません（<value-of select="@source"/>）。
        この巻では <value-of select="$expected"/> のはずです。
      </assert>
    </rule>
  </pattern>

  <pattern id="commodity">
    <title>物品（@commodity）が taxonomy の ID で書かれているか</title>
    <!-- 巻23 は名前（#筆）、巻24 は ID（#noun…）で書かれていて、サイトの表示が食い違った。
         統合で消えた ID を使い続けている巻も、ここで分かる -->
    <rule context="tei:*[@commodity]">
      <let name="toks" value="tokenize(normalize-space(@commodity), ' ')"/>
      <let name="notId" value="$toks[not(matches(., '^#noun\d+$'))]"/>
      <let name="missing" value="$toks[matches(., '^#noun\d+$') and not(substring(., 2) = $taxIds)]"/>
      <assert test="empty($notId)" role="error">
        物品が taxonomy の ID ではなく、名前などで書かれています（commodity="<value-of select="string-join($notId, ' ')"/>"）。
        #noun… の形の ID で書いてください。
      </assert>
      <assert test="empty($missing)" role="error">
        物品の ID <value-of select="string-join($missing, ' ')"/> が taxonomy にありません。
        統合・削除した ID を使っていないか、確かめてください。
      </assert>
    </rule>
  </pattern>
  <pattern id="relation">
    <title>relation（物品の上下関係など）の「#」参照の行き先が存在するか</title>
    <!-- standOff の地名などに、すぐ直せないものが残っているため、当面は警告のみ -->
    <rule context="tei:relation[@active | @passive | @mutual]">
      <let name="bad"
           value="for $t in tokenize(normalize-space(string-join((@active, @passive, @mutual), ' ')), ' ')
                  return if (starts-with($t, '#') and not(substring($t, 2) = $knownIds)) then $t else ()"/>
      <assert test="empty($bad)" role="warning">
        relation の参照先 <value-of select="string-join($bad, ' ')"/> が見つかりません。
        統合・削除した ID が残っていないか、確かめてください。
      </assert>
    </rule>
  </pattern>
  <pattern id="same-name">
    <title>taxonomy に、名前も読みも同じ物品が二つ以上ないか</title>
    <!-- 稷米・黍米・秫米が、上位の分類だけ違う別 ID で二重に登録されていた（PR #479 で統合）。
         名前が同じでも読みが違うもの（粱米・麩）は、別の物品として扱う決まりなので対象外 -->
    <rule context="tei:taxonomy[tei:desc/tei:name]">
      <let name="same" value="key('tax-name-reading', local:nameReading(.)) except ."/>
      <report test="exists($same)" role="error">
        物品「<value-of select="normalize-space(tei:desc/tei:name)"/>」（<value-of select="@xml:id"/>、読み: <value-of select="local:reading(.)"/>）と
        同じ名前・同じ読みの物品が、<value-of select="string-join($same/@xml:id, ' ')"/> にも登録されています。
        同じ物品なら一つに統合し、別の物品なら読みを変えてください。
      </report>
    </rule>
  </pattern>
</schema>
