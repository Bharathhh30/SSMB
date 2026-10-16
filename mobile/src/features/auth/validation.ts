export type CredentialsMode = 'sign-in' | 'sign-up';

export type CredentialsDraft = {
  displayName: string;
  email: string;
  password: string;
};

export type CredentialsErrors = Partial<Record<keyof CredentialsDraft, string>>;

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateCredentials(
  mode: CredentialsMode,
  draft: CredentialsDraft,
): CredentialsErrors {
  const errors: CredentialsErrors = {};
  const email = draft.email.trim();

  if (mode === 'sign-up' && draft.displayName.trim().length < 2) {
    errors.displayName = 'Enter a name with at least 2 characters.';
  }

  if (!email) {
    errors.email = 'Enter your email address.';
  } else if (!emailPattern.test(email)) {
    errors.email = 'Enter an email address in the format name@example.com.';
  }

  if (!draft.password) {
    errors.password = 'Enter your password.';
  }

  return errors;
}
