# 星めぐり天文暦｜通年生成・水星2027年デザイン統一 v2（正式LOCKED）
固定日: 2026-11-15 JST

## 正式原本
ChatGPTライブラリ:
`/ホシトウラナイ/01B_星めぐり天文暦2027/06_正式版/星めぐり天文暦_通年生成_水星統一v2_正式LOCKED_20261115.zip`

[ライブラリの正式原本](https://chatgpt.com/library?file_id=libfile_36949bb2dc988191a6a4974cbdde5b06)

ZIP SHA-256:
`eb32ea3455f9b16374263476e888a1b26a2b9a09fcf6abfdd0e28b651b2e1953`

## Pythonソース
[GitHub v2 Pythonと素材](https://github.com/hoshitouranai/hoshimeguri-ephemeris/tree/main/perennial/v2_mercury_2027_style_WORKING)

フォルダ名は変更しないが、v2のコードを使用した正式復元ZIPはLOCKED済み。GitHub上のディレクトリにある生成コードを更新する場合は、必ず別バージョンとし原本ZIPは変更しない。

## 検査
保存済みZIPをライブラリから再取得。
- ZIP SHA-256一致
- 内部218ファイル SHA-256一致
- 取り出したコードで `python build_year.py --year 2028 --months all` を完走（exit 0、15枚SHA一致）
- 同じく2029年を完走（exit 0、15枚SHA一致）
- 合計30 PNGを原本と機械的照合

復元記録:
`/ホシトウラナイ/01B_星めぐり天文暦2027/06_正式版/星めぐり天文暦_水星統一v2_LOCKED_復元検証_PASS_20261115.json`

## 制約
2028・2029年の再現性を確認した。全年全日全イベントの独立外部暦照合は実施していない。2027年LOCKED v3および通年生成v1の原本は無変更。
