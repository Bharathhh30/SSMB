export type ProfileDraft = {
  displayName: string;
  interests: string[];
};

export function validateProfileDraft(draft: ProfileDraft): string | undefined {
  if (!draft.displayName.trim()) {
    return 'Add a display name to preview your profile.';
  }

  return undefined;
}

export function toggleProfileInterest(selected: string[], interest: string): string[] {
  return selected.includes(interest)
    ? selected.filter((item) => item !== interest)
    : [...selected, interest];
}
