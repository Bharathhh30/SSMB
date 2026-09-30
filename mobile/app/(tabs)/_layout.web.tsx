import { Tabs } from 'expo-router';

import { AppSymbol } from '@/components/app-symbol';
import { typeScale, useAppTheme } from '@/theme';

export default function WebTabLayout() {
  const colors = useAppTheme();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.inkSubtle,
        tabBarLabelStyle: {
          fontSize: typeScale.caption,
          lineHeight: typeScale.footnote,
          fontWeight: '600',
        },
        tabBarStyle: {
          height: 64,
          paddingTop: 4,
          paddingBottom: 6,
          backgroundColor: colors.surface,
          borderTopColor: colors.hairline,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size }) => <AppSymbol color={color} name="people" size={size} />,
        }}
      />
      <Tabs.Screen
        name="discover"
        options={{
          title: 'Discover',
          tabBarIcon: ({ color, size }) => <AppSymbol color={color} name="search" size={size} />,
        }}
      />
    </Tabs>
  );
}
