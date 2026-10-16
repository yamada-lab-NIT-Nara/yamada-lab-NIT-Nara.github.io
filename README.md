# 山田研究室ウェブサイト（無料公開・自動更新対応）

## 無料公開する（GitHub Pages）
1. https://github.com/signup で無料アカウントを作成。
2. New repository → `yamada-lab-website`（Public）→ Create repository。
3. このフォルダーの**中身**（`.github` フォルダーも含む）をリポジトリの `main` ブランチへアップロード。GitHubのWeb画面では隠しフォルダー `.github` を含めてアップロードすること。
4. Settings → Pages → Build and deployment → Source を **GitHub Actions** に変更。
5. Actions → `Publish laboratory website` → Run workflow（または main への push で公開）。
6. 公開URLは `https://<GitHubユーザー名>.github.io/yamada-lab-website/`。

## researchmapと連携する
- 公開業績用のWeb API利用には、JSTへの申請・承認が必要です。承認前は絶対に定期取得を有効にしないでください。
- 参照: https://researchmap.jp/outline/notice/Terms_of_Service_for_the_researchmap_Web_API_Jpn.pdf
- 承認後に、APIの認証方法・利用範囲・IP制限についてJSTの指示に合わせて `sync_researchmap.py` を確認・調整します。GitHub Actionsの共有IPが利用不可の場合は実行先の再検討が必要です。
- 承認後、GitHubの Settings → Secrets and variables → Actions → Variables → New repository variable に `RESEARCHMAP_API_APPROVED=true` を登録。
- 発行されたトークンが必要な場合は Secrets に `RESEARCHMAP_API_TOKEN` として登録。**HTMLやリポジトリには絶対にトークンを書かないこと。**
- 毎日1回のスケジュール（日本時間11時23分ごろ、遅延あり）で公開済み論文・学会発表・受賞を取得。取得失敗時は直前のデータを維持します。
- 実際のAPIレスポンスのフィールド構造が仕様と異なる場合は `sync_researchmap.py` の項目マッピングを調整してください。現時点ではAPI承認・実接続テストは未実施です。

## 注意
- `index.html` には代表論文3件の手動記述が初期表示として残っています。承認後、正常なJSON取得が完了すると論文欄を自動更新します。
- 学生の氏名・写真、校章、共同研究先の情報は公開許可を確認してください。
- 現在のサイトは試作版です。正式公開前に所属・部屋番号・学位・論文表記を確認してください。
