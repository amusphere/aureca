import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import HomePage from '@/components/pages/HomePage';

// Mock the hooks and components
vi.mock('@/components/hooks/useUser', () => ({
  useUser: vi.fn()
}));

vi.mock('@/components/components/commons/AIChat', () => ({
  default: () => <div data-testid="ai-chat">AI Chat</div>
}));

vi.mock('@/components/components/commons/AIUpgradePrompt', () => ({
  AIUpgradePrompt: () => <div data-testid="ai-upgrade-prompt">AI Upgrade Prompt</div>
}));

vi.mock('@/components/components/tasks/TaskList', () => ({
  TaskList: () => <div data-testid="task-list">Task List</div>
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}));

import { useUser } from '@/components/hooks/useUser';

const mockUseUser = useUser as any;

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows AI upgrade prompt for non-premium users', () => {
    mockUseUser.mockReturnValue({
      user: { id: 1, email: 'test@example.com' },
      isLoading: false,
      isPremium: false,
      error: null,
      refreshUser: vi.fn()
    });

    render(<HomePage />);

    expect(screen.getByTestId('ai-upgrade-prompt')).toBeInTheDocument();
    expect(screen.queryByTestId('ai-chat')).not.toBeInTheDocument();
    expect(screen.getByTestId('task-list')).toBeInTheDocument();
  });

  it('shows AI chat for premium users', () => {
    mockUseUser.mockReturnValue({
      user: { id: 1, email: 'test@example.com' },
      isLoading: false,
      isPremium: true,
      error: null,
      refreshUser: vi.fn()
    });

    render(<HomePage />);

    expect(screen.queryByTestId('ai-upgrade-prompt')).not.toBeInTheDocument();
    expect(screen.getByTestId('ai-chat')).toBeInTheDocument();
    expect(screen.getByTestId('task-list')).toBeInTheDocument();
  });

  it('shows loading state while user data is loading', () => {
    mockUseUser.mockReturnValue({
      user: null,
      isLoading: true,
      isPremium: false,
      error: null,
      refreshUser: vi.fn()
    });

    render(<HomePage />);

    expect(screen.getByTestId('task-list')).toBeInTheDocument();
    // Loading states are handled within PremiumGuard components
  });

  it('handles unauthenticated users', () => {
    mockUseUser.mockReturnValue({
      user: null,
      isLoading: false,
      isPremium: false,
      error: null,
      refreshUser: vi.fn()
    });

    render(<HomePage />);

    expect(screen.queryByTestId('ai-upgrade-prompt')).not.toBeInTheDocument();
    expect(screen.queryByTestId('ai-chat')).not.toBeInTheDocument();
    expect(screen.getByTestId('task-list')).toBeInTheDocument();
  });
});