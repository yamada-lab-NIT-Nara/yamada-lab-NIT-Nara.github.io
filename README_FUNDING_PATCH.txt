研究業績ページ：ORCID Funding 連携パッチ（2026-10-19）

最新版ZIPを元に作成。以下3ファイルだけ上書きしてください。
  sync_orcid.py
  .github/workflows/site.yml
  publications.html

GitHub DesktopでCommit → Push origin後、Actions → Publish laboratory website を確認。
ORCID Funding が公開（Everyone）であれば、次回のActionsで data/funding.json が生成されます。
研究費データが未公開・取得不能の場合は空欄案内とし、架空の実績は表示しません。
論文データ data/orcid.json、microCMS、設備スライダー、CSS、NEWSには変更を加えていません。

※ORCID APIの実接続テストはこの環境では行っていません。構文とサンプルレスポンスで検証しています。
※金額・代表分担は不確実なため表示しません。
