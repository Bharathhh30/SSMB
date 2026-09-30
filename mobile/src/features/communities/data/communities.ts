import type { ApiCommunity } from '@/features/communities/api/communities-api';

export type CommunityTopic = 'Exam prep' | 'Technology' | 'Languages' | 'Creative';
export type CommunityTone = 'sage' | 'apricot' | 'lilac' | 'sky' | 'rose';

export type Community = {
  id: string;
  slug?: string;
  name: string;
  topic: string;
  description: string;
  members?: string;
  activeNow?: number;
  access: 'Open' | 'Invite only';
  tone: CommunityTone;
  monogram: string;
  tags: string[];
};

export const communityTopics: CommunityTopic[] = [
  'Exam prep',
  'Technology',
  'Languages',
  'Creative',
];

export const communities: Community[] = [
  {
    id: 'gate-quant-lab',
    name: 'GATE Quant Lab',
    topic: 'Exam prep',
    description: 'Focused problem-solving, one small win at a time.',
    members: '2.4k members',
    activeNow: 38,
    access: 'Open',
    tone: 'sage',
    monogram: 'GQ',
    tags: ['GATE', 'Quantitative aptitude', 'Study group'],
  },
  {
    id: 'jee-study-hall',
    name: 'JEE Study Hall',
    topic: 'Exam prep',
    description: 'A calm, consistent space for JEE preparation.',
    members: '1.8k members',
    activeNow: 24,
    access: 'Open',
    tone: 'apricot',
    monogram: 'J',
    tags: ['JEE', 'Physics', 'Chemistry', 'Maths'],
  },
  {
    id: 'react-native-makers',
    name: 'React Native Makers',
    topic: 'Technology',
    description: 'Build, share, and learn from each other.',
    members: '960 members',
    activeNow: 17,
    access: 'Open',
    tone: 'sky',
    monogram: 'RN',
    tags: ['React Native', 'Expo', 'Mobile development'],
  },
  {
    id: 'design-product-notes',
    name: 'Design + Product Notes',
    topic: 'Creative',
    description: 'Thoughtful critique for people who make things.',
    members: '740 members',
    activeNow: 9,
    access: 'Invite only',
    tone: 'lilac',
    monogram: 'D+',
    tags: ['Product design', 'Portfolio', 'Feedback'],
  },
  {
    id: 'language-exchange',
    name: 'Language Exchange',
    topic: 'Languages',
    description: 'Practice a new language with friendly people.',
    members: '1.2k members',
    activeNow: 21,
    access: 'Open',
    tone: 'rose',
    monogram: 'L',
    tags: ['Languages', 'Conversation', 'Practice'],
  },
];

export const featuredCommunity = communities[0];
export const joinedCommunityIds = ['gate-quant-lab', 'react-native-makers'];
export const joinedCommunities = communities.filter((community) =>
  joinedCommunityIds.includes(community.id),
);

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
    tags: [],
  };
}
