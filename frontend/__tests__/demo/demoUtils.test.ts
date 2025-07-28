import { isDemoEnvironment, checkDemoFeatureAccess, DEMO_AI_RESTRICTION_MESSAGE } from '@/utils/demoUtils';

// window.locationのモック
const mockLocation = {
  pathname: '/'
};

Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

describe('demoUtils', () => {
  describe('isDemoEnvironment', () => {
    it('should return true for demo path', () => {
      mockLocation.pathname = '/demo';
      expect(isDemoEnvironment()).toBe(true);
    });

    it('should return true for demo sub-paths', () => {
      mockLocation.pathname = '/demo/test';
      expect(isDemoEnvironment()).toBe(true);
    });

    it('should return false for non-demo paths', () => {
      mockLocation.pathname = '/';
      expect(isDemoEnvironment()).toBe(false);

      mockLocation.pathname = '/home';
      expect(isDemoEnvironment()).toBe(false);
    });
  });

  describe('checkDemoFeatureAccess', () => {
    beforeEach(() => {
      mockLocation.pathname = '/';
    });

    it('should allow features in non-demo environment', () => {
      mockLocation.pathname = '/home';

      expect(checkDemoFeatureAccess('ai_chat')).toEqual({ allowed: true });
      expect(checkDemoFeatureAccess('integrations')).toEqual({ allowed: true });
      expect(checkDemoFeatureAccess('advanced_features')).toEqual({ allowed: true });
    });

    it('should restrict AI chat in demo environment', () => {
      mockLocation.pathname = '/demo';

      const result = checkDemoFeatureAccess('ai_chat');

      expect(result.allowed).toBe(false);
      expect(result.message).toBe('AI チャット機能は本格利用でのみご利用いただけます');
    });

    it('should restrict integrations in demo environment', () => {
      mockLocation.pathname = '/demo';

      const result = checkDemoFeatureAccess('integrations');

      expect(result.allowed).toBe(false);
      expect(result.message).toBe('外部サービス連携は本格利用でのみご利用いただけます');
    });

    it('should restrict advanced features in demo environment', () => {
      mockLocation.pathname = '/demo';

      const result = checkDemoFeatureAccess('advanced_features');

      expect(result.allowed).toBe(false);
      expect(result.message).toBe('高度な機能は本格利用でのみご利用いただけます');
    });
  });

  describe('DEMO_AI_RESTRICTION_MESSAGE', () => {
    it('should have correct restriction message', () => {
      expect(DEMO_AI_RESTRICTION_MESSAGE).toEqual({
        title: 'AI機能はデモでは利用できません',
        description: 'AI アシスタント機能は本格利用でのみご利用いただけます。登録して全機能をお試しください。',
        action: '本格利用を開始'
      });
    });
  });
});