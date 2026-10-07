"""BOOTH で配る ZIP を作る。

使い方:
  ~/.venvs/o-calendar-maker/bin/python make_dist.py

初回だけ用意が要る:
  python3 -m venv ~/.venvs/o-calendar-maker
  ~/.venvs/o-calendar-maker/bin/pip install fonttools brotli

ダブルクリックで開いた HTML（file://）からは、Chrome と Firefox が別ファイルの書体を読み込まない。
そのため書体を必要な文字・太さだけに絞って woff2 にし、HTML の中に埋め込む。
出力は dist/ に作る（git の対象外）。
"""

import base64
import io
import re
import sys
import zipfile
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / 'booth' / 'fonts'
DIST = ROOT / 'dist'

# 配布物に入れるファイル（ZIP 内のパス → 中身の作り方）。グロブにせず、ここに全部並べる
LICENSES = ['OFL_KonkhmerSleokchher.txt', 'OFL_NotoSans.txt', 'OFL_NotoSansJP.txt']

LATIN = 'U+0020-007E,U+00A0-00FF,U+2010-2027,U+2030-205E,U+20AC,U+2122'
JAPANESE = LATIN + ',U+3000-30FF,U+3400-4DBF,U+4E00-9FFF,U+F900-FAFF,U+FF00-FFEF'

# Google Fonts を読み込む3行。BOOTH 版では埋め込みの @font-face に置き換える
GOOGLE_FONTS = re.compile(r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\n'
                          r'<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>\n'
                          r'<link href="https://fonts\.googleapis\.com/css2\?[^"]+" rel="stylesheet">\n')


def woff2(path, unicodes, axes=None):
    """書体を、指定の太さ・幅に固定し、指定の文字だけに絞った woff2 にする"""
    font = TTFont(path)
    if axes:
        font = instancer.instantiateVariableFont(font, axes)
    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.layout_features = ['*']
    opts.name_IDs = ['*']
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=subset.parse_unicodes(unicodes))
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = 'woff2'
    font.save(buf)
    return buf.getvalue()


def font_face(family, data, weight, stretch='100%'):
    b64 = base64.b64encode(data).decode('ascii')
    return (f'@font-face {{ font-family: "{family}"; font-weight: {weight}; font-stretch: {stretch}; '
            f'src: url(data:font/woff2;base64,{b64}) format("woff2"); }}')


def build_html(source):
    if not GOOGLE_FONTS.search(source):
        sys.exit('index.html に Google Fonts の読み込み行が見つかりません。make_dist.py の GOOGLE_FONTS を見直してください')
    faces = [
        # 数字と曜日。英数字だけあればよい
        font_face('Konkhmer Sleokchher', woff2(FONTS / 'KonkhmerSleokchher-Regular.ttf', LATIN), 400),
        # クレジットの英数字。Figma と同じ ExtraCondensed Black に固定する
        font_face('Noto Sans', woff2(FONTS / 'NotoSans-Variable.ttf', LATIN, {'wdth': 62.5, 'wght': 900}), 900, '62.5%'),
        # クレジットの日本語。Black に固定する
        font_face('Noto Sans JP', woff2(FONTS / 'NotoSansJP-Variable.ttf', JAPANESE, {'wght': 900}), 900),
    ]
    style = '<style>\n/* BOOTH 版: 書体を埋め込み（SIL Open Font License。licenses/ を参照） */\n' + '\n'.join(faces) + '\n</style>\n'
    return GOOGLE_FONTS.sub(lambda _: style, source, count=1)


def readme(version):
    return f"""O/ Calendar Maker {version}
made by ODD DEsigN

■ これは何？
イラストを入れて、スマホの待受や印刷用のカレンダーを作るツールです。

■ 使い方
1. 「O-Calendar-Maker.html」をダブルクリックして、ブラウザで開きます
   （Chrome・Safari・Edge・Firefox の新しい版で動きます）
2. 年月を選び、イラストの画像を入れます（背景を透過した PNG がおすすめです）
3. 色を選びます（プリセット・おすすめ・ランダム）
4. サイズ（待受・はがき・2L判・A4）と形式（PNG・PDF）を選んで保存します

■ できること
・イラストを「裏（帯の後ろ）」「表（帯の前）」の2枚まで重ねられます
・差分の画像に差し替えても、位置と大きさはそのままです
・日本の伝統色から作った152通りの色の組み合わせと、月ごとのおすすめ
・土日・祝日の色付け（振替休日なども計算します）
・週の始まり（月曜・日曜）、曜日の表記、書体を変えられます
・印刷サイズは 300dpi で書き出します

■ 知っておいてほしいこと
・インターネットにつながっていなくても使えます
・画像はこのパソコンの中だけで処理され、どこにも送信されません
・作業内容はブラウザに保存されます。ブラウザのデータを消すと消えます
・印刷所に入稿するための塗り足し（周囲の余白）は付きません

■ スマホで使いたいとき
Web 版をスマホのブラウザで開いてください。
https://maximaworks18-source.github.io/o-calendar-maker/

■ 利用について
・このツールは無料で使えます。個人・商用を問いません
・作ったカレンダーの画像や PDF は、販売・配布・SNS への投稿など、商用利用を含めて自由に使えます。クレジット表記は不要です
・カレンダーに使ったイラストや書体の権利は、それぞれの権利者にあります。他の人のイラストや、商用利用できない書体を使うときは、その権利者のルールに従ってください
・ツール本体（このフォルダのファイル）の再配布・転売・改変しての配布はご遠慮ください
・イラストや写真など、自分の作品を入れずに作ったカレンダーを、テンプレートや素材として配布・販売することはご遠慮ください（自分で使うのは自由です）
・このツールを使ったことで起きたトラブルや損害について、制作者は責任を負いかねます
・内容は予告なく変わることがあります

■ 書体について
SIL Open Font License の書体を埋め込んでいます（licenses フォルダを参照）。
・Konkhmer Sleokchher
・Noto Sans
・Noto Sans JP

気に入ったら、BOOTH の BOOST で応援してもらえるとうれしいです。
"""


def text_bytes(text):
    # Windows のメモ帳でも文字化けしないように BOM 付き UTF-8 にする
    return b'\xef\xbb\xbf' + text.replace('\r\n', '\n').encode('utf-8')


def main():
    source = (ROOT / 'index.html').read_text(encoding='utf-8')
    m = re.search(r"const VERSION = '(v[\d.]+)';", source)
    if not m:
        sys.exit('index.html に VERSION が見つかりません')
    version = m.group(1)
    folder = f'O-Calendar-Maker_{version}'

    files = {
        f'{folder}/O-Calendar-Maker.html': build_html(source).encode('utf-8'),
        f'{folder}/はじめに読む.txt': text_bytes(readme(version)),
        f'{folder}/変更履歴.txt': text_bytes((ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')),
    }
    for name in LICENSES:
        files[f'{folder}/licenses/{name}'] = (FONTS / name).read_bytes()

    DIST.mkdir(exist_ok=True)
    out = DIST / f'{folder}.zip'
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for path, data in files.items():
            z.writestr(path, data)

    # 中身を展開したものも置いておく（動作確認用）
    for path, data in files.items():
        dest = DIST / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    print(f'{out.relative_to(ROOT)}  {out.stat().st_size / 1024 / 1024:.1f} MB')
    for path, data in files.items():
        print(f'  {path}  {len(data) / 1024:.0f} KB')


if __name__ == '__main__':
    main()
