2027年星めぐり天文暦 1月 外周変更試作 / WORKING・未承認

出典：月別v17 LOCKED（原本は一切変更していない）
変更：12サイン背景をアプリ基本色20%＋白80%、サイングリフ色と濃紺アウトラインにする。角度配置、右側表、天体軌跡は変更しない。
原本の再生成：original/render_month_LOCKED.py --month 1
変更版の再生成：trial/render_month_LOCKED.py --month 1
依存：numpy, scipy, pyswisseph, matplotlib、Noto Sans CJK JPおよびFreeSerif、Swiss Ephemerisのデータとパス。使用環境に応じてパスを調整する必要がある。
重要：描画上の月末表記と軌跡の終点（翌月1日00:00 JST）の一致問題は未解決。
検査：2027年1月のみ。内部・外周外側の画素差0。年次・印刷・全文字可読性検査は未実施。
