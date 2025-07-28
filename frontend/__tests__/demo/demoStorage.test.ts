import { DemoStorage } from '@/utils/demoStorage';
import { DemoSession, DemoTask } from '@/types/Demo';

describe('DemoStorage', () => {
  beforeEach(() => {
    // sessionStorageのモック
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  const mockSession: DemoSession = {
    id: 'test-session',
    tasks: [
      {
        id: 'task-1',
        title: 'Test Task',
        description: 'Test Description',
        completed: false,
        created_at: Date.now(),
        source_type: 'demo'
      }
    ],
    created_at: Date.now(),
    expires_at: Date.now() + 30 * 60 * 1000,
    limitations: {
      max_tasks: 10,
      max_duration: 30 * 60 * 1000,
      current_task_count: 1
    }
  };

  it('should save session to sessionStorage', () => {
    DemoStorage.saveSession(mockSession);

    expect(sessionStorage.setItem).toHaveBeenCalledWith(
      'demo_session',
      JSON.stringify(mockSession)
    );
  });

  it('should load session from sessionStorage', () => {
    (sessionStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(mockSession));

    const result = DemoStorage.loadSession();

    expect(result).toEqual(mockSession);
    expect(sessionStorage.getItem).toHaveBeenCalledWith('demo_session');
  });

  it('should return null for expired session', () => {
    const expiredSession = {
      ...mockSession,
      expires_at: Date.now() - 1000 // 1秒前に期限切れ
    };

    (sessionStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(expiredSession));

    const result = DemoStorage.loadSession();

    expect(result).toBeNull();
    expect(sessionStorage.removeItem).toHaveBeenCalledWith('demo_session');
  });

  it('should add task to session', () => {
    (sessionStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(mockSession));

    const newTask: DemoTask = {
      id: 'task-2',
      title: 'New Task',
      completed: false,
      created_at: Date.now(),
      source_type: 'demo'
    };

    const result = DemoStorage.addTask(newTask);

    expect(result).toBe(true);
    expect(sessionStorage.setItem).toHaveBeenCalled();
  });

  it('should not add task when limit reached', () => {
    const fullSession = {
      ...mockSession,
      tasks: new Array(10).fill(null).map((_, i) => ({
        id: `task-${i}`,
        title: `Task ${i}`,
        completed: false,
        created_at: Date.now(),
        source_type: 'demo' as const
      })),
      limitations: {
        ...mockSession.limitations,
        current_task_count: 10
      }
    };

    (sessionStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(fullSession));

    const newTask: DemoTask = {
      id: 'task-11',
      title: 'Overflow Task',
      completed: false,
      created_at: Date.now(),
      source_type: 'demo'
    };

    const result = DemoStorage.addTask(newTask);

    expect(result).toBe(false);
  });

  it('should update existing task', () => {
    (sessionStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(mockSession));

    const result = DemoStorage.updateTask('task-1', { completed: true });

    expect(result).toBe(true);
    expect(sessionStorage.setItem).toHaveBeenCalled();
  });

  it('should delete task', () => {
    (sessionStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(mockSession));

    const result = DemoStorage.deleteTask('task-1');

    expect(result).toBe(true);
    expect(sessionStorage.setItem).toHaveBeenCalled();
  });

  it('should clear session', () => {
    DemoStorage.clearSession();

    expect(sessionStorage.removeItem).toHaveBeenCalledWith('demo_session');
  });

  it('should check if session is expired', () => {
    const expiredSession = {
      ...mockSession,
      expires_at: Date.now() - 1000
    };

    (sessionStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(expiredSession));

    const result = DemoStorage.isSessionExpired();

    expect(result).toBe(true);
  });

  it('should get remaining time', () => {
    const futureTime = Date.now() + 10 * 60 * 1000; // 10分後
    const sessionWithFutureExpiry = {
      ...mockSession,
      expires_at: futureTime
    };

    (sessionStorage.getItem as jest.Mock).mockReturnValue(JSON.stringify(sessionWithFutureExpiry));

    const result = DemoStorage.getRemainingTime();

    expect(result).toBeGreaterThan(0);
    expect(result).toBeLessThanOrEqual(10 * 60 * 1000);
  });
});