# Daikin Air Cleaner - Home Assistant カスタムコンポーネント

ダイキン製空気清浄機をHome Assistantで制御するためのカスタムコンポーネントです。ローカルネットワーク経由でHTTP APIを使って機器と通信します。

## 対応機器

- ダイキン 空気清浄機（ローカルHTTP APIに対応しているモデル）
  - 例: MCK70X、MCK55X など（加湿空気清浄機シリーズ）

## 機能

- **ファンエンティティ**: 電源のオン/オフ、運転モードの切り替え
- **セレクトエンティティ**: 風量・加湿レベル・LEDディスプレイ輝度の個別制御
- **センサーエンティティ**: 室温・室内湿度・PM2.5・ほこり・におい
- **バイナリセンサー**: 給水タンクの補給お知らせ
- **カスタムカード**: タップで開くボトムシートダイアログ

### 運転モード

| モード | 説明 |
|--------|------|
| おまかせ | 自動で最適運転 |
| 風量自動 | 風量自動、加湿手動設定 |
| 手動 | 風量・加湿を手動設定 |
| 節電 | 省エネ運転 |
| 花粉 | 花粉対策運転 |
| のど/はだ | 肌・のどうるおい運転 |
| サーキュ | サーキュレーション運転 |

### セレクトエンティティ一覧

| エンティティ | 選択肢 | 備考 |
|---|---|---|
| 風量 | 弱 / 標準 / 高 / 最高 | 手動モード時のみ有効 |
| 加湿 | 無 / 弱 / 標準 / 高 | 手動・風量自動モード時のみ有効 |
| LEDディスプレイ | 点灯 / 暗め / 消灯 | 本体ディスプレイの輝度設定 |

### センサーエンティティ一覧

| エンティティ | 単位 |
|---|---|
| 室温 | °C |
| 湿度 | % |
| PM2.5 | μg/m³ |
| ほこり | μg/m³ |
| におい | （数値） |

### 使用API

| エンドポイント | 用途 |
|---|---|
| `GET /common/basic_info` | MACアドレス取得（デバイスID生成） |
| `GET /cleaner/get_control_info` | 運転状態取得 |
| `GET /cleaner/get_unit_status` | ユニット状態取得 |
| `GET /cleaner/get_sensor_info` | センサー値取得（室温・湿度・PM2.5等） |
| `GET /cleaner/set_control_info` | 運転設定変更 |

参考: [nasshu2916/DAIKIN-API](https://github.com/nasshu2916/DAIKIN-API), [akiraseto/daikinCleaner](https://github.com/akiraseto/daikinCleaner)

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
3. IPアドレスと名前を入力（MACアドレスを自動取得してデバイスIDとして使用）

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
```

## ライセンス

MIT License
