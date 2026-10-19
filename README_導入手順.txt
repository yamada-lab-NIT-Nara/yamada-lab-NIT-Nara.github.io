研究設備のCMS完全連携・レイアウト修正（2026-10-19）

今回の差し替えは3ファイルだけです。ZIPのフォルダ構造に従って上書きしてください。
  sync_microcms.py
  assets/redesign.css
  cms/templates/facilities.html

変更点:
- 設備カードはすべてfacilities APIの公開データから生成（HTMLのFE-SEM/XPSカードは残さない）
- 研究環境の総合紹介だけ設備一覧の下に独立して残す
- 実機写真の表示高さを230pxに制限（スマートフォン200px）
- 主な用途を縦のリストに整形
- TOPのスライダー、メンバー、NEWS、研究シーズには変更なし

注意: microCMSに登録していないXPSは設備一覧に表示されません。
CMSにXPSを登録・公開すると次回のGitHub Actions実行時に自動追加されます。
GitHub DesktopでCommit→Push origin後、Actionsの完了を確認してください。
