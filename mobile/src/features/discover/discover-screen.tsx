import { useEffect, useMemo, useState } from 'react';
import {
  FlatList,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useLocalSearchParams } from 'expo-router';

import { AppSymbol } from '@/components/app-symbol';
import { MotionPressable } from '@/components/motion-pressable';
import { CommunityRow } from '@/features/communities/components/community-row';
import {
  communities,
  communityTopics,
  type CommunityTopic,
} from '@/features/communities/data/communities';
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
  const [query, setQuery] = useState('');
  const [selectedTopic, setSelectedTopic] = useState<TopicFilter>(
    isCommunityTopic(initialTopic) ? initialTopic : 'All',
  );

  useEffect(() => {
    if (isCommunityTopic(initialTopic)) {
      setSelectedTopic(initialTopic);
    }
  }, [initialTopic]);

  const filteredCommunities = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase();

    return communities.filter((community) => {
      const matchesTopic = selectedTopic === 'All' || community.topic === selectedTopic;
      const searchableText = [
        community.name,
        community.topic,
        community.description,
        ...community.tags,
      ]
        .join(' ')
        .toLocaleLowerCase();

      return matchesTopic && (!normalizedQuery || searchableText.includes(normalizedQuery));
    });
  }, [query, selectedTopic]);

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
              {filteredCommunities.length}{' '}
              {filteredCommunities.length === 1 ? 'circle' : 'circles'} to explore
            </Text>
          </View>
          <View style={styles.resultsIcon}>
            <AppSymbol color={colors.accent} name="people" size={18} />
          </View>
        </View>
      </View>
    ),
    [colors, filteredCommunities.length, query, selectedTopic, styles],
  );

  const emptyState = (
    <View style={styles.emptyState}>
      <View style={styles.emptyIcon}>
        <AppSymbol color={colors.accent} name="search" size={22} />
      </View>
      <Text style={styles.emptyTitle}>No circles found</Text>
      <Text style={styles.emptyCopy}>Try a different phrase or clear your filters.</Text>
      <MotionPressable onPress={clearFilters} style={styles.clearFilters}>
        <Text style={styles.clearFiltersText}>Clear filters</Text>
      </MotionPressable>
    </View>
  );

  return (
    <View style={styles.screen}>
      <FlatList
        ItemSeparatorComponent={() => <View style={styles.separator} />}
        ListEmptyComponent={emptyState}
        ListHeaderComponent={listHeader}
        contentContainerStyle={styles.content}
        contentInsetAdjustmentBehavior="automatic"
        data={filteredCommunities}
        keyboardShouldPersistTaps="handled"
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <CommunityRow community={item} />}
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
