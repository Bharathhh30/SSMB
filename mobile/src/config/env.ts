export type AppEnvironment = 'development' | 'staging' | 'production';

const rawAppEnvironment = process.env.EXPO_PUBLIC_APP_ENV;
const supportedEnvironments = ['development', 'staging', 'production'] as const;
const isAppEnvironment = (value: string): value is AppEnvironment =>
  supportedEnvironments.some((environment) => environment === value);
const appEnvironment = rawAppEnvironment
  ? isAppEnvironment(rawAppEnvironment)
    ? rawAppEnvironment
    : 'invalid'
  : 'development';

export const publicConfig = {
  appEnvironment,
  apiBaseUrl: process.env.EXPO_PUBLIC_API_BASE_URL?.trim() ?? '',
  webBaseUrl: process.env.EXPO_PUBLIC_WEB_BASE_URL?.trim() ?? '',
} as const;

export function getApiBaseUrl(): string {
  const baseUrl = publicConfig.apiBaseUrl;
  const hasHttpProtocol = /^https?:\/\/[^/\s]+/i.test(baseUrl);
  const isExampleUrl = baseUrl.includes('replace-with-your-backend-tunnel');

  if (publicConfig.appEnvironment === 'invalid') {
    throw new Error('EXPO_PUBLIC_APP_ENV must be development, staging, or production.');
  }

  if (!baseUrl || isExampleUrl || !hasHttpProtocol) {
    throw new Error(
      'Set EXPO_PUBLIC_API_BASE_URL in mobile/.env.development.local, then restart Expo.',
    );
  }

  if (publicConfig.appEnvironment === 'production' && !/^https:\/\//i.test(baseUrl)) {
    throw new Error('Production API URLs must use HTTPS.');
  }

  return baseUrl.replace(/\/+$/, '');
}
