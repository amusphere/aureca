'use client';

import { useState } from 'react';
import { useDemo } from '@/components/contexts/DemoContext';
import { DemoTask, UpdateDemoTaskRequest } from '@/types/Demo';
import { Button } from '@/components/components/ui/button';
import { Input } from '@/components/components/ui/input';
import { Textarea } from '@/components/components/ui/textarea';
import { Label } from '@/components/components/ui/label';
import { Calendar } from '@/components/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/components/ui/popover';
import { CalendarIcon, Save, X } from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { toast } from 'sonner';

interface DemoTaskEditFormProps {
  task: DemoTask;
  onSuccess: () => void;
  onCancel: () => void;
}

export function DemoTaskEditForm({ task, onSuccess, onCancel }: DemoTaskEditFormProps) {
  const { updateTask } = useDemo();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<UpdateDemoTaskRequest>({
    title: task.title,
    description: task.description || '',
    completed: task.completed,
    expires_at: task.expires_at
  });
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(
    task.expires_at ? new Date(task.expires_at) : undefined
  );
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title?.trim()) {
      newErrors.title = 'タイトルは必須です';
    } else if (formData.title.length > 100) {
      newErrors.title = 'タイトルは100文字以内で入力してください';
    }

    if (formData.description && formData.description.length > 500) {
      newErrors.description = '説明は500文字以内で入力してください';
    }

    if (selectedDate && selectedDate < new Date()) {
      newErrors.expires_at = '期限は現在時刻より後に設定してください';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const updateData: UpdateDemoTaskRequest = {
        ...formData,
        expires_at: selectedDate?.getTime()
      };

      const success = await updateTask(task.id, updateData);

      if (success) {
        toast.success('タスクを更新しました');
        onSuccess();
      } else {
        toast.error('タスクの更新に失敗しました');
      }
    } catch (error) {
      console.error('Task update error:', error);
      toast.error('エラーが発生しました');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDateSelect = (date: Date | undefined) => {
    setSelectedDate(date);
    if (errors.expires_at) {
      setErrors(prev => ({ ...prev, expires_at: '' }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium">タスクを編集</h3>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onCancel}
          className="h-8 w-8 p-0"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* タイトル */}
      <div className="space-y-2">
        <Label htmlFor="edit-title">タイトル *</Label>
        <Input
          id="edit-title"
          value={formData.title}
          onChange={(e) => {
            setFormData(prev => ({ ...prev, title: e.target.value }));
            if (errors.title) {
              setErrors(prev => ({ ...prev, title: '' }));
            }
          }}
          placeholder="タスクのタイトルを入力"
          className={errors.title ? 'border-red-500' : ''}
          maxLength={100}
        />
        {errors.title && (
          <p className="text-sm text-red-600">{errors.title}</p>
        )}
      </div>

      {/* 説明 */}
      <div className="space-y-2">
        <Label htmlFor="edit-description">説明</Label>
        <Textarea
          id="edit-description"
          value={formData.description}
          onChange={(e) => {
            setFormData(prev => ({ ...prev, description: e.target.value }));
            if (errors.description) {
              setErrors(prev => ({ ...prev, description: '' }));
            }
          }}
          placeholder="タスクの詳細説明（任意）"
          className={errors.description ? 'border-red-500' : ''}
          rows={3}
          maxLength={500}
        />
        {errors.description && (
          <p className="text-sm text-red-600">{errors.description}</p>
        )}
        <p className="text-xs text-gray-500">
          {formData.description?.length || 0}/500文字
        </p>
      </div>

      {/* 期限 */}
      <div className="space-y-2">
        <Label>期限</Label>
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className={`w-full justify-start text-left font-normal ${
                !selectedDate && 'text-muted-foreground'
              } ${errors.expires_at ? 'border-red-500' : ''}`}
            >
              <CalendarIcon className="mr-2 h-4 w-4" />
              {selectedDate ? (
                format(selectedDate, 'PPP', { locale: ja })
              ) : (
                '期限を設定（任意）'
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={handleDateSelect}
              disabled={(date) => date < new Date()}
              initialFocus
            />
            {selectedDate && (
              <div className="p-3 border-t">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDateSelect(undefined)}
                  className="w-full"
                >
                  期限をクリア
                </Button>
              </div>
            )}
          </PopoverContent>
        </Popover>
        {errors.expires_at && (
          <p className="text-sm text-red-600">{errors.expires_at}</p>
        )}
      </div>

      {/* 完了状態 */}
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="edit-completed"
          checked={formData.completed}
          onChange={(e) => setFormData(prev => ({ ...prev, completed: e.target.checked }))}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <Label htmlFor="edit-completed">完了済みとしてマーク</Label>
      </div>

      {/* アクションボタン */}
      <div className="flex justify-end space-x-3 pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          キャンセル
        </Button>
        <Button
          type="submit"
          disabled={isSubmitting || !formData.title?.trim()}
          className="flex items-center space-x-2"
        >
          <Save className="h-4 w-4" />
          <span>{isSubmitting ? '更新中...' : '更新'}</span>
        </Button>
      </div>
    </form>
  );
}