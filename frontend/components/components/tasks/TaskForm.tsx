"use client";

import { Button } from "@/components/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/components/ui/dialog";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/components/ui/form";
import { Input } from "@/components/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/components/ui/select";
import { Textarea } from "@/components/components/ui/textarea";
import { CreateTaskRequest, Task, UpdateTaskRequest } from "@/types/Task";
import { handlePriorityKeyboardShortcuts, announceToScreenReader } from "@/utils/accessibility";
import { format, fromUnixTime } from "date-fns";
import { useCallback, useEffect, useState } from "react";
import { useForm } from "react-hook-form";

interface TaskFormProps {
  isOpen: boolean;
  task?: Task; // 編集時に渡される既存のタスク
  onClose: () => void;
  onSubmit: (taskData: CreateTaskRequest | UpdateTaskRequest) => Promise<void>;
}

interface TaskFormValues {
  title: string;
  description?: string;
  expires_at?: string; // ISO date string for form input
  priority?: string; // UI用の文字列値（"high", "middle", "low", "none"）
}

export function TaskForm({ isOpen, task, onClose, onSubmit }: TaskFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isEditMode = !!task;

  // 優先度の数値を文字列に変換
  const priorityToString = useCallback((priority?: number): string => {
    switch (priority) {
      case 1: return "high";
      case 2: return "middle";
      case 3: return "low";
      default: return "none";
    }
  }, []);

  const form = useForm<TaskFormValues>({
    defaultValues: {
      title: "",
      description: "",
      expires_at: "",
      priority: "none",
    },
  });

  // タスクが変更されたときにフォームの値を更新
  useEffect(() => {
    if (task) {
      form.reset({
        title: task.title,
        description: task.description || "",
        expires_at: task.expires_at
          ? format(fromUnixTime(task.expires_at), "yyyy-MM-dd'T'HH:mm")
          : "",
        priority: priorityToString(task.priority),
      });
    } else {
      form.reset({
        title: "",
        description: "",
        expires_at: "",
        priority: "none",
      });
    }
  }, [task, form, priorityToString]);

  const handleSubmit = async (data: TaskFormValues) => {
    setIsSubmitting(true);
    try {
      // 優先度の文字列を数値に変換
      let priorityValue: 1 | 2 | 3 | undefined = undefined;
      if (data.priority === "high") {
        priorityValue = 1;
      } else if (data.priority === "middle") {
        priorityValue = 2;
      } else if (data.priority === "low") {
        priorityValue = 3;
      }

      const taskData = {
        title: data.title,
        description: data.description || undefined,
        expires_at: data.expires_at ? Math.floor(new Date(data.expires_at).getTime() / 1000) : undefined,
        priority: priorityValue,
      };

      await onSubmit(taskData);

      if (!isEditMode) {
        form.reset(); // 新規作成時のみリセット
      }
      onClose();
    } catch {
      // エラーハンドリングは上位コンポーネントで処理
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset form to original values
    if (task) {
      form.reset({
        title: task.title,
        description: task.description || "",
        expires_at: task.expires_at
          ? format(fromUnixTime(task.expires_at), "yyyy-MM-dd'T'HH:mm")
          : "",
        priority: priorityToString(task.priority),
      });
    } else {
      form.reset();
    }
    onClose();
  };

  // 優先度変更のキーボードショートカット処理
  const handlePriorityShortcut = useCallback((priority: 1 | 2 | 3 | undefined) => {
    const priorityString = priority === 1 ? "high" : priority === 2 ? "middle" : priority === 3 ? "low" : "none";
    form.setValue("priority", priorityString);

    // 変更をアナウンス
    const priorityName = priority === 1 ? "高優先度" : priority === 2 ? "中優先度" : priority === 3 ? "低優先度" : "優先度未設定";
    announceToScreenReader(`優先度を${priorityName}に設定しました`, 'polite');
  }, [form]);

  // キーボードイベントハンドラー
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    // 優先度設定のキーボードショートカット
    if (handlePriorityKeyboardShortcuts(event.nativeEvent, handlePriorityShortcut)) {
      return; // ショートカットが処理された場合は他の処理をスキップ
    }
  }, [handlePriorityShortcut]);

  // 現在時刻をISO形式で取得（datetime-localの最小値用）
  const now = new Date();
  const localDateTime = format(now, "yyyy-MM-dd'T'HH:mm");

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent
        className="sm:max-w-md"
        onKeyDown={handleKeyDown}
        aria-describedby="form-shortcuts-help"
      >
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "タスクを編集" : "新しいタスクを作成"}
          </DialogTitle>
          <DialogDescription>
            タスクの詳細を入力してください。期限は任意です。
          </DialogDescription>
          <div id="form-shortcuts-help" className="sr-only">
            キーボードショートカット: Ctrl+1で高優先度、Ctrl+2で中優先度、Ctrl+3で低優先度、Ctrl+0で優先度未設定に変更できます。
          </div>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="title"
              rules={{
                required: "タイトルは必須です",
                minLength: { value: 1, message: "タイトルを入力してください" }
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>タイトル *</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      placeholder="タスクのタイトルを入力"
                      disabled={isSubmitting}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>説明</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder="タスクの詳細を入力（任意）"
                      rows={3}
                      disabled={isSubmitting}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="priority"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>優先度</FormLabel>
                  <FormDescription>
                    タスクの重要度を設定できます（任意）
                  </FormDescription>
                  <FormControl>
                    <Select
                      onValueChange={(value) => {
                        // "none"の場合はundefinedを設定
                        field.onChange(value === "none" ? undefined : value);
                      }}
                      value={field.value || "none"}
                      disabled={isSubmitting}
                      aria-describedby="priority-description"
                    >
                      <SelectTrigger
                        className="w-full focus:ring-2 focus:ring-ring focus:ring-offset-2"
                        aria-label="優先度を選択"
                      >
                        <SelectValue placeholder="優先度を選択（任意）" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem
                          value="none"
                          aria-label="優先度を設定しない"
                        >
                          設定しない
                        </SelectItem>
                        <SelectItem
                          value="high"
                          aria-label="高優先度に設定"
                        >
                          高 - 緊急度が高いタスク
                        </SelectItem>
                        <SelectItem
                          value="middle"
                          aria-label="中優先度に設定"
                        >
                          中 - 標準的な重要度のタスク
                        </SelectItem>
                        <SelectItem
                          value="low"
                          aria-label="低優先度に設定"
                        >
                          低 - 時間があるときに対応
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="expires_at"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>期限</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      type="datetime-local"
                      min={localDateTime}
                      disabled={isSubmitting}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter className="gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={isSubmitting}
              >
                キャンセル
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting
                  ? (isEditMode ? "更新中..." : "作成中...")
                  : (isEditMode ? "更新" : "作成")
                }
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
