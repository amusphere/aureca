import { DemoTask, DemoSession } from '@/types/Demo';

export const DEMO_LIMITATIONS = {
  SESSION_KEY: 'demo_session'
};

export const generateSampleTasks = (): DemoTask[] => {
  const now = Date.now();

  return [
    {
      id: 'demo-1',
      title: 'プロジェクト企画書の作成',
      description: '新しいプロジェクトの企画書を作成し、チームに共有する',
      completed: false,
      expires_at: now + (7 * 24 * 60 * 60 * 1000), // 7日後
      created_at: now - (2 * 24 * 60 * 60 * 1000), // 2日前
      source_type: 'demo'
    },
    {
      id: 'demo-2',
      title: 'クライアントミーティングの準備',
      description: '来週のクライアントミーティングの資料準備',
      completed: true,
      expires_at: now + (3 * 24 * 60 * 60 * 1000), // 3日後
      created_at: now - (1 * 24 * 60 * 60 * 1000), // 1日前
      source_type: 'demo'
    },
    {
      id: 'demo-3',
      title: 'システムのバックアップ確認',
      description: 'データベースとファイルシステムのバックアップ状況を確認',
      completed: false,
      expires_at: now + (1 * 24 * 60 * 60 * 1000), // 1日後
      created_at: now - (3 * 60 * 60 * 1000), // 3時間前
      source_type: 'demo'
    },
    {
      id: 'demo-4',
      title: 'チームメンバーとの1on1ミーティング',
      description: '各チームメンバーとの個別面談を実施',
      completed: false,
      expires_at: now + (5 * 24 * 60 * 60 * 1000), // 5日後
      created_at: now - (4 * 60 * 60 * 1000), // 4時間前
      source_type: 'demo'
    },
    {
      id: 'demo-5',
      title: '月次レポートの作成',
      description: '先月の業績と今月の目標をまとめたレポートを作成',
      completed: true,
      expires_at: now + (2 * 24 * 60 * 60 * 1000), // 2日後
      created_at: now - (5 * 24 * 60 * 60 * 1000), // 5日前
      source_type: 'demo'
    }
  ];
};

export const createDemoSession = (): DemoSession => {
  const now = Date.now();
  const sessionId = `demo_${now}_${Math.random().toString(36).substr(2, 9)}`;

  return {
    id: sessionId,
    tasks: generateSampleTasks(),
    created_at: now,
    expires_at: null, // 時間制限なし
    limitations: {
      max_tasks: null, // タスク数制限なし
      max_duration: null, // 時間制限なし
      current_task_count: generateSampleTasks().length
    }
  };
};