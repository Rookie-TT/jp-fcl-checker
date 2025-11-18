# GitHub デプロイ手册（5分で完了）

## ステップ1: リポジトリ作成
1. GitHub にログイン
2. "New repository" クリック
   [擬似スクリーンショット: GitHub ダッシュボードの緑の "New" ボタン]

3. 名前: `jp-fcl-checker` (推奨)
4. Public にチェック、Create repository
   [擬似スクリーンショット: リポジトリ作成フォーム、名前入力欄]

## ステップ2: ファイルアップロード
1. リポジトリのメイン画面で "uploading an existing file" または "Add file > Upload files"
   [擬似スクリーンショット: リポジトリの空ページ、"Add file" ドロップダウン]

2. すべてのファイルをドラッグ&ドロップ (index.html, style.css 等)
3. Commit changes (メッセージ: "Initial commit")
   [擬似スクリーンショット: ファイルリスト + 緑の "Commit changes" ボタン]

## ステップ3: GitHub Pages アクティベート
1. リポジトリ > Settings タブ
2. 左メニュー "Pages"
   [擬似スクリーンショット: Settings ページの左サイドバー、"Pages" 選択]

3. Source: Deploy from a branch > main > / (root) > Save
   [擬似スクリーンショット: Pages 設定フォーム、Branch 選択ドロップダウン]

4. 30秒待機後、URL 表示: https://yourusername.github.io/jp-fcl-checker/
   [擬似スクリーンショット: Pages セクションの緑チェック + URL 表示]

## ステップ4: テスト
ブラウザで URL 開き、住所入力 → 結果確認
- 問題? Logs でデバッグ (Actions タブ)

## トラブルシュート
- 404 エラー: Branch が main か確認
- スタイル崩れ: CSS ファイル名大文字小文字確認

完成! 日本ユーザーへ共有開始。
[擬似スクリーンショット: 最終 URL ページの成功メッセージ]