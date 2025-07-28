'use client';

import { Button } from '@/components/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/components/ui/card';
import { Lock, ArrowRight } from 'lucide-react';
import Link from 'next/link';

interface DemoFeatureRestrictionProps {
  title: string;
  description: string;
  feature: string;
  className?: string;
}

export function DemoFeatureRestriction({
  title,
  description,
  feature,
  className = ''
}: DemoFeatureRestrictionProps) {
  return (
    <Card className={`bg-gray-50 border-gray-200 ${className}`}>
      <CardHeader className="text-center">
        <div className="mx-auto w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center mb-4">
          <Lock className="h-6 w-6 text-gray-500" />
        </div>
        <CardTitle className="text-gray-700">{title}</CardTitle>
        <CardDescription className="text-gray-600">
          {description}
        </CardDescription>
      </CardHeader>
      <CardContent className="text-center">
        <div className="space-y-3">
          <p className="text-sm text-gray-600">
            「{feature}」機能を利用するには本格利用への登録が必要です
          </p>
          <Link href="/">
            <Button className="flex items-center space-x-2">
              <span>本格利用を開始</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}