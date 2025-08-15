# 実装計画

- [x] 1. 本番コードからテスト固有処理を除去
  - AIChatUsageServiceからPYTEST_CURRENT_TEST環境変数チェックを削除
  - unittest.mockの動的インポートを除去
  - Mock検出ロジックを削除
  - テスト固有の条件分岐を除去
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 1.1 AIChatUsageServiceのget_user_planメソッドをクリーンアップ
  - PYTEST_CURRENT_TEST環境変数チェックを削除
  - unittest.mockの動的インポートを除去
  - _is_clerk_mockedフィールドを削除
  - テスト固有の分岐処理を除去
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 1.2 AIChatUsageServiceのget_usage_statsメソッドをクリーンアップ
  - Mock検出ロジックを削除
  - unittest.mockの動的インポートを除去
  - リポジトリアクセスを統一
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 1.3 AIChatUsageServiceのcan_use_chatメソッドをクリーンアップ
  - Mock検出ロジックを削除
  - unittest.mockの動的インポートを除去
  - リポジトリアクセスを統一
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 1.4 AIChatUsageServiceのincrement_usageメソッドをクリーンアップ
  - Mock検出ロジックを削除
  - unittest.mockの動的インポートを除去
  - リポジトリアクセスを統一
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 1.5 AIChatUsageServiceのis_clerk_mockedメソッドを削除
  - テスト専用メソッドを削除
  - 関連するフィールドを削除
  - _Requirements: 1.5_

- [x] 1.6 AIChatUsageRepositoryのincrement_daily_usageラッパーを削除
  - テスト専用の後方互換ラッパーを削除
  - 直接increment_usage_countを使用するよう統一
  - _Requirements: 1.5_

- [x] 1.7 AIアシスタントAPIのテスト固有処理を削除
  - PYTEST_CURRENT_TEST環境変数チェックを削除
  - unittest.mockの動的インポートを除去
  - Mock検出ロジックを削除
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. 依存性注入の導入
  - AIChatUsageServiceにコンストラクタ注入を追加
  - ClerkServiceの注入を可能にする
  - AIChatUsageRepositoryの注入を可能にする
  - デフォルト値で後方互換性を保つ
  - _Requirements: 2.3_

- [x] 2.1 AIChatUsageServiceのコンストラクタを拡張
  - clerk_serviceパラメータを追加
  - usage_repositoryパラメータを追加
  - デフォルト値で既存コードとの互換性を保つ
  - _Requirements: 2.3_

- [x] 2.2 AIChatUsageServiceのメソッドを依存性注入対応に修正
  - get_user_planでself.clerk_serviceを使用
  - リポジトリアクセスでself.usage_repositoryを使用
  - 全メソッドで注入された依存性を活用
  - _Requirements: 2.3_

- [x] 3. テストユーティリティの作成
  - TestDataFactoryクラスを作成
  - TestErrorScenariosクラスを作成
  - UserFactoryクラスを作成
  - 再利用可能なテストヘルパーを実装
  - _Requirements: 2.1, 2.2, 2.5_

- [x] 3.1 TestDataFactoryクラスを実装
  - create_userメソッドを実装
  - create_usage_recordメソッドを実装
  - デフォルト値とカスタマイズ可能なパラメータを提供
  - _Requirements: 2.1, 2.2_

- [x] 3.2 UserFactoryクラスを実装
  - buildメソッドでUserオブジェクト生成
  - createメソッドでデータベース永続化
  - ファクトリーパターンを適用
  - _Requirements: 2.1, 2.2_

- [x] 3.3 TestErrorScenariosクラスを実装
  - simulate_clerk_api_errorメソッド
  - simulate_database_errorメソッド
  - エラーシナリオのテストを支援
  - _Requirements: 2.1, 2.2_

- [x] 4. conftest.pyの再設計
  - 既存のテスト固有処理を削除
  - 適切なfixtureを作成
  - 依存性オーバーライドを活用
  - テストの分離を確保
  - _Requirements: 2.1, 2.2, 2.3, 3.5_

- [x] 4.1 mock_clerk_serviceフィクスチャを作成
  - get_clerk_serviceをモック
  - 標準的なレスポンスを設定
  - テスト間での状態分離を確保
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 4.2 mock_ai_usage_repositoryフィクスチャを作成
  - AIChatUsageRepositoryをモック
  - 標準的なメソッドの動作を設定
  - テスト間での状態分離を確保
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 4.3 sample_tasksフィクスチャを修正
  - リポジトリ関数の直接呼び出しを削除
  - ファクトリーパターンを使用
  - テストデータの生成を標準化
  - _Requirements: 2.2, 2.5_

