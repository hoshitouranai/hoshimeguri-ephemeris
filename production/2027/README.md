2027年版・制作中

原本: hoshimeguri_annual_monthly_SHARED_LOCKED_20261028.zip (SHA-256 622f619145b313da5d831d777a0893976974728730901ed6e99843284e67de6b)。作業用に展開し、git apply で renderer.patch を適用。prototype/monthly/data を monthly/data にコピー。

依存: numpy, scipy, pyswisseph, matplotlib, Pillow。Noto Sans CJK JP と FreeSerif（HOSHIMEGURI_SYMBOL_FONT で指定可）。V53_EPHE_DIR に Swiss Ephemeris データを指定。

python annual/annual_engine.py --year 2027 --output annual-2027.png
python monthly/render_month_COLOR_FLOW_TRIAL.py --month 1 （1〜12を指定）

検査: 原本の107件ハッシュ一致。年間図と全12か月を生成（DejaVu Sans使用）。年間の座標・矢印・キロン計算とCSVが変更前後で一致。月間終点は月末23:59 JST。採用v53との画素一致、A4実測、全頁目視、2028年、復元検証は未完。
