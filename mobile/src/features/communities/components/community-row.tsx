import { StyleSheet, Text, View } from 'react-native';

import { spacing, typeScale, useAppTheme } from '@/theme';

import type { Community } from '../data/communities';

type CommunityRowProps = {
  community: Community;
};

export function CommunityRow({ community }: CommunityRowProps) {
  const colors = useAppTheme();
  const tone = colors.community[community.tone];
  const styles = makeStyles(colors);

  return (
    <View
      accessible
      accessibilityLabel={`${community.name}, ${community.topic}, ${community.members}, ${community.access}`}
      style={styles.row}
    >
      <View style={[styles.avatar, { backgroundColor: tone.background }]}>
        <Text style={[styles.monogram, { color: tone.foreground }]}>{community.monogram}</Text>
      </View>

      <View style={styles.copy}>
        <Text numberOfLines={1} style={styles.name}>
          {community.name}
        </Text>
        <Text numberOfLines={1} style={styles.meta}>
          {community.topic} <Text style={styles.separator}>·</Text> {community.members}
        </Text>
      </View>

      <View style={styles.activity}>
        <View style={styles.activityDot} />
        <Text style={styles.activityText}>{community.activeNow}</Text>
      </View>
    </View>
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
    activityDot: {
      width: 7,
      height: 7,
      borderRadius: 4,
      backgroundColor: colors.positive,
    },
    activityText: {
      color: colors.inkMuted,
      fontSize: typeScale.caption,
      fontVariant: ['tabular-nums'],
    },
  });
}