- [x] 5. ユニットテストの書き直し
  - test_ai_chat_usage_service.pyを完全に書き直し
  - 依存性注入を活用したテスト設計
  - 本番コードへの依存を除去
  - 全てのテストケースを移行
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2, 5.3_

- [x] 5.1 AIChatUsageServiceのユニットテストを再実装
  - mock_dependenciesフィクスチャを削除
  - 依存性注入を使用したテストセットアップ
  - 全てのメソッドのテストケースを移行
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5.2 ClerkServiceのユニットテストを確認・修正
  - 既存のテストが適切に分離されているか確認
  - 必要に応じて改善
  - _Requirements: 2.1, 2.2, 2.3, 3.5_

- [x] 5.3 その他のユニットテストを確認・修正
  - test_ai_chat_usage_repository.pyを確認
  - test_plan_limits.pyを確認
  - test_task_repository.pyを確認
  - 必要に応じて改善
  - _Requirements: 2.1, 2.2, 2.3, 3.5_

- [x] 6. 統合テストの改善
  - test_ai_chat_usage_integration_simple.pyを書き直し
  - FastAPIの依存性オーバーライドを活用
  - 環境変数への依存を除去
  - テストの分離を確保
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 5.4_

- [x] 6.1 統合テストの依存性オーバーライドを実装
  - setup_app_overridesフィクスチャを作成
  - FastAPIのdependency_overridesを活用
  - テスト後のクリーンアップを確保
  - _Requirements: 2.1, 2.2, 2.3, 3.2_

- [x] 6.2 統合テストケースを書き直し
  - _setup_authと_cleanup_authを削除
  - 依存性オーバーライドを使用
  - 全てのテストケースを移行
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 6.3 その他の統合テストを確認・修正
  - test_ai_chat_usage_api_integration.pyを確認
  - test_ai_chat_usage_e2e_integration.pyを確認
  - test_clerk_api_integration.pyを確認
  - 必要に応じて改善
  - _Requirements: 2.1, 2.2, 2.3, 3.5, 5.4_

- [x] 7. パフォーマンステストの確認・修正
  - test_ai_chat_usage_performance.pyを確認
  - test_task_priority_performance.pyを確認
  - 本番コードへの依存がないか確認
  - 必要に応じて改善
  - _Requirements: 2.1, 2.2, 2.3, 3.5, 5.2_

- [x] 8. テスト実行とデバッグ
  - 全てのテストが正常に実行されることを確認
  - pytest実行時のエラーを修正
  - テストの独立性を確認
  - _Requirements: 4.3, 5.1, 5.2, 5.3_

- [x] 8.1 ユニットテストの実行確認
  - uv run pytest tests/unit/ -vを実行
  - 全てのテストが合格することを確認
  - エラーがあれば修正
  - _Requirements: 4.3, 5.1, 5.2, 5.3_

- [x] 8.2 統合テストの実行確認
  - uv run pytest tests/integration/ -vを実行
  - 全てのテストが合格することを確認
  - エラーがあれば修正
  - _Requirements: 4.3, 5.1, 5.2, 5.3, 5.4_

- [x] 8.3 パフォーマンステストの実行確認
  - uv run pytest tests/performance/ -vを実行
  - 全てのテストが合格することを確認
  - エラーがあれば修正
  - _Requirements: 4.3, 5.1, 5.2, 5.3_

- [ ] 9. コード品質の確認
  - Ruffフォーマットとリントを実行
  - 全てのチェックに合格することを確認
  - コード品質基準を満たすことを確認
  - _Requirements: 4.1, 4.2, 4.4, 4.5_

- [ ] 9.1 Ruffフォーマットの実行
  - uv run ruff format .を実行
  - フォーマットエラーがないことを確認
  - 必要に応じてコードを修正
  - _Requirements: 4.1, 4.4, 4.5_

- [ ] 9.2 Ruffリントの実行
  - uv run ruff check . --fixを実行
  - リントエラーがないことを確認
  - 必要に応じてコードを修正
  - _Requirements: 4.2, 4.4, 4.5_

- [ ] 10. 最終検証とドキュメント更新
  - 全体的なテスト実行を確認
  - テストカバレッジを検証
  - 改善内容をドキュメント化
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 10.1 全テストの最終実行
  - uv run pytestを実行
  - 全てのテストが合格することを確認
  - テスト実行時間が適切であることを確認
  - _Requirements: 4.3, 5.1, 5.2, 5.3_

- [ ] 10.2 テストカバレッジの確認
  - 既存のテスト機能が保持されていることを確認
  - エッジケースが適切にテストされていることを確認
  - _Requirements: 5.1, 5.3_

- [ ] 10.3 改善内容のドキュメント化
  - 変更内容をREADMEに記載
  - テストパターンの使用方法を文書化
  - 新しいテストユーティリティの使用方法を説明
  - _Requirements: 5.5_