# microCMS × GitHub Pages — 運用と確認

サービス: `yamada-lab-nara` / API: `news`, `seeds` / GitHub Secret: `MICROCMS_API_KEY`

## 仕組み

`Publish laboratory website` が起動すると、`sync_microcms.py` が公開中のmicroCMSコンテンツを取得し、既存のHTMLテンプレートに**追加**します。NEWSはTOPページ・NEWS一覧・`news/<id>.html`、研究シーズはTOPの横スライダー・研究シーズ案内・`seeds/<id>.html` に反映します。既存のNEWS記事、シーズ3件、写真、ORCID連携は維持します。既存の手書き記事とIDが重なる場合、その記事HTMLは上書きしません。

## 最初の動作確認

1. このZIP内のファイルを、**ディレクトリ構造を保ったまま**GitHubリポジトリのルートにアップロードしてコミットします。特に `.github/workflows/site.yml` と `cms/templates/` が重要です。
2. GitHub → Actions → **Publish laboratory website** → Run workflow を実行します。
3. `publish` の **Generate NEWS and research seeds from microCMS** を開き、`microCMS API fetch successful: news=1, seeds=0` のような行を確認します（件数は実データ次第）。
4. デプロイ完了後、TOPのNEWSに「CMS連携テスト」が表示され、リンク先の独立記事が開けるか確認します。研究シーズも登録後に同様に確認できます。

## 注意

- CMSの記事は公開済みである必要があります。APIキーはGitHub Secretsだけに保存し、ファイルやチャットに書かないでください。
- **CMSからの同期はGitHub Actions実行時のみ**。microCMS公開直後のWebhookは未設定です。日次実行と手動実行で更新します。
- CMSの画像はmicroCMS画像CDNを参照します。既存記事の外部画像リンク切れはこの変更では解決しません。
- NEWS/シーズのレイアウト変更は `cms/templates/index.html`、`cms/templates/news.html`、`cms/templates/seeds.html` にも反映してください。ビルド時にこれらを基にHTMLを再生成します。
- microCMSへの既存記事の全面移行は未実施です。移行完了まではCMS未登録の既存記事を消さない運用です。
- 失敗時はデプロイを停止します。GitHub Actionsのログに表示されるエラーを確認してください。
- ORCIDの処理は既存ワークフローのままです。
