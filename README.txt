研究設備ページ：カテゴリー別表示・2列固定 修正

元データ：2026-10-19に提供された最新版ZIP
上書きするファイルは2つだけです。
  sync_microcms.py
  assets/redesign.css

microCMSの facilities API の「category」フィールドの値ごとに見出しを作り、
各カテゴリー内の設備カードをPCでは2列、スマートフォンでは1列に並べます。
設備が1件だけでもカードを横長に拡大しません。
既存のカテゴリー名をそのまま使用します（microCMSのフィールド追加は不要）。
分類変更はmicroCMSで各設備の category を変更してください。
同じカテゴリーの設備は同じグループに表示されます。
カテゴリーの表示順はsortOrderが最も早い設備の順です。
TOPスライダー関連のコードは変更していません。

反映：GitHub DesktopでCommit→Push origin→GitHub Actions公開完了を待つ。
