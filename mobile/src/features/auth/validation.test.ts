import { describe, expect, it } from 'vitest';

import { validateCredentials } from '@/features/auth/validation';

describe('validateCredentials', () => {
  it('requires a name, valid email, and password for sign-up', () => {
    expect(
      validateCredentials('sign-up', {
        displayName: 'A',
        email: 'not-an-email',
        password: '',
      }),
    ).toEqual({
      displayName: 'Enter a name with at least 2 characters.',
      email: 'Enter an email address in the format name@example.com.',
      password: 'Enter your password.',
    });
  });

  it('accepts a valid sign-up draft after trimming the name and email', () => {
    expect(
      validateCredentials('sign-up', {
        displayName: '  Sam  ',
        email: ' sam@example.com ',
        password: 'draft-password',
      }),
    ).toEqual({});
  });

  it('does not require a display name for sign-in', () => {
    expect(
      validateCredentials('sign-in', {
        displayName: '',
        email: 'sam@example.com',
        password: 'anything',
      }),
    ).toEqual({});
  });

  it('reports missing sign-in fields without echoing user input', () => {
    expect(
      validateCredentials('sign-in', {
        displayName: '',
        email: '',
        password: '',
      }),
    ).toEqual({
      email: 'Enter your email address.',
      password: 'Enter your password.',
    });
  });
});
