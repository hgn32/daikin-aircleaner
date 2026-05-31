# Daikin Air Cleaner - Home Assistant カスタムコンポーネント

ダイキン製空気清浄機をHome Assistantで制御するためのカスタムコンポーネントです。ローカルネットワーク経由でHTTP APIを使って機器と通信します。

## 対応機器

- ダイキン 空気清浄機（ローカルHTTP APIに対応しているモデル）
  - 例: MCK70X、MCK55X など（加湿空気清浄機シリーズ）

## 機能

- **ファンエンティティ**: 電源のオン/オフ、運転モードの切り替え
- **セレクトエンティティ**: 風量・加湿レベルの個別制御
- **バイナリセンサー**: 給水タンクの満水検知
- **カスタムカード**: タップで開くボトムシートダイアログ

### 運転モード

| モード | 説明 |
|--------|------|
| おまかせ | 自動で最適運転 |
| 手動 | 風量・加湿を手動設定 |
| 節電 | 省エネ運転 |
| 花粉 | 花粉対策運転 |
| のど/はだ | 肌・のどうるおい運転 |
| サーキュ | サーキュレーション運転 |

## インストール

### HACS（推奨）

1. HACSを開き、「カスタムリポジトリ」から `https://github.com/hgn32/daikin-aircleaner` を追加します。
2. カテゴリは「Integration」を選択します。
3. 「Daikin Air Cleaner」をインストールします。
4. Home Assistantを再起動します。

### 手動インストール

1. `custom_components/daikin_aircleaner/` を HA の `<config>/custom_components/` にコピーします。
2. Home Assistantを再起動します。

## 設定

1. 「設定」→「デバイスとサービス」→「統合を追加」
2. 「Daikin Air Cleaner」を検索して選択
3. IPアドレスと名前を入力

## カスタムカード

Lovelaceリソースに追加：

```yaml
resources:
  - url: /daikin_aircleaner/daikin-aircleaner-card.js
    type: module
```

カード設定例：

```yaml
type: custom:daikin-aircleaner-card
entity: fan.living_air_cleaner
airvol_entity: select.living_air_cleaner_airvol
humd_entity: select.living_air_cleaner_humd
```

## ライセンス

MIT License
