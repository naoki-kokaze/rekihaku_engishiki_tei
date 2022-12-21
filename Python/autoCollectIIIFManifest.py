from bs4 import BeautifulSoup
import json
import requests
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# 関数

def createXml(manifest, id_format="{}"):

  baseText = r'''
        <facsimile></facsimile>
  '''

  soup = BeautifulSoup(baseText, "xml")

  facsimile = soup.find("facsimile")
  facsimile["source"] = manifest

  # manifestのロード

  manifest_data = requests.get(manifest).json()
  canvases = manifest_data["sequences"][0]["canvases"]

  for canvas in canvases:
      prefix = canvas["images"][0]["resource"]["service"]["@id"]
      image = prefix + "/full/full/0/default.jpg"
      canvasId = canvas["@id"]

      # canvasのIDの末尾をxml:idとして扱います。データや用途に応じて、適宜変更してください。
      id = id_format.format(canvasId.split("/")[-1])

      surface_text = r'''
      <surface source="{}" xml:id="{}">
      <graphic url="{}"/>
      </surface>
      '''.format(canvasId, id, image)

      surface = BeautifulSoup(surface_text, "xml")
      facsimile.append(surface)

  return soup

def main(manifest, output_file, id_format="{}"):
  # 以下、実行
  xml = createXml(manifest, id_format)

  f = open(output_file, "w")
  f.write(xml.prettify())
  f.close()


# 延喜式（国立歴史民俗博物館）の例
manifest = "https://khirin-a.rekihaku.ac.jp/iiif/rekihaku/H-743-74-1/manifest.json"
output_file = "engishiki_1.xml"
main(manifest, output_file)