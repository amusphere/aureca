'use client';

import { useState } from 'react';
import { useDemo } from '@/components/contexts/DemoContext';
import { DemoTask } from '@/types/Demo';
import { Button } from '@/components/components/ui/button';
import { Card, CardContent } from '@/components/components/ui/card';
import { Badge } from '@/components/components/ui/badge';
import { Checkbox } from '@/components/components/ui/checkbox';
import {
  MoreHorizontal,
  Edit,
  Trash2,
  Calendar,
  Clock
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/components/ui/alert-dialog';
import { DemoTaskEditForm } from './DemoTaskEditForm';

interface DemoTaskItemProps {
  task: DemoTask;
}

export function DemoTaskItem({ task }: DemoTaskItemProps) {
  const { updateTask, deleteTask } = useDemo();
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const handleToggleComplete = async () => {
    await updateTask(task.id, { completed: !task.completed });
  };

  const handleDelete = async () => {
    await deleteTask(task.id);
    setShowDeleteDialog(false);
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('ja-JP', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isExpired = task.expires_at && task.expires_at < Date.now();
  const isExpiringSoon = task.expires_at && task.expires_at < Date.now() + (24 * 60 * 60 * 1000);

  if (isEditing) {
    return (
      <Card className="p-4">
        <DemoTaskEditForm
          task={task}
          onSuccess={() => setIsEditing(false)}
          onCancel={() => setIsEditing(false)}
        />
      </Card>
    );
  }

  return (
    <>
      <Card className={`transition-all duration-200 hover:shadow-md ${
        task.completed ? 'bg-gray-50' : 'bg-white'
      }`}>
        <CardContent className="p-4">
          <div className="flex items-start space-x-3">
            {/* チェックボックス */}
            <div className="flex-shrink-0 mt-1">
              <Checkbox
                checked={task.completed}
                onCheckedChange={handleToggleComplete}
                className="h-5 w-5"
              />
            </div>

            {/* タスク内容 */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className={`font-medium ${
                    task.completed
                      ? 'text-gray-500 line-through'
                      : 'text-gray-900'
                  }`}>
                    {task.title}
                  </h3>

                  {task.description && (
                    <p className={`mt-1 text-sm ${
                      task.completed
                        ? 'text-gray-400'
                        : 'text-gray-600'
                    }`}>
                      {task.description}
                    </p>
                  )}

                  {/* メタ情報 */}
                  <div className="flex items-center space-x-4 mt-2">
                    {/* 期限 */}
                    {task.expires_at && (
                      <div className={`flex items-center space-x-1 text-xs ${
                        isExpired
                          ? 'text-red-600'
                          : isExpiringSoon
                          ? 'text-yellow-600'
                          : 'text-gray-500'
                      }`}>
                        <Calendar className="h-3 w-3" />
                        <span>{formatDate(task.expires_at)}</span>
                        {isExpired && <Badge variant="destructive" className="ml-1 text-xs">期限切れ</Badge>}
                        {!isExpired && isExpiringSoon && <Badge variant="outline" className="ml-1 text-xs">期限間近</Badge>}
                      </div>
                    )}

                    {/* 作成日時 */}
                    <div className="flex items-center space-x-1 text-xs text-gray-500">
                      <Clock className="h-3 w-3" />
                      <span>作成: {formatDate(task.created_at)}</span>
                    </div>

                    {/* ソースタイプ */}
                    <Badge variant="secondary" className="text-xs">
                      デモ
                    </Badge>
                  </div>
                </div>

                {/* アクションメニュー */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => setIsEditing(true)}>
                      <Edit className="h-4 w-4 mr-2" />
                      編集
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => setShowDeleteDialog(true)}
                      className="text-red-600"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      削除
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 削除確認ダイアログ */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>タスクを削除しますか？</AlertDialogTitle>
            <AlertDialogDescription>
              「{task.title}」を削除します。この操作は取り消せません。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>キャンセル</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-red-600 hover:bg-red-700">
              削除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}