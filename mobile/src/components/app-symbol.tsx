import { SymbolView } from 'expo-symbols';
import type { SymbolViewProps } from 'expo-symbols';
import type { ColorValue } from 'react-native';

const symbols = {
  search: { ios: 'magnifyingglass', android: 'search', web: 'search' },
  arrowRight: { ios: 'arrow.right', android: 'arrow_forward', web: 'arrow_forward' },
  close: { ios: 'xmark', android: 'close', web: 'close' },
  people: { ios: 'person.2.fill', android: 'group', web: 'group' },
  sparkle: { ios: 'sparkles', android: 'auto_awesome', web: 'auto_awesome' },
  share: {
    ios: 'square.and.arrow.up',
    android: 'ios_share',
    web: 'share',
  },
} satisfies Record<string, SymbolViewProps['name']>;

export type AppSymbolName = keyof typeof symbols;

type AppSymbolProps = {
  name: AppSymbolName;
  color: ColorValue;
  size?: number;
};

export function AppSymbol({ name, color, size = 20 }: AppSymbolProps) {
  return <SymbolView accessible={false} name={symbols[name]} tintColor={color} size={size} />;
}
