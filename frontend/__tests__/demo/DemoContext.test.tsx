import { renderHook, act } from '@testing-library/react';
import { DemoProvider, useDemo } from '@/components/contexts/DemoContext';
import { DemoStorage } from '@/utils/demoStorage';

// DemoStorageをモック
jest.mock('@/utils/demoStorage');
const mockDemoStorage = DemoStorage as jest.Mocked<typeof DemoStorage>;

describe('DemoContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
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

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <DemoProvider>{children}</DemoProvider>
  );

  it('should initialize demo session', async () => {
    const mockSession = {
      id: 'test-session',
      tasks: [],
      created_at: Date.now(),
      expires_at: Date.now() + 30 * 60 * 1000,
      limitations: {
        max_tasks: 10,
        max_duration: 30 * 60 * 1000,
        current_task_count: 0
      }
    };

    mockDemoStorage.loadSession.mockReturnValue(mockSession);

    const { result } = renderHook(() => useDemo(), { wrapper });

    act(() => {
      result.current.initializeSession();
    });

    expect(result.current.state.session).toEqual(mockSession);
    expect(result.current.state.isLoading).toBe(false);
  });

  it('should create new task', async () => {
    const mockSession = {
      id: 'test-session',
      tasks: [],
      created_at: Date.now(),
      expires_at: Date.now() + 30 * 60 * 1000,
      limitations: {
        max_tasks: 10,
        max_duration: 30 * 60 * 1000,
        current_task_count: 0
      }
    };

    mockDemoStorage.loadSession.mockReturnValue(mockSession);
    mockDemoStorage.addTask.mockReturnValue(true);

    const { result } = renderHook(() => useDemo(), { wrapper });

    act(() => {
      result.current.initializeSession();
    });

    const taskRequest = {
      title: 'Test Task',
      description: 'Test Description'
    };

    let success: boolean;
    await act(async () => {
      success = await result.current.createTask(taskRequest);
    });

    expect(success!).toBe(true);
    expect(mockDemoStorage.addTask).toHaveBeenCalled();
  });

  it('should respect task limit', async () => {
    const mockSession = {
      id: 'test-session',
      tasks: new Array(10).fill(null).map((_, i) => ({
        id: `task-${i}`,
        title: `Task ${i}`,
        completed: false,
        created_at: Date.now(),
        source_type: 'demo' as const
      })),
      created_at: Date.now(),
      expires_at: Date.now() + 30 * 60 * 1000,
      limitations: {
        max_tasks: 10,
        max_duration: 30 * 60 * 1000,
        current_task_count: 10
      }
    };

    mockDemoStorage.loadSession.mockReturnValue(mockSession);

    const { result } = renderHook(() => useDemo(), { wrapper });

    act(() => {
      result.current.initializeSession();
    });

    const taskRequest = {
      title: 'Test Task',
      description: 'Test Description'
    };

    let success: boolean;
    await act(async () => {
      success = await result.current.createTask(taskRequest);
    });

    expect(success!).toBe(false);
    expect(result.current.state.limitations).toHaveLength(1);
    expect(result.current.state.limitations[0].type).toBe('task_limit');
  });
});