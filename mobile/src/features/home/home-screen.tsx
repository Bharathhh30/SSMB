import { useCallback, useMemo } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';

import { AppSymbol } from '@/components/app-symbol';
import { ApiRequestReference } from '@/components/api-request-reference';
import { MotionPressable } from '@/components/motion-pressable';
import { useCommunityTopics } from '@/features/communities/hooks/use-community-topics';
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

const topicDescriptions: Record<string, string> = {
  'Exam prep': 'Study toward a test, certification, or personal milestone.',
  Technology: 'Explore tools, code, and technical ideas together.',
  Languages: 'Practice a language through shared goals and conversation.',
  Creative: 'Make room for ideas, craft, and thoughtful feedback.',
};

export default function HomeScreen() {
  const colors = useAppTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const router = useRouter();
  const topicsQuery = useCommunityTopics();

  const openDiscover = useCallback(
    (topic?: string) => {
      router.push(topic ? { pathname: '/discover', params: { topic } } : '/discover');
    },
    [router],
  );

  const renderTopic = useCallback(
    ({ item }: { item: string }) => (
      <MotionPressable
        accessibilityLabel={`Explore ${item} communities`}
        onPress={() => openDiscover(item)}
        style={styles.topicCard}
      >
        <View style={styles.topicCardTopline}>
          <View style={styles.topicMark}>
            <AppSymbol color={colors.accent} name="sparkle" size={16} />
          </View>
          <AppSymbol color={colors.inkSubtle} name="arrowRight" size={16} />
        </View>
        <Text style={styles.topicTitle}>{item}</Text>
        <Text numberOfLines={2} style={styles.topicDescription}>
          {topicDescriptions[item] ?? 'Find people and communities around this shared interest.'}
        </Text>
      </MotionPressable>
    ),
    [colors.accent, colors.inkSubtle, openDiscover, styles],
  );

  const topicRowSeparator = useCallback(
    () => <View style={styles.topicRowSeparator} />,
    [styles.topicRowSeparator],
  );

  const topicsEmptyState =
    topicsQuery.status === 'loading' ? (
      <View style={styles.topicState}>
        <ActivityIndicator color={colors.accent} />
        <Text style={styles.topicStateMessage}>Finding topics to explore…</Text>
      </View>
    ) : topicsQuery.status === 'error' ? (
      <View style={styles.topicState}>
        <Text style={styles.topicStateMessage}>Couldn’t load topics right now.</Text>
        <ApiRequestReference requestId={topicsQuery.error?.requestId} />
        <MotionPressable
          accessibilityLabel="Retry loading topics"
          onPress={topicsQuery.retry}
          style={styles.topicRetry}
        >
          <Text style={styles.topicRetryText}>Try again</Text>
        </MotionPressable>
      </View>
    ) : (
      <View style={styles.topicState}>
        <Text style={styles.topicStateMessage}>
          No topics have public communities yet. Try browsing all communities.
        </Text>
        <MotionPressable
          accessibilityLabel="Browse all communities"
          onPress={() => openDiscover()}
          style={styles.topicRetry}
        >
          <Text style={styles.topicRetryText}>Browse all</Text>
        </MotionPressable>
      </View>
    );

  const listHeader = useMemo(
    () => (
      <View style={styles.headerContent}>
        <View style={styles.intro}>
          <View style={styles.eyebrowRow}>
            <View style={styles.eyebrowDot} />
            <Text style={styles.eyebrow}>LEARN, MAKE, GROW TOGETHER</Text>
          </View>
          <View style={styles.dateRow}>
            <Text style={styles.date}>{LONG_DATE_FORMATTER.format(new Date())}</Text>
            <MotionPressable
              accessibilityLabel="Open account options"
              onPress={() => router.push('/account')}
              style={styles.accountAction}
            >
              <Text style={styles.accountActionText}>Get started</Text>
            </MotionPressable>
          </View>
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

        <View style={styles.feature}>
          <View accessible={false} style={styles.artRingOuter} />
          <View accessible={false} style={styles.artRingInner} />
          <View style={styles.featureTopline}>
            <View style={styles.featureLabel}>
              <AppSymbol color={colors.highlight} name="sparkle" size={14} />
              <Text style={styles.featureEyebrow}>A GOOD PLACE TO BEGIN</Text>
            </View>
          </View>

          <Text style={styles.featureTitle}>Big goals feel{'\n'}lighter together.</Text>
          <Text style={styles.featureCopy}>
            Find an open community around something you're learning, making, or simply curious
            about.
          </Text>

          <MotionPressable
            accessibilityLabel="Explore open communities"
            onPress={() => openDiscover()}
            style={styles.featureAction}
          >
            <Text style={styles.featureActionText}>Explore communities</Text>
            <AppSymbol color={colors.highlightInk} name="arrowRight" size={17} />
          </MotionPressable>
        </View>

        <View style={styles.sectionHeading}>
          <View>
            <Text accessibilityRole="header" style={styles.sectionTitle}>
              Explore by interest
            </Text>
            <Text style={styles.sectionSubtitle}>
              Pick a starting point and see what's out there.
            </Text>
          </View>
        </View>
      </View>
    ),
    [colors, openDiscover, router, styles],
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
        ItemSeparatorComponent={topicRowSeparator}
        ListEmptyComponent={topicsEmptyState}
        ListFooterComponent={listFooter}
        ListHeaderComponent={listHeader}
        columnWrapperStyle={styles.topicRow}
        contentContainerStyle={styles.content}
        contentInsetAdjustmentBehavior="automatic"
        data={topicsQuery.topics}
        keyExtractor={(topic) => topic}
        numColumns={2}
        renderItem={renderTopic}
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
    },
    dateRow: {
      minHeight: 44,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: spacing.sm,
    },
    accountAction: {
      minHeight: 44,
      justifyContent: 'center',
      paddingHorizontal: spacing.md,
      backgroundColor: colors.accentSoft,
      borderRadius: radius.full,
      borderCurve: 'continuous',
    },
    accountActionText: {
      color: colors.accentInk,
      fontSize: typeScale.footnote,
      fontWeight: '700',
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
    topicRow: {
      gap: spacing.sm,
    },
    topicRowSeparator: {
      height: spacing.sm,
    },
    topicCard: {
      flex: 1,
      minWidth: 0,
      minHeight: 142,
      justifyContent: 'space-between',
      gap: spacing.sm,
      padding: spacing.md,
      backgroundColor: colors.surface,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.hairline,
      borderRadius: radius.lg,
      borderCurve: 'continuous',
    },
    topicCardTopline: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
    topicMark: {
      width: 34,
      height: 34,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors.accentSoft,
      borderRadius: radius.full,
    },
    topicTitle: {
      color: colors.ink,
      fontSize: typeScale.body,
      fontWeight: '700',
    },
    topicDescription: {
      color: colors.inkMuted,
      fontSize: typeScale.caption,
      lineHeight: 18,
    },
    topicState: {
      alignItems: 'center',
      gap: spacing.sm,
      paddingHorizontal: spacing.md,
      paddingVertical: spacing.xl,
    },
    topicStateMessage: {
      color: colors.inkMuted,
      fontSize: typeScale.footnote,
      lineHeight: 20,
      textAlign: 'center',
    },
    topicRetry: {
      minHeight: 44,
      justifyContent: 'center',
      paddingHorizontal: spacing.md,
      backgroundColor: colors.accentSoft,
      borderRadius: radius.full,
      borderCurve: 'continuous',
    },
    topicRetryText: {
      color: colors.accentInk,
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
