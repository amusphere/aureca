import { DemoProvider } from '@/components/contexts/DemoContext';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'デモ - タスク管理システム',
  description: 'タスク管理システムのデモ版です。認証なしで主要機能をお試しいただけます。',
};

export default function DemoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <DemoProvider>
      {children}
    </DemoProvider>
  );
}