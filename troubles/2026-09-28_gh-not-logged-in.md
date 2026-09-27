# GitHub CLI が未ログインで PR を作成できない

- 日付：2026-09-28
- ブランチ：setup/directory-structure
- 状態：未解決（ユーザーによるログイン待ち）

## 何が起きたか

ブランチのプッシュ（`git push`）は成功した。しかし `gh pr create` を実行すると、次のエラーが出てPRを作成できなかった。

```
To get started with GitHub CLI, please run:  gh auth login
```

## 原因

GitHub CLI（`gh`）がどの GitHub アカウントにもログインしていない。
`git push` は Git の認証情報で通るが、`gh` は別の認証が必要になる。

## 対処

- PR はブラウザから作成してもらう：https://github.com/ko-ichimo-ri/Singurality_anime/pull/new/setup/directory-structure
- 恒久的には、ユーザーがターミナルで `gh auth login` を実行する（ブラウザでの認証が必要なため、エージェントからは行えない）

## 再発防止

作業の最初に `gh auth status` を確認する。未ログインなら、PR作成の前にユーザーへ伝える。
