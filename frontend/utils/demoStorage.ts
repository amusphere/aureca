import { DemoSession, DemoTask } from '@/types/Demo';
import { DEMO_LIMITATIONS } from './demoData';

export class DemoStorage {
  private static getSessionKey(): string {
    return DEMO_LIMITATIONS.SESSION_KEY;
  }

  static saveSession(session: DemoSession): void {
    try {
      sessionStorage.setItem(this.getSessionKey(), JSON.stringify(session));
    } catch (error) {
      console.error('Failed to save demo session:', error);
    }
  }

  static loadSession(): DemoSession | null {
    try {
      const sessionData = sessionStorage.getItem(this.getSessionKey());
      if (!sessionData) return null;

      const session: DemoSession = JSON.parse(sessionData);

      // セッションの有効期限をチェック（時間制限なしの場合はスキップ）
      if (session.expires_at && Date.now() > session.expires_at) {
        this.clearSession();
        return null;
      }

      return session;
    } catch (error) {
      console.error('Failed to load demo session:', error);
      return null;
    }
  }

  static updateTasks(tasks: DemoTask[]): void {
    const session = this.loadSession();
    if (!session) return;

    session.tasks = tasks;
    session.limitations.current_task_count = tasks.length;
    this.saveSession(session);
  }

  static addTask(task: DemoTask): boolean {
    const session = this.loadSession();
    if (!session) return false;

    session.tasks.push(task);
    session.limitations.current_task_count = session.tasks.length;
    this.saveSession(session);
    return true;
  }

  static updateTask(taskId: string, updates: Partial<DemoTask>): boolean {
    const session = this.loadSession();
    if (!session) return false;

    const taskIndex = session.tasks.findIndex(task => task.id === taskId);
    if (taskIndex === -1) return false;

    session.tasks[taskIndex] = { ...session.tasks[taskIndex], ...updates };
    this.saveSession(session);
    return true;
  }

  static deleteTask(taskId: string): boolean {
    const session = this.loadSession();
    if (!session) return false;

    const taskIndex = session.tasks.findIndex(task => task.id === taskId);
    if (taskIndex === -1) return false;

    session.tasks.splice(taskIndex, 1);
    session.limitations.current_task_count = session.tasks.length;
    this.saveSession(session);
    return true;
  }

  static clearSession(): void {
    try {
      sessionStorage.removeItem(this.getSessionKey());
    } catch (error) {
      console.error('Failed to clear demo session:', error);
    }
  }

  static isSessionExpired(): boolean {
    const session = this.loadSession();
    if (!session) return true;
    if (!session.expires_at) return false; // 時間制限なしの場合は期限切れなし
    return Date.now() > session.expires_at;
  }

  static getRemainingTime(): number {
    const session = this.loadSession();
    if (!session || !session.expires_at) return Infinity; // 時間制限なしの場合は無限
    return Math.max(0, session.expires_at - Date.now());
  }
}