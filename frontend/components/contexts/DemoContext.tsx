'use client';

import React, { createContext, useContext, useReducer, useEffect, useCallback, ReactNode } from 'react';
import { DemoTask, DemoSession, DemoLimitation, CreateDemoTaskRequest, UpdateDemoTaskRequest } from '@/types/Demo';
import { DemoStorage } from '@/utils/demoStorage';
import { createDemoSession } from '@/utils/demoData';

interface DemoState {
  session: DemoSession | null;
  isLoading: boolean;
  error: string | null;
  limitations: DemoLimitation[];
}

type DemoAction =
  | { type: 'INIT_SESSION'; payload: DemoSession }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ADD_TASK'; payload: DemoTask }
  | { type: 'UPDATE_TASK'; payload: { id: string; updates: Partial<DemoTask> } }
  | { type: 'DELETE_TASK'; payload: string }
  | { type: 'SET_LIMITATIONS'; payload: DemoLimitation[] }
  | { type: 'RESET_SESSION' }
  | { type: 'CLEAR_SESSION' };

const initialState: DemoState = {
  session: null,
  isLoading: true,
  error: null,
  limitations: []
};

function demoReducer(state: DemoState, action: DemoAction): DemoState {
  switch (action.type) {
    case 'INIT_SESSION':
      return {
        ...state,
        session: action.payload,
        isLoading: false,
        error: null
      };

    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false
      };

    case 'ADD_TASK':
      if (!state.session) return state;
      return {
        ...state,
        session: {
          ...state.session,
          tasks: [...state.session.tasks, action.payload],
          limitations: {
            ...state.session.limitations,
            current_task_count: state.session.tasks.length + 1
          }
        }
      };

    case 'UPDATE_TASK':
      if (!state.session) return state;
      return {
        ...state,
        session: {
          ...state.session,
          tasks: state.session.tasks.map(task =>
            task.id === action.payload.id
              ? { ...task, ...action.payload.updates }
              : task
          )
        }
      };

    case 'DELETE_TASK':
      if (!state.session) return state;
      return {
        ...state,
        session: {
          ...state.session,
          tasks: state.session.tasks.filter(task => task.id !== action.payload),
          limitations: {
            ...state.session.limitations,
            current_task_count: state.session.tasks.length - 1
          }
        }
      };

    case 'SET_LIMITATIONS':
      return {
        ...state,
        limitations: action.payload
      };

    case 'RESET_SESSION':
      const newSession = createDemoSession();
      return {
        ...state,
        session: newSession,
        error: null,
        limitations: []
      };

    case 'CLEAR_SESSION':
      return {
        ...state,
        session: null,
        error: null,
        limitations: []
      };

    default:
      return state;
  }
}

interface DemoContextType {
  state: DemoState;
  initializeSession: () => void;
  createTask: (task: CreateDemoTaskRequest) => Promise<boolean>;
  updateTask: (id: string, updates: UpdateDemoTaskRequest) => Promise<boolean>;
  deleteTask: (id: string) => Promise<boolean>;
  resetSession: () => void;
  clearSession: () => void;
  getRemainingTime: () => number;
  checkLimitations: () => DemoLimitation[];
}

const DemoContext = createContext<DemoContextType | undefined>(undefined);

export function DemoProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(demoReducer, initialState);

  const initializeSession = useCallback(() => {
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      let session = DemoStorage.loadSession();

      if (!session || DemoStorage.isSessionExpired()) {
        session = createDemoSession();
        DemoStorage.saveSession(session);
      }

      dispatch({ type: 'INIT_SESSION', payload: session });
    } catch (err) {
      console.error('Session initialization error:', err);
      dispatch({ type: 'SET_ERROR', payload: 'セッションの初期化に失敗しました' });
    }
  }, []);

  const createTask = async (taskRequest: CreateDemoTaskRequest): Promise<boolean> => {
    if (!state.session) return false;

    const newTask: DemoTask = {
      id: `demo-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      title: taskRequest.title,
      description: taskRequest.description,
      completed: false,
      expires_at: taskRequest.expires_at,
      created_at: Date.now(),
      source_type: 'demo'
    };

    const success = DemoStorage.addTask(newTask);
    if (success) {
      dispatch({ type: 'ADD_TASK', payload: newTask });
    }

    return success;
  };

  const updateTask = async (id: string, updates: UpdateDemoTaskRequest): Promise<boolean> => {
    const success = DemoStorage.updateTask(id, updates);
    if (success) {
      dispatch({ type: 'UPDATE_TASK', payload: { id, updates } });
    }
    return success;
  };

  const deleteTask = async (id: string): Promise<boolean> => {
    const success = DemoStorage.deleteTask(id);
    if (success) {
      dispatch({ type: 'DELETE_TASK', payload: id });
    }
    return success;
  };

  const resetSession = () => {
    const newSession = createDemoSession();
    DemoStorage.saveSession(newSession);
    dispatch({ type: 'RESET_SESSION' });
  };

  const clearSession = () => {
    DemoStorage.clearSession();
    dispatch({ type: 'CLEAR_SESSION' });
  };

  const getRemainingTime = useCallback((): number => {
    return DemoStorage.getRemainingTime();
  }, []);

  const checkLimitations = useCallback((): DemoLimitation[] => {
    // 時間制限を削除したため、制限チェックは不要
    return [];
  }, []);

  // 時間制限を削除したため、セッション監視は不要

  // ページ離脱時のクリーンアップ
  useEffect(() => {
    const handleBeforeUnload = () => {
      // セッションは自動的に期限切れになるため、特別なクリーンアップは不要
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  const contextValue: DemoContextType = {
    state,
    initializeSession,
    createTask,
    updateTask,
    deleteTask,
    resetSession,
    clearSession,
    getRemainingTime,
    checkLimitations
  };

  return (
    <DemoContext.Provider value={contextValue}>
      {children}
    </DemoContext.Provider>
  );
}

export function useDemo(): DemoContextType {
  const context = useContext(DemoContext);
  if (context === undefined) {
    throw new Error('useDemo must be used within a DemoProvider');
  }
  return context;
}