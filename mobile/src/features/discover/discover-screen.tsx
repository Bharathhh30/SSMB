import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { AppSymbol } from '@/components/app-symbol';
import { MotionPressable } from '@/components/motion-pressable';
import { CommunityRow } from '@/features/communities/components/community-row';
import {
  communityTopics,
  toCommunityCard,
  type Community,
  type CommunityTopic,
} from '@/features/communities/data/communities';
import { useDiscoverCommunities } from '@/features/communities/hooks/use-discover-communities';
import { layout, radius, spacing, typeScale, useAppTheme } from '@/theme';

const allTopics = ['All', ...communityTopics] as const;
type TopicFilter = (typeof allTopics)[number];

function isCommunityTopic(value: unknown): value is CommunityTopic {
  return typeof value === 'string' && communityTopics.some((topic) => topic === value);
}

export default function DiscoverScreen() {
  const colors = useAppTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const { topic: initialTopic } = useLocalSearchParams<{ topic?: string }>();
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [selectedTopic, setSelectedTopic] = useState<TopicFilter>(
    isCommunityTopic(initialTopic) ? initialTopic : 'All',
  );
  const communityQuery = useDiscoverCommunities(
    query,
    selectedTopic === 'All' ? undefined : selectedTopic,
  );
  const displayedCommunities = useMemo(
    () => communityQuery.items.map(toCommunityCard),
    [communityQuery.items],
  );
  const openCommunity = useCallback(
    (community: Community) => {
      if (community.slug) {
        router.push({
          pathname: '/communities/[slug]',
          params: { slug: community.slug },
        });
      }
    },
    [router],
  );
  const renderCommunity = useCallback(
    ({ item }: { item: Community }) => (
      <CommunityRow community={item} onPress={() => openCommunity(item)} />
    ),
    [openCommunity],
  );

  useEffect(() => {
    if (isCommunityTopic(initialTopic)) {
      setSelectedTopic(initialTopic);
    }
  }, [initialTopic]);

  const clearFilters = () => {
    setQuery('');
    setSelectedTopic('All');
  };

  const listHeader = useMemo(
    () => (
      <View style={styles.headerContent}>
        <View style={styles.intro}>
          <Text style={styles.eyebrow}>GOOD COMPANY STARTS HERE</Text>
          <Text accessibilityRole="header" style={styles.headline}>
            Find your circle.
          </Text>
          <Text style={styles.subtitle}>
            Explore spaces built around what you’re learning and what you love.
          </Text>
        </View>

        <View style={styles.searchField}>
          <AppSymbol color={colors.inkMuted} name="search" size={19} />
          <TextInput
            accessibilityLabel="Search communities"
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={setQuery}
            placeholder="Try “GATE” or “design”"
            placeholderTextColor={colors.inkSubtle}
            returnKeyType="search"
            style={styles.searchInput}
            value={query}
          />
          {query.length > 0 ? (
            <MotionPressable
              accessibilityLabel="Clear search"
              onPress={() => setQuery('')}
              style={styles.clearSearch}
            >
              <AppSymbol color={colors.inkMuted} name="close" size={17} />
            </MotionPressable>
          ) : null}
        </View>

        <ScrollView
          contentContainerStyle={styles.topicList}
          horizontal
          keyboardShouldPersistTaps="handled"
          showsHorizontalScrollIndicator={false}
        >
          {allTopics.map((topic) => {
            const selected = topic === selectedTopic;

            return (
              <MotionPressable
                accessibilityLabel={`${topic} communities`}
                accessibilityState={{ selected }}
                key={topic}
                onPress={() => setSelectedTopic(topic)}
                style={[
                  styles.topicChip,
                  selected ? styles.topicChipSelected : styles.topicChipUnselected,
                ]}
              >
                <Text style={[styles.topicText, selected && styles.topicTextSelected]}>
                  {topic}
                </Text>
              </MotionPressable>
            );
          })}
        </ScrollView>

        <View style={styles.resultsHeading}>
          <View>
            <Text style={styles.resultsTitle}>
              {selectedTopic === 'All' ? 'A few good places to begin' : selectedTopic}
            </Text>
            <Text style={styles.resultsSubtitle}>
              {communityQuery.status === 'loading'
                ? 'Finding circles…'
                : communityQuery.status === 'error'
                  ? 'Could not reach the community service'
                  : `${communityQuery.total} ${
                      communityQuery.total === 1 ? 'circle' : 'circles'
                    } to explore`}
            </Text>
          </View>
          <View style={styles.resultsIcon}>
            <AppSymbol color={colors.accent} name="people" size={18} />
          </View>
        </View>
      </View>
    ),
    [colors, communityQuery.status, communityQuery.total, query, selectedTopic, styles],
  );

  const hasFilters = query.trim().length > 0 || selectedTopic !== 'All';
  const emptyState =
    communityQuery.status === 'loading' ? (
      <View style={styles.statePanel}>
        <ActivityIndicator color={colors.accent} />
        <Text style={styles.stateMessage}>Finding good circles for you…</Text>
      </View>
    ) : communityQuery.status === 'error' ? (
      <View style={styles.statePanel}>
        <Text style={styles.emptyTitle}>Can’t load communities</Text>
        <Text style={styles.stateMessage}>{communityQuery.error?.message}</Text>
        <MotionPressable
          accessibilityLabel="Retry loading communities"
          onPress={communityQuery.retry}
          style={styles.retryButton}
        >
          <Text style={styles.retryText}>Try again</Text>
        </MotionPressable>
      </View>
    ) : displayedCommunities.length === 0 ? (
      <View style={styles.emptyState}>
        <View style={styles.emptyIcon}>
          <AppSymbol color={colors.accent} name="search" size={22} />
        </View>
        <Text style={styles.emptyTitle}>{hasFilters ? 'No circles found' : 'No circles yet'}</Text>
        <Text style={styles.emptyCopy}>
          {hasFilters
            ? 'Try another phrase or clear your filters.'
            : 'New communities will show up here when they’re ready.'}
        </Text>
        {hasFilters ? (
          <MotionPressable onPress={clearFilters} style={styles.clearFilters}>
            <Text style={styles.clearFiltersText}>Clear filters</Text>
          </MotionPressable>
        ) : null}
      </View>
    ) : null;

  const listFooter =
    communityQuery.hasNextPage || communityQuery.isLoadingMore ? (
      <View style={styles.loadMoreContainer}>
        {communityQuery.isLoadingMore ? (
          <View style={styles.loadingMoreRow}>
            <ActivityIndicator color={colors.accent} size="small" />
            <Text style={styles.stateMessage}>Loading more circles…</Text>
          </View>
        ) : communityQuery.loadingMoreError ? (
          <>
            <Text style={styles.stateMessage}>{communityQuery.loadingMoreError.message}</Text>
            <MotionPressable
              accessibilityLabel="Retry loading more communities"
              onPress={communityQuery.retryLoadingMore}
              style={styles.loadMoreButton}
            >
              <Text style={styles.retryText}>Retry</Text>
            </MotionPressable>
          </>
        ) : (
          <MotionPressable
            accessibilityLabel="Load more communities"
            onPress={() => void communityQuery.loadMore()}
            style={styles.loadMoreButton}
          >
            <Text style={styles.retryText}>Load more circles</Text>
          </MotionPressable>
        )}
      </View>
    ) : null;

  return (
    <View style={styles.screen}>
      <FlatList
        ItemSeparatorComponent={() => <View style={styles.separator} />}
        ListEmptyComponent={emptyState}
        ListFooterComponent={listFooter}
        ListHeaderComponent={listHeader}
        contentContainerStyle={styles.content}
        contentInsetAdjustmentBehavior="automatic"
        data={displayedCommunities}
        keyboardShouldPersistTaps="handled"
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
      paddingTop: spacing.xl,
      paddingBottom: spacing.xxl,
      flexGrow: 1,
    },
    headerContent: {
      width: '100%',
      gap: spacing.lg,
      paddingBottom: spacing.sm,
    },
    intro: {
      gap: spacing.xs,
    },
    eyebrow: {
      color: colors.accent,
      fontSize: typeScale.caption,
      fontWeight: '700',
      letterSpacing: 1.05,
    },
    headline: {
      color: colors.ink,
      fontSize: typeScale.display,
      lineHeight: 43,
      fontWeight: '700',
      letterSpacing: -1.2,
      marginTop: spacing.xxs,
    },
    subtitle: {
      maxWidth: 340,
      color: colors.inkMuted,
      fontSize: typeScale.body,
      lineHeight: 22,
    },
    searchField: {
      minHeight: 56,
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.sm,
      paddingLeft: spacing.md,
      paddingRight: spacing.xs,
      backgroundColor: colors.surface,
      borderRadius: radius.md,
      borderCurve: 'continuous',
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.hairline,
    },
    searchInput: {
      minWidth: 0,
      flex: 1,
      minHeight: 52,
      color: colors.ink,
      fontSize: typeScale.body,
      paddingVertical: 0,
    },
    clearSearch: {
      width: 44,
      height: 44,
      alignItems: 'center',
      justifyContent: 'center',
    },
    topicList: {
      alignItems: 'center',
      gap: spacing.xs,
      paddingRight: spacing.md,
    },
    topicChip: {
      minHeight: 42,
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: spacing.md,
      borderRadius: radius.full,
      borderCurve: 'continuous',
    },
    topicChipSelected: {
      backgroundColor: colors.accent,
    },
    topicChipUnselected: {
      backgroundColor: colors.surface,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.hairline,
    },
    topicText: {
      color: colors.inkMuted,
      fontSize: typeScale.footnote,
      fontWeight: '600',
    },
    topicTextSelected: {
      color: colors.heroInk,
    },
    resultsHeading: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: spacing.md,
      marginTop: spacing.xs,
    },
    resultsTitle: {
      color: colors.ink,
      fontSize: typeScale.subheading,
      lineHeight: 24,
      fontWeight: '700',
      letterSpacing: -0.25,
    },
    resultsSubtitle: {
      color: colors.inkMuted,
      fontSize: typeScale.footnote,
      marginTop: spacing.xxs,
    },
    resultsIcon: {
      width: 40,
      height: 40,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors.accentSoft,
      borderRadius: radius.full,
    },
    separator: {
      height: StyleSheet.hairlineWidth,
      backgroundColor: colors.hairline,
      marginLeft: 50 + spacing.md,
    },
    emptyState: {
      flex: 1,
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: spacing.xl,
      paddingVertical: spacing.xxxl,
      gap: spacing.sm,
    },
    statePanel: {
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: spacing.xl,
      paddingVertical: spacing.xxxl,
      gap: spacing.md,
    },
    stateMessage: {
      color: colors.inkMuted,
      fontSize: typeScale.footnote,
      lineHeight: 20,
      textAlign: 'center',
    },
    retryButton: {
      minHeight: 44,
      justifyContent: 'center',
      paddingHorizontal: spacing.lg,
      backgroundColor: colors.accentSoft,
      borderRadius: radius.full,
      borderCurve: 'continuous',
    },
    retryText: {
      color: colors.accentInk,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
    loadMoreContainer: {
      alignItems: 'center',
      justifyContent: 'center',
      gap: spacing.sm,
      paddingTop: spacing.md,
      paddingBottom: spacing.xl,
    },
    loadingMoreRow: {
      minHeight: 44,
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.sm,
    },
    loadMoreButton: {
      minHeight: 44,
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: spacing.lg,
      backgroundColor: colors.accentSoft,
      borderRadius: radius.full,
      borderCurve: 'continuous',
    },
    emptyIcon: {
      width: 56,
      height: 56,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors.accentSoft,
      borderRadius: radius.full,
      marginBottom: spacing.xs,
    },
    emptyTitle: {
      color: colors.ink,
      fontSize: typeScale.subheading,
      fontWeight: '700',
    },
    emptyCopy: {
      color: colors.inkMuted,
      fontSize: typeScale.body,
      textAlign: 'center',
      lineHeight: 22,
    },
    clearFilters: {
      minHeight: 44,
      justifyContent: 'center',
      paddingHorizontal: spacing.md,
      marginTop: spacing.xs,
    },
    clearFiltersText: {
      color: colors.accent,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
  });
}
