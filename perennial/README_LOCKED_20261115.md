# 星めぐり天文暦｜通年生成 Python 正式LOCKED（2026-11-15）

## 正式原本の所在
ChatGPTライブラリ:
`/ホシトウラナイ/01B_星めぐり天文暦2027/06_正式版/星めぐり天文暦_通年生成_正式LOCKED_20261115.zip`

ライブラリ内リンク:
https://chatgpt.com/library?file_id=libfile_dcf0e800e21481918a9ca4db6dc02154

ZIP SHA-256:
`253c6ae6b04187832319ba2bad29e56aec556cc7b22441cd7b595e3e1868dc15`

これはプログラム原本・指定年の実出力・検査記録を含む復元ZIPへの管理索引です。
**ZIPのコードはGitHubにはまだ一式アップロードしていません。**
GitHubにある2027年LOCKED v3とは別の成果物で、旧原本は無変更。

## 実行
ZIPを展開しPythonの依存環境をそろえた上で:
```sh
python build_year.py --year 2028 --months all
python build_year.py --year 2029 --months all
```
各年: 表紙・年間図・月間12枚・水星詳細の計15枚およびイベント一覧。日食・月食計算は同梱の計算コードを使用。
外部暦との比較は抜き取り検証に限る。検査条件と依存環境はZIP内の`LOCKED_README.md`、`validation/`参照。

## 保全上の注意
2027年のLOCKED v3を変更しない。ZIP内の`SHA256_MANIFEST_LOCKED.json`で各ファイルを照合する。実際の再生成・SHA一致を確認した場合にのみ復元PASSを記載する。
