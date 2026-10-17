# microCMS連携

- サービスID: `yamada-lab-nara`
- リスト形式 API: `news` と `seeds`
- GitHub Actions Secret: `MICROCMS_API_KEY`
- GitHub Actions → Publish laboratory website → Run workflow で即時反映を実行。定期実行は既存の日次スケジュールです。
- microCMSの公開直後に自動反映するWebhookは**未設定**です。必要なら後から追加してください。
- 既存の手作業記事・画像・研究シーズのHTMLは維持し、CMS登録分を追加します。
- `cms/templates/` は元のTOP/NEWS/研究シーズページのテンプレートです。**今後のレイアウト修正はこの3ファイルを編集**してください。
- CMS記事のIDは `news/<id>.html` / `seeds/<id>.html` に対応します。既存の手書きページと同じIDのときは上書きしません。
- CMSの画像は現状microCMS CDNのURLを使います。画像のGitHub内保存は未実装です。
- セキュリティ: APIキーはSecretsにのみ設定。公開HTMLには埋め込みません。
- CMS側の `body` はリッチエディタHTMLを利用します。
- エラー時はデプロイを中止します。APIキーが未設定・スキーマが不一致の場合はActionsログを確認してください。
- 既存のORCID同期ワークフローを残しています。
