import { useCallback, useMemo } from 'react';
import { FlatList, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';

import { AppSymbol } from '@/components/app-symbol';
import { MotionPressable } from '@/components/motion-pressable';
import { CommunityRow } from '@/features/communities/components/community-row';
import { featuredCommunity, joinedCommunities } from '@/features/communities/data/communities';
import { layout, radius, spacing, typeScale, useAppTheme } from '@/theme';

const LONG_DATE_FORMATTER = new Intl.DateTimeFormat(undefined, {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
});

const greetingForHour = (hour: number) => {
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
};

export default function HomeScreen() {
  const colors = useAppTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const router = useRouter();

  const openDiscover = useCallback(
    (topic?: string) => {
      router.push(topic ? { pathname: '/discover', params: { topic } } : '/discover');
    },
    [router],
  );

  const renderCommunity = useCallback(
    ({ item }: { item: (typeof joinedCommunities)[number] }) => (
      <CommunityRow community={item} />
    ),
    [],
  );

  const separator = useCallback(() => <View style={styles.separator} />, [styles.separator]);

  const listHeader = useMemo(
    () => (
      <View style={styles.headerContent}>
        <View style={styles.intro}>
          <View style={styles.eyebrowRow}>
            <View style={styles.eyebrowDot} />
            <Text style={styles.eyebrow}>A BETTER WAY TO LEARN</Text>
          </View>
          <Text style={styles.date}>{LONG_DATE_FORMATTER.format(new Date())}</Text>
          <Text accessibilityRole="header" style={styles.headline}>
            {greetingForHour(new Date().getHours())},{'\n'}let’s grow together.
          </Text>
          <Text style={styles.subheadline}>
            Find people who make showing up feel a little easier.
          </Text>
        </View>

        <MotionPressable
          accessibilityLabel="Search communities and topics"
          onPress={() => openDiscover()}
          style={styles.searchPrompt}
        >
          <AppSymbol color={colors.inkMuted} name="search" size={19} />
          <Text style={styles.searchPlaceholder}>Search topics or communities</Text>
          <AppSymbol color={colors.inkSubtle} name="arrowRight" size={17} />
        </MotionPressable>

        <View
          accessibilityLabel={`Featured community: ${featuredCommunity.name}`}
          style={styles.feature}
        >
          <View accessible={false} style={styles.artRingOuter} />
          <View accessible={false} style={styles.artRingInner} />
          <View style={styles.featureTopline}>
            <View style={styles.featureLabel}>
              <AppSymbol color={colors.highlight} name="sparkle" size={14} />
              <Text style={styles.featureEyebrow}>CIRCLE OF THE WEEK</Text>
            </View>
            <Text style={styles.featureCount}>0{joinedCommunities.length + 1}</Text>
          </View>

          <Text style={styles.featureTitle}>Big goals feel{'\n'}lighter together.</Text>
          <Text style={styles.featureCopy}>
            Meet {featuredCommunity.name} — a focused space to keep your momentum.
          </Text>

          <MotionPressable
            accessibilityLabel={`Explore ${featuredCommunity.topic} communities`}
            onPress={() => openDiscover(featuredCommunity.topic)}
            style={styles.featureAction}
          >
            <Text style={styles.featureActionText}>Find your circle</Text>
            <AppSymbol color={colors.highlightInk} name="arrowRight" size={17} />
          </MotionPressable>
        </View>

        <View style={styles.sectionHeading}>
          <View>
            <Text accessibilityRole="header" style={styles.sectionTitle}>
              Your circles
            </Text>
            <Text style={styles.sectionSubtitle}>Good things grow together.</Text>
          </View>
          <MotionPressable
            accessibilityLabel="Browse all communities"
            onPress={() => openDiscover()}
            style={styles.seeAll}
          >
            <Text style={styles.seeAllText}>See all</Text>
            <AppSymbol color={colors.accent} name="arrowRight" size={15} />
          </MotionPressable>
        </View>
      </View>
    ),
    [colors, openDiscover, styles],
  );

  const listFooter = useMemo(
    () => (
      <View style={styles.footer}>
        <View style={styles.footerMark}>
          <AppSymbol color={colors.accent} name="people" size={18} />
        </View>
        <Text style={styles.footerText}>There’s room for one more good idea.</Text>
        <MotionPressable
          accessibilityLabel="Explore more communities"
          onPress={() => openDiscover()}
          style={styles.footerAction}
        >
          <Text style={styles.footerActionText}>Explore communities</Text>
        </MotionPressable>
      </View>
    ),
    [colors, openDiscover, styles],
  );

  return (
    <View style={styles.screen}>
      <FlatList
        ItemSeparatorComponent={separator}
        ListFooterComponent={listFooter}
        ListHeaderComponent={listHeader}
        contentContainerStyle={styles.content}
        contentInsetAdjustmentBehavior="automatic"
        data={joinedCommunities}
        keyExtractor={(item) => item.id}
        renderItem={renderCommunity}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
}

function makeStyles(colors: ReturnType<typeof useAppTheme>) {
  return StyleSheet.create({
    screen: {
      flex: 1,
      width: '100%',
      minWidth: 0,
      backgroundColor: colors.canvas,
    },
    content: {
      width: '100%',
      maxWidth: layout.readingWidth,
      alignSelf: 'center',
      paddingHorizontal: spacing.lg,
      paddingTop: spacing.md,
      paddingBottom: spacing.xxl,
    },
    headerContent: {
      width: '100%',
      gap: spacing.lg,
    },
    intro: {
      gap: spacing.xs,
    },
    eyebrowRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.xs,
      marginBottom: spacing.xxs,
    },
    eyebrowDot: {
      width: 8,
      height: 8,
      borderRadius: 4,
      backgroundColor: colors.accent,
    },
    eyebrow: {
      color: colors.accent,
      fontSize: typeScale.caption,
      fontWeight: '700',
      letterSpacing: 1.1,
    },
    date: {
      color: colors.inkSubtle,
      fontSize: typeScale.footnote,
      marginBottom: spacing.xxs,
    },
    headline: {
      color: colors.ink,
      fontSize: typeScale.display,
      lineHeight: 42,
      fontWeight: '700',
      letterSpacing: -1.35,
    },
    subheadline: {
      color: colors.inkMuted,
      fontSize: typeScale.body,
      lineHeight: 22,
      maxWidth: 320,
      marginTop: spacing.xxs,
    },
    searchPrompt: {
      width: '100%',
      alignSelf: 'stretch',
      minHeight: 58,
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.sm,
      paddingHorizontal: spacing.md,
      backgroundColor: colors.surface,
      borderRadius: radius.md,
      borderCurve: 'continuous',
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.hairline,
    },
    searchPlaceholder: {
      flex: 1,
      color: colors.inkMuted,
      fontSize: typeScale.body,
    },
    feature: {
      position: 'relative',
      overflow: 'hidden',
      width: '100%',
      minHeight: 258,
      padding: spacing.lg,
      justifyContent: 'space-between',
      gap: spacing.md,
      backgroundColor: colors.hero,
      borderRadius: radius.xl,
      borderCurve: 'continuous',
    },
    artRingOuter: {
      position: 'absolute',
      width: 205,
      height: 205,
      right: -92,
      top: 34,
      borderRadius: 110,
      borderWidth: 1,
      borderColor: colors.heroOutline,
    },
    artRingInner: {
      position: 'absolute',
      width: 143,
      height: 143,
      right: -61,
      top: 65,
      borderRadius: 80,
      borderWidth: 1,
      borderColor: colors.heroAccentOutline,
    },
    featureTopline: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: spacing.sm,
    },
    featureLabel: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.xs,
    },
    featureEyebrow: {
      color: colors.heroMuted,
      fontSize: typeScale.caption,
      fontWeight: '700',
      letterSpacing: 1,
    },
    featureCount: {
      color: colors.heroMuted,
      fontSize: typeScale.caption,
      fontVariant: ['tabular-nums'],
      fontWeight: '600',
    },
    featureTitle: {
      color: colors.heroInk,
      fontSize: typeScale.title + 4,
      lineHeight: 33,
      fontWeight: '700',
      letterSpacing: -0.7,
      marginTop: spacing.xs,
    },
    featureCopy: {
      maxWidth: 290,
      color: colors.heroMuted,
      fontSize: typeScale.footnote,
      lineHeight: 19,
    },
    featureAction: {
      alignSelf: 'flex-start',
      minHeight: 46,
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.sm,
      paddingHorizontal: spacing.md,
      backgroundColor: colors.highlight,
      borderRadius: radius.full,
      borderCurve: 'continuous',
    },
    featureActionText: {
      color: colors.highlightInk,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
    sectionHeading: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: spacing.md,
      marginTop: spacing.xs,
      marginBottom: spacing.xs,
    },
    sectionTitle: {
      color: colors.ink,
      fontSize: typeScale.subheading,
      lineHeight: 24,
      fontWeight: '700',
      letterSpacing: -0.2,
    },
    sectionSubtitle: {
      color: colors.inkMuted,
      fontSize: typeScale.footnote,
      marginTop: spacing.xxs,
    },
    seeAll: {
      minHeight: 44,
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.xs,
      paddingHorizontal: spacing.xs,
    },
    seeAllText: {
      color: colors.accent,
      fontSize: typeScale.footnote,
      fontWeight: '600',
    },
    separator: {
      height: StyleSheet.hairlineWidth,
      backgroundColor: colors.hairline,
      marginLeft: 50 + spacing.md,
    },
    footer: {
      alignItems: 'center',
      gap: spacing.sm,
      paddingTop: spacing.xl,
      paddingBottom: spacing.md,
    },
    footerMark: {
      width: 42,
      height: 42,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors.accentSoft,
      borderRadius: radius.full,
    },
    footerText: {
      color: colors.inkMuted,
      fontSize: typeScale.footnote,
      textAlign: 'center',
    },
    footerAction: {
      minHeight: 44,
      justifyContent: 'center',
      paddingHorizontal: spacing.md,
    },
    footerActionText: {
      color: colors.accent,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
  });
}
