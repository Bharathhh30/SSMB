import type { ApiCommunity } from '@/features/communities/api/communities-api';

export type CommunityTopic = 'Exam prep' | 'Technology' | 'Languages' | 'Creative';
export type CommunityTone = 'sage' | 'apricot' | 'lilac' | 'sky' | 'rose';

export type Community = {
  id: string;
  slug?: string;
  name: string;
  topic: string;
  description: string;
  access: 'Open' | 'Invite only';
  tone: CommunityTone;
  monogram: string;
};

export const communityTopics: CommunityTopic[] = [
  'Exam prep',
  'Technology',
  'Languages',
  'Creative',
];

const communityTones: CommunityTone[] = ['sage', 'apricot', 'lilac', 'sky', 'rose'];

export function toCommunityCard(community: ApiCommunity): Community {
  const toneIndex = [...community.id].reduce(
    (total, character) => total + character.charCodeAt(0),
    0,
  );
  const monogram = community.name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toLocaleUpperCase();

  return {
    id: community.id,
    slug: community.slug,
    name: community.name,
    topic: community.topic,
    description: community.description,
    access: community.access_type === 'open' ? 'Open' : 'Invite only',
    tone: communityTones[toneIndex % communityTones.length],
    monogram,
  };
}
