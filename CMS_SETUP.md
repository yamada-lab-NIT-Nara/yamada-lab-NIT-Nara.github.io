# 山田研究室 microCMS 更新手順

## CMS API
- news: NEWS、記事詳細
- seeds: 研究シーズ、詳細
- members: 教員プロフィール・学生一覧

## GitHub Secrets
`MICROCMS_API_KEY` にmicroCMSの読み取り可能なAPIキーを設定します。キーは公開ファイルに書きません。

## GitHub Actions
`.github/workflows/site.yml` が毎日・mainへのpush・手動実行でCMSを取得し、GitHub Pagesへデプロイします。microCMSを更新した直後は Actions > Publish laboratory website > Run workflow で反映できます。

## 注意
- `cms/templates/` がデザインの原本です。生成された `index.html`, `news.html`, `seeds.html`, `members.html` を編集しても次回の生成で上書きされます。
- CMSに登録したNEWS・研究シーズのみ一覧に表示します。CMS未移行の古い記事はバックアップとしてファイルに残りますが、一覧には出ません。
- 教員の詳細は `members/<CMS ID>.html`、学生は `members.html` の年度付き一覧です。
- CMSのAPIキーには news, seeds, members のGET権限が必要です。
- 公開前に `MICROCMS_API_KEY` とGitHub Pages設定を確認してください。
