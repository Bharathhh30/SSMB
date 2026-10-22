import { describe, expect, it } from 'vitest';

import { toggleProfileInterest, validateProfileDraft } from '@/features/auth/profile-draft';

describe('profile draft helpers', () => {
  it('requires a display name for previewing', () => {
    expect(validateProfileDraft({ displayName: '  ', interests: [] })).toBe(
      'Add a display name to preview your profile.',
    );
  });

  it('allows a name without selecting interests', () => {
    expect(validateProfileDraft({ displayName: 'Sam', interests: [] })).toBeUndefined();
  });

  it('adds and removes an interest without mutating the original selection', () => {
    const selected = ['Technology'];
    const added = toggleProfileInterest(selected, 'Languages');
    const removed = toggleProfileInterest(added, 'Technology');

    expect(added).toEqual(['Technology', 'Languages']);
    expect(removed).toEqual(['Languages']);
    expect(selected).toEqual(['Technology']);
  });
});
