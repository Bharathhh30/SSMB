import { useColorScheme } from 'react-native';

export const spacing = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 22,
  xl: 30,
  xxl: 40,
  xxxl: 52,
} as const;

export const radius = {
  sm: 12,
  md: 18,
  lg: 24,
  xl: 30,
  full: 999,
} as const;

export const layout = {
  readingWidth: 560,
} as const;

export const typeScale = {
  caption: 12,
  footnote: 13,
  body: 15,
  subheading: 18,
  title: 26,
  display: 36,
} as const;

export const motion = {
  pressDuration: '120ms',
  pressScale: 0.975,
  contentEntranceDuration: 250,
  reducedContentEntranceDuration: 150,
  contentEntranceOffset: 8,
} as const;

export const themeBackgrounds = {
  light: '#F5F4EF',
  dark: '#111814',
} as const;

const light = {
  canvas: themeBackgrounds.light,
  surface: '#FFFFFF',
  surfaceMuted: '#ECEDE7',
  ink: '#1C2923',
  inkMuted: '#65716A',
  inkSubtle: '#87928A',
  hairline: '#E1E5DF',
  accent: '#176449',
  accentSoft: '#E1EEE5',
  accentInk: '#154A38',
  hero: '#173D30',
  heroInk: '#F8F7EF',
  heroMuted: '#C8D7CE',
  heroOutline: '#F8F7EF33',
  heroAccentOutline: '#D9EF7855',
  highlight: '#D9EF78',
  highlightInk: '#26331D',
  positive: '#2D7956',
  positiveSoft: '#E4F1E7',
  community: {
    sage: { background: '#DCEBE0', foreground: '#245840' },
    apricot: { background: '#F3E3D0', foreground: '#7D4F27' },
    lilac: { background: '#E6E0F1', foreground: '#57477A' },
    sky: { background: '#DDEAF0', foreground: '#345B70' },
    rose: { background: '#F1E0DC', foreground: '#814D43' },
  },
} as const;

const dark = {
  canvas: themeBackgrounds.dark,
  surface: '#1A241E',
  surfaceMuted: '#222E27',
  ink: '#F0F3ED',
  inkMuted: '#B3BEB6',
  inkSubtle: '#8F9C93',
  hairline: '#334139',
  accent: '#9DD2B0',
  accentSoft: '#263B2E',
  accentInk: '#C8E5D0',
  hero: '#19382B',
  heroInk: '#F3F5EC',
  heroMuted: '#C4D5CA',
  heroOutline: '#F3F5EC33',
  heroAccentOutline: '#D9EF7855',
  highlight: '#D9EF78',
  highlightInk: '#26331D',
  positive: '#9DD2B0',
  positiveSoft: '#263B2E',
  community: {
    sage: { background: '#2A4636', foreground: '#C4E3CE' },
    apricot: { background: '#493A2C', foreground: '#F0CEAA' },
    lilac: { background: '#3C344F', foreground: '#D7C9F2' },
    sky: { background: '#293E48', foreground: '#C0DFEC' },
    rose: { background: '#493432', foreground: '#F0C8BE' },
  },
} as const;

export type AppColors = {
  [Key in keyof typeof light]: (typeof light)[Key];
};

export function useAppTheme(): AppColors {
  const scheme = useColorScheme();
  return (scheme === 'dark' ? dark : light) as AppColors;
}
