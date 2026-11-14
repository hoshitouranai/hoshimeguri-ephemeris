# 通年生成 Python ソース（2026-11-15 正式LOCKED由来）

正式な保全原本はChatGPTライブラリの『星めぐり天文暦_通年生成_正式LOCKED_20261115.zip』。このディレクトリは同梱Pythonコードと実行に必要な素材のGitHub再配布用ミラーです。

## 実行
Python 3.11+ と numpy, scipy, matplotlib, pyswisseph, Pillow, PyMuPDF を用意し、OSに Noto Sans CJK および FreeSerif をインストールします（フォントはこのリポジトリに含まれません）。

```bash
cd perennial/source
python build_year.py --year 2028 --months all
python build_year.py --year 2029 --months all
```

年指定対応範囲はコード上1900〜2099。実測の全月正常終了は2028年・2029年。日食・月食、天体位置の外部照合は抜き取り検査で、全年度の検証ではありません。

- annual_work/colors_v17.zip は大型2027年資料ZIPから、描画エンジンが読む承認色CSVのみを同じバイトで抽出した縮約版です。2028年の年間図を正式原本のPNGとSHA-256照合して完全一致を確認しています。元のLOCKED ZIPは変更していません。
- ephe/seas_18.se1 はキロン計算に使用する天体暦の素材です。
- 公開GitHubへのアップロードは、Swiss Ephemeris のライセンスと、同梱元コードの著作権表示を維持した形です。
- 出力画像・2027年イベントCSV・販売PDFはミラーに含めていません。`data/` と `output/` は生成時に作成されます。
- 年間図コード中に「試作」「未承認」等の検査状態コメントが残っています。それらは元LOCKED由来のソースを無断変更しないために保持しています。

正式原本： https://chatgpt.com/library?file_id=libfile_dcf0e800e21481918a9ca4db6dc02154
