# 実装計画

- [x] 1. データベーススキーマ更新とマイグレーション
  - Usersテーブルにstripe_customer_idカラムを追加
  - 既存のSubscriptionsテーブルを削除（不要になったため）
  - Alembicマイグレーションファイルを生成・実行
  - _要件: 要件2.1, 要件2.4_

- [x] 2. SQLModelスキーマ定義の更新
  - 既存のSubscriptionモデルを削除
  - UserモデルにStripe Customer IDフィールドのみ追加
  - schema.pyを更新
  - _要件: 要件2.1, 要件2.4_

- [x] 3. Stripe SDK設定とサービス基盤構築
  - Stripe Python SDKをプロジェクトに追加
  - 環境変数設定（STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY）
  - Stripe APIキー設定とテストモード確認
  - _要件: 要件1.1_

- [ ] 3.1. キャッシュライブラリの設定
  - fastapi-cacheライブラリを追加（エンドポイントキャッシュ用）
  - React Queryをフロントエンドに追加（クライアントキャッシュ用）
  - メモリベースキャッシュの設定
  - _要件: 要件6.1_

- [ ] 4. Stripe Serviceの実装
  - StripeServiceクラスの基本構造を作成
  - Customer作成・取得機能を実装
  - サブスクリプション情報取得機能を実装（Stripe APIから直接）
  - Checkout Session作成機能を実装（サブスクリプション購入用）
  - Customer Portal Session作成機能を実装（管理・キャンセル用）
  - _要件: 要件1.1, 要件2.1, 要件3.1, 要件3.2, 要件3.4_

- [ ] 5. ユーザーサービスの実装
  - UserServiceクラスを新規作成（backend/app/services/user_service.py）
  - ensure_stripe_customer機能を実装（初回アクセス時にStripe Customer作成）
  - stripe_customer_idをデータベースに保存する機能
  - Stripe APIからサブスクリプション情報を取得する機能
  - エラーハンドリングとロールバック処理を実装
  - _要件: 要件1.1, 要件2.1, 要件7.1_

- [ ] 6. Stripe APIルーターの実装
  - /api/stripe/create-checkout-session エンドポイント
  - /api/stripe/create-portal-session エンドポイント
  - 認証とエラーハンドリングを実装
  - _要件: 要件3.1, 要件3.2, 要件3.4_

- [ ] 7. Users APIの拡張
  - /api/users/me エンドポイントを拡張
  - Stripe APIからサブスクリプション情報を取得
  - サブスクリプション情報を含むレスポンス形式を定義
  - isPremium判定ロジックを実装
  - プラン名、有効期限、ステータス情報を含める
  - @cacheデコレータでエンドポイントレベルキャッシュを実装（5分間）
  - _要件: 要件2.1, 要件5.1, 要件5.2, 要件6.1_

- [ ] 8. フロントエンド型定義の更新
  - UserWithSubscription型を定義
  - SubscriptionInfo型を定義
  - API レスポンス型を更新
  - _要件: 要件4.4, 要件5.2_

- [ ] 9. useUserフックの拡張
  - サブスクリプション情報を含むユーザー情報取得
  - isPremium判定機能を追加
  - React Queryによるクライアントサイドキャッシュを実装（5分間）
  - リフレッシュ機能を実装
  - _要件: 要件4.4, 要件5.2, 要件6.1_

- [ ] 10. useSubscriptionフックの実装
  - Checkout Session作成機能
  - Customer Portal開く機能
  - エラーハンドリングとローディング状態管理
  - _要件: 要件3.1, 要件3.2, 要件3.4_

- [ ] 11. PremiumGuardコンポーネントの実装
  - Clerkの<Protect>コンポーネントを置き換え
  - useUserフックからサブスクリプション状態を取得
  - 条件付きレンダリングとフォールバック表示
  - アップグレードプロンプト機能
  - _要件: 要件4.1, 要件4.2, 要件4.3_

- [ ] 12. サブスクリプションページの実装
  - Stripe Pricing Tableコンポーネントの統合
  - 現在のプラン状態表示
  - Customer Portalへのリンク
  - レスポンシブデザイン対応
  - _要件: 要件3.1, 要件3.2, 要件3.4_

- [ ] 13. TaskListコンポーネントの更新
  - Clerkの<Protect>をPremiumGuardに置き換え
  - 自動生成ボタンの表示制御をPremiumGuardで実装
  - サブスクリプション状態に基づく機能制御
  - _要件: 要件4.1, 要件4.3_

- [ ] 14. HomePageコンポーネントの更新
  - Clerkの<Protect>をPremiumGuardに置き換え
  - AIUpgradePromptの表示制御を更新
  - AIChatの表示制御を更新
  - _要件: 要件4.2, 要件4.3_

- [ ] 15. 環境変数とデプロイ設定
  - フロントエンド環境変数を追加（NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY）
  - バックエンド環境変数を追加（STRIPE_SECRET_KEY）
  - 本番環境とテスト環境の設定分離
  - _要件: 要件1.2_

- [ ] 16. エラーハンドリングとログ機能の実装
  - Stripe API エラーの適切な処理
  - キャッシュエラー時のフォールバック処理
  - ユーザー向けエラーメッセージの改善
  - _要件: 要件6.3, 要件6.4_

- [ ] 17. 単体テストの実装
  - StripeServiceのテスト（モック使用）
  - UserServiceのテスト
  - PremiumGuardコンポーネントのテスト
  - _要件: 要件1.2, 要件2.1, 要件6.1_

- [ ] 18. 統合テストの実装
  - Stripe Test Mode APIを使用したE2Eテスト
  - サブスクリプション購入フローのテスト
  - キャッシュ機能のテスト
  - _要件: 要件3.1, 要件3.2, 要件6.1_

- [ ] 19. 既存Clerk Billing機能の無効化
  - Clerkの<Protect>コンポーネント使用箇所を特定・置き換え
  - Clerk Billing関連設定の無効化
  - Clerk Billing関連環境変数の削除
  - _要件: 要件1.2, 要件7.4_

- [ ] 20. 不要なコードとテストの精査・削除
  - Clerk Billing関連のコード削除
  - Subscriptionsテーブル関連のコード削除
  - Webhook関連のコード削除
  - 使用されなくなったコンポーネント・フック・ユーティリティの削除
  - 不要なテストファイルの削除
  - 不要なnpm/uv依存関係の削除
  - 古いコメントやTODOの整理
  - _要件: 要件7.4_

- [ ] 21. データ移行とクリーンアップ
  - 既存ユーザーのStripe Customer作成（必要に応じて）
  - 既存Subscriptionsテーブルのデータ削除
  - 旧システムとの整合性確認
  - 移行完了後の動作確認
  - _要件: 要件7.1, 要件7.2, 要件7.3_

- [ ] 22. ドキュメント更新
  - README.mdの環境変数設定を更新
  - docs/architecture.mdにStripe統合の説明を追加
  - API仕様書の更新（サブスクリプション関連エンドポイント）
  - 開発者向けセットアップガイドの更新
  - Stripe APIから直接取得する設計の説明を追加
  - _要件: 要件1.2_

- [ ] 23. 最終コードレビューと品質チェック
  - 全体的なコード品質の確認
  - セキュリティ観点でのレビュー
  - パフォーマンス観点でのレビュー（キャッシュ機能含む）
  - アクセシビリティ対応の確認
  - レスポンシブデザインの確認
  - _要件: 要件1.2, 要件7.4_