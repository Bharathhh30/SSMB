import { Pressable, StyleSheet, Text, View } from 'react-native';

import { spacing, typeScale, useAppTheme } from '@/theme';

import type { Community } from '../data/communities';

type CommunityRowProps = {
  community: Community;
  onPress?: () => void;
};

export function CommunityRow({ community, onPress }: CommunityRowProps) {
  const colors = useAppTheme();
  const tone = colors.community[community.tone];
  const styles = makeStyles(colors);
  const accessibilityLabel = `${community.name}, ${community.topic}, ${community.access}`;
  const content = (
    <>
      <View style={[styles.avatar, { backgroundColor: tone.background }]}>
        <Text style={[styles.monogram, { color: tone.foreground }]}>{community.monogram}</Text>
      </View>

      <View style={styles.copy}>
        <Text numberOfLines={1} style={styles.name}>
          {community.name}
        </Text>
        <Text numberOfLines={1} style={styles.meta}>
          {community.topic} <Text style={styles.separator}>·</Text> {community.description}
        </Text>
      </View>

      <View style={styles.activity}>
        <Text style={styles.accessText}>{community.access}</Text>
      </View>
    </>
  );

  if (!onPress) {
    return (
      <View accessible accessibilityLabel={accessibilityLabel} style={styles.row}>
        {content}
      </View>
    );
  }

  return (
    <Pressable
      accessible
      accessibilityLabel={accessibilityLabel}
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.row, pressed ? styles.rowPressed : null]}
    >
      {content}
    </Pressable>
  );
}

function makeStyles(colors: ReturnType<typeof useAppTheme>) {
  return StyleSheet.create({
    row: {
      width: '100%',
      minWidth: 0,
      minHeight: 78,
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.md,
      paddingVertical: spacing.sm,
    },
    rowPressed: {
      backgroundColor: colors.surfaceMuted,
    },
    avatar: {
      width: 50,
      height: 50,
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 17,
      borderCurve: 'continuous',
    },
    monogram: {
      fontSize: typeScale.body,
      fontWeight: '700',
      letterSpacing: -0.4,
    },
    copy: {
      flex: 1,
      minWidth: 0,
      gap: spacing.xxs,
    },
    name: {
      color: colors.ink,
      fontSize: typeScale.body,
      fontWeight: '600',
      letterSpacing: -0.2,
    },
    meta: {
      color: colors.inkMuted,
      fontSize: typeScale.footnote,
    },
    separator: {
      color: colors.inkSubtle,
    },
    activity: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.xs,
      paddingLeft: spacing.xs,
    },
    accessText: {
      color: colors.inkMuted,
      fontSize: typeScale.caption,
      fontWeight: '600',
      textAlign: 'right',
    },
  });
}
