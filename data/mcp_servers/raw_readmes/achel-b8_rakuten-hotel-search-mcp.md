# rakuten-hotel-mcp

楽天トラベル空室検索APIを利用したMCPサーバー

## 概要

このプロジェクトは、楽天トラベルの空室検索APIを利用して周辺ホテルの空室情報を取得するMCPサーバーです。

## 技術スタック

- 言語: TypeScript
- Webフレームワーク: Express
- MCP SDK: @modelcontextprotocol/sdk
- テスト: Vitest
- 静的解析: ESLint
- フォーマッター: Prettier
- HTTPクライアント: axios
- 環境変数管理: dotenv

## 機能

- `getHotels`: 指定された条件（チェックイン日、チェックアウト日、位置情報など）で周辺ホテルの空室情報を取得します。

## 使用方法

### インストール

```bash
# 依存パッケージのインストール
npm install

# 開発サーバーの起動
npm run dev

# ビルド
npm run build

# テスト実行
npm test

# リント実行
npm run lint

# フォーマット実行
npm run format
```

### 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成し、必要な環境変数を設定してください。

```
APPLICATION_ID=your_application_id_here
APPLICATION_SECRET=your_application_secret_here
AFFILIATE_ID=your_affiliate_id_here
```

### MCPサーバーの設定

ビルド後、以下のようにMCPサーバーの設定を行います。

1. Clineの設定ファイル（`cline_mcp_settings.json`）に以下の設定を追加します：

```json
{
  "mcpServers": {
    "rakuten-hotel": {
      "command": "node",
      "args": ["パス/to/rakuten-hotel-mcp/build/index.js"],
      "env": {
        "APPLICATION_ID": "your_application_id_here",
        "APPLICATION_SECRET": "your_application_secret_here",
        "AFFILIATE_ID": "your_affiliate_id_here"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

2. Clineを再起動すると、`getHotels`ツールが利用可能になります。

### 使用例

MCPサーバーが設定されると、以下のようにClineで使用できます：

```
東京駅周辺のホテルを2023年12月1日から12月2日まで検索して
```

## APIパラメータ

`getHotels`ツールは以下のパラメータを受け付けます：

- `checkIn`: チェックイン日（YYYY-MM-DD形式）【必須】
- `checkOut`: チェックアウト日（YYYY-MM-DD形式）【必須】
- `latitude`: 緯度（省略可能、デフォルトは東京）
- `longitude`: 経度（省略可能、デフォルトは東京）
- `radiusKm`: 検索半径 km（省略可能、デフォルト2km）

## ライセンス

MIT
