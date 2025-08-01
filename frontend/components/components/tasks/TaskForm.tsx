"use client";

import { Button } from "@/components/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/components/ui/form";
import { Input } from "@/components/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/components/ui/select";
import { Textarea } from "@/components/components/ui/textarea";
import { CreateTaskRequest, Task, TaskPriority, UpdateTaskRequest } from "@/types/Task";
import { format, fromUnixTime } from "date-fns";
import { useEffect, useState } from "react";
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
  priority?: TaskPriority;
}

export function TaskForm({ isOpen, task, onClose, onSubmit }: TaskFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isEditMode = !!task;

  const form = useForm<TaskFormValues>({
    defaultValues: {
      title: "",
      description: "",
      expires_at: "",
      priority: undefined,
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
        priority: task.priority,
      });
    } else {
      form.reset({
        title: "",
        description: "",
        expires_at: "",
        priority: undefined,
      });
    }
  }, [task, form]);

  const handleSubmit = async (data: TaskFormValues) => {
    setIsSubmitting(true);
    try {
      const taskData = {
        title: data.title,
        description: data.description || undefined,
        expires_at: data.expires_at ? Math.floor(new Date(data.expires_at).getTime() / 1000) : undefined,
        priority: data.priority,
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
        priority: task.priority,
      });
    } else {
      form.reset();
    }
    onClose();
  };

  // 現在時刻をISO形式で取得（datetime-localの最小値用）
  const now = new Date();
  const localDateTime = format(now, "yyyy-MM-dd'T'HH:mm");

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEditMode ? "タスクを編集" : "新しいタスクを作成"}
          </DialogTitle>
          <DialogDescription>
            タスクの詳細を入力してください。期限は任意です。
          </DialogDescription>
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
                  <FormControl>
                    <Select
                      onValueChange={(value) => {
                        // 空文字列の場合はundefinedを設定
                        field.onChange(value || undefined);
                      }}
                      value={field.value || ""}
                      disabled={isSubmitting}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="優先度を選択（任意）" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="high">高</SelectItem>
                        <SelectItem value="middle">中</SelectItem>
                        <SelectItem value="low">低</SelectItem>
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
