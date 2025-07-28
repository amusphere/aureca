'use client';

import { useState } from 'react';
import { useDemo } from '@/components/contexts/DemoContext';
import { DemoTaskForm } from './DemoTaskForm';
import { DemoTaskItem } from './DemoTaskItem';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/components/ui/card';
import { Button } from '@/components/components/ui/button';
import { Plus, CheckCircle, Circle, Clock } from 'lucide-react';
// import { DemoTask } from '@/types/Demo';

export function DemoTaskList() {
  const { state } = useDemo();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed'>('all');

  if (!state.session) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <p className="text-gray-500">セッションが見つかりません</p>
        </CardContent>
      </Card>
    );
  }

  const tasks = state.session.tasks;
  const filteredTasks = tasks.filter(task => {
    switch (filter) {
      case 'pending':
        return !task.completed;
      case 'completed':
        return task.completed;
      default:
        return true;
    }
  });

  const completedCount = tasks.filter(task => task.completed).length;
  const pendingCount = tasks.length - completedCount;

  return (
    <div className="space-y-6">
      {/* 統計情報 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Circle className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">全タスク</p>
                <p className="text-2xl font-bold text-gray-900">{tasks.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">未完了</p>
                <p className="text-2xl font-bold text-gray-900">{pendingCount}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">完了済み</p>
                <p className="text-2xl font-bold text-gray-900">{completedCount}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* タスクリスト */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>タスク一覧</CardTitle>
            <Button
              onClick={() => setShowCreateForm(true)}
              className="flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>新しいタスク</span>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* フィルター */}
          <div className="flex space-x-2 mb-4">
            <Button
              variant={filter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('all')}
            >
              すべて ({tasks.length})
            </Button>
            <Button
              variant={filter === 'pending' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('pending')}
            >
              未完了 ({pendingCount})
            </Button>
            <Button
              variant={filter === 'completed' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('completed')}
            >
              完了済み ({completedCount})
            </Button>
          </div>

          {/* タスク作成フォーム */}
          {showCreateForm && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <DemoTaskForm
                onSuccess={() => setShowCreateForm(false)}
                onCancel={() => setShowCreateForm(false)}
              />
            </div>
          )}

          {/* タスクリスト */}
          <div className="space-y-3">
            {filteredTasks.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-gray-400 mb-2">
                  <Circle className="h-12 w-12 mx-auto" />
                </div>
                <p className="text-gray-500">
                  {filter === 'all'
                    ? 'タスクがありません'
                    : filter === 'pending'
                    ? '未完了のタスクがありません'
                    : '完了済みのタスクがありません'
                  }
                </p>
                {filter === 'all' && !showCreateForm && (
                  <Button
                    onClick={() => setShowCreateForm(true)}
                    variant="outline"
                    className="mt-4"
                  >
                    最初のタスクを作成
                  </Button>
                )}
              </div>
            ) : (
              filteredTasks
                .sort((a, b) => {
                  // 未完了を上に、完了済みを下に
                  if (a.completed !== b.completed) {
                    return a.completed ? 1 : -1;
                  }
                  // 期限が近いものを上に
                  if (a.expires_at && b.expires_at) {
                    return a.expires_at - b.expires_at;
                  }
                  if (a.expires_at && !b.expires_at) return -1;
                  if (!a.expires_at && b.expires_at) return 1;
                  // 作成日時が新しいものを上に
                  return b.created_at - a.created_at;
                })
                .map(task => (
                  <DemoTaskItem key={task.id} task={task} />
                ))
            )}
          </div>

          {/* 制限なしでタスク作成可能 */}
        </CardContent>
      </Card>
    </div>
  );
}