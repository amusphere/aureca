"use client";

import { AlertTriangle, Plus, Trash2 } from "lucide-react";
import { useCallback, useState } from "react";
import type { ChatThread, CreateChatThreadRequest } from "../../../types/Chat";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";

interface ChatThreadActionsProps {
  onCreateThread: (request?: CreateChatThreadRequest) => Promise<ChatThread | null>;
  onDeleteThread: (threadUuid: string) => Promise<boolean>;
  disabled?: boolean;
  className?: string;
}

/**
 * チャットスレッド操作コンポーネント
 *
 * 要件4.1: 新しいスレッド作成機能
 * 要件4.4: スレッド削除機能と確認ダイアログ
 */
export function ChatThreadActions({
  onCreateThread,
  onDeleteThread,
  disabled = false,
  className,
}: ChatThreadActionsProps) {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [threadToDelete, setThreadToDelete] = useState<{
    uuid: string;
    title: string;
  } | null>(null);
  const [newThreadTitle, setNewThreadTitle] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Handle create thread dialog
  const handleCreateClick = useCallback(() => {
    setNewThreadTitle("");
    setCreateDialogOpen(true);
  }, []);

  const handleCreateConfirm = useCallback(async () => {
    if (isCreating) return;

    setIsCreating(true);
    try {
      const request: CreateChatThreadRequest = newThreadTitle.trim()
        ? { title: newThreadTitle.trim() }
        : {};

      const result = await onCreateThread(request);
      if (result) {
        setCreateDialogOpen(false);
        setNewThreadTitle("");
      }
    } catch (error) {
      console.error('Failed to create thread:', error);
    } finally {
      setIsCreating(false);
    }
  }, [newThreadTitle, onCreateThread, isCreating]);

  const handleCreateCancel = useCallback(() => {
    if (isCreating) return;
    setCreateDialogOpen(false);
    setNewThreadTitle("");
  }, [isCreating]);



  const handleDeleteConfirm = useCallback(async () => {
    if (!threadToDelete || isDeleting) return;

    setIsDeleting(true);
    try {
      const success = await onDeleteThread(threadToDelete.uuid);
      if (success) {
        setDeleteDialogOpen(false);
        setThreadToDelete(null);
      }
    } catch (error) {
      console.error('Failed to delete thread:', error);
    } finally {
      setIsDeleting(false);
    }
  }, [threadToDelete, onDeleteThread, isDeleting]);

  const handleDeleteCancel = useCallback(() => {
    if (isDeleting) return;
    setDeleteDialogOpen(false);
    setThreadToDelete(null);
  }, [isDeleting]);

  // Handle Enter key in create dialog
  const handleCreateKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleCreateConfirm();
    }
  }, [handleCreateConfirm]);

  return (
    <>
      {/* Create Thread Button */}
      <Button
        onClick={handleCreateClick}
        disabled={disabled}
        size="sm"
        variant="default"
        className={className}
      >
        <Plus className="h-4 w-4 mr-2" />
        新しいチャット
      </Button>

      {/* Create Thread Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              新しいチャットを作成
            </DialogTitle>
            <DialogDescription>
              新しいチャットスレッドを作成します。タイトルは省略可能です。
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="thread-title">
                タイトル（省略可能）
              </Label>
              <Input
                id="thread-title"
                placeholder="例: プロジェクトについて"
                value={newThreadTitle}
                onChange={(e) => setNewThreadTitle(e.target.value)}
                onKeyDown={handleCreateKeyDown}
                maxLength={100}
                disabled={isCreating}
                autoFocus
              />
              <p className="text-xs text-muted-foreground">
                タイトルを入力しない場合、自動的に生成されます
              </p>
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={handleCreateCancel}
              disabled={isCreating}
            >
              キャンセル
            </Button>
            <Button
              onClick={handleCreateConfirm}
              disabled={isCreating}
            >
              {isCreating ? "作成中..." : "作成"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Thread Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              チャットを削除
            </DialogTitle>
            <DialogDescription>
              この操作は取り消すことができません。
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <div className="p-4 bg-destructive/5 border border-destructive/20 rounded-lg">
              <p className="text-sm font-medium text-foreground mb-2">
                削除するチャット:
              </p>
              <p className="text-sm text-muted-foreground break-words">
                {threadToDelete?.title || "無題のチャット"}
              </p>
            </div>

            <div className="mt-4 space-y-2">
              <div className="flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
                <div className="text-sm text-muted-foreground">
                  <p className="font-medium text-destructive mb-1">
                    この操作により以下が削除されます:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>チャットスレッド</li>
                    <li>すべてのメッセージ履歴</li>
                    <li>関連するメタデータ</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={handleDeleteCancel}
              disabled={isDeleting}
            >
              キャンセル
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              {isDeleting ? "削除中..." : "削除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

interface DeleteThreadButtonProps {
  threadUuid: string;
  threadTitle: string;
  onDelete: (threadUuid: string, threadTitle: string) => void;
  disabled?: boolean;
  size?: "sm" | "default" | "lg";
  variant?: "ghost" | "outline" | "destructive";
  className?: string;
}

/**
 * 個別スレッド削除ボタンコンポーネント
 * スレッド一覧などで使用
 */
export function DeleteThreadButton({
  threadUuid,
  threadTitle,
  onDelete,
  disabled = false,
  size = "sm",
  variant = "ghost",
  className,
}: DeleteThreadButtonProps) {
  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent parent click events
    onDelete(threadUuid, threadTitle);
  }, [threadUuid, threadTitle, onDelete]);

  return (
    <Button
      size={size}
      variant={variant}
      onClick={handleClick}
      disabled={disabled}
      className={className}
      aria-label={`チャット「${threadTitle}」を削除`}
    >
      <Trash2 className="h-4 w-4" />
    </Button>
  );
}

interface CreateThreadButtonProps {
  onCreate: () => void;
  disabled?: boolean;
  size?: "sm" | "default" | "lg";
  variant?: "default" | "outline" | "ghost";
  className?: string;
  children?: React.ReactNode;
}

/**
 * スレッド作成ボタンコンポーネント
 * 様々な場所で再利用可能
 */
export function CreateThreadButton({
  onCreate,
  disabled = false,
  size = "default",
  variant = "default",
  className,
  children,
}: CreateThreadButtonProps) {
  return (
    <Button
      onClick={onCreate}
      disabled={disabled}
      size={size}
      variant={variant}
      className={className}
    >
      {children || (
        <>
          <Plus className="h-4 w-4 mr-2" />
          新しいチャット
        </>
      )}
    </Button>
  );
}