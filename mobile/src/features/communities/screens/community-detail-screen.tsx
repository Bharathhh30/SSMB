import { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import * as Linking from 'expo-linking';

import { AppSymbol } from '@/components/app-symbol';
import { MotionPressable } from '@/components/motion-pressable';
import { toCommunityCard } from '@/features/communities/data/communities';
import { useCommunityDetail } from '@/features/communities/hooks/use-community-detail';
import { layout, radius, spacing, typeScale, useAppTheme } from '@/theme';

export default function CommunityDetailScreen() {
  const colors = useAppTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const router = useRouter();
  const { slug } = useLocalSearchParams<{ slug?: string }>();
  const communityQuery = useCommunityDetail(slug ?? '');
  const [isSharing, setIsSharing] = useState(false);
  const community = communityQuery.community
    ? toCommunityCard(communityQuery.community)
    : null;
  const expiresAt = communityQuery.community?.expires_at;
  const tone = community ? colors.community[community.tone] : null;
  const isNotFound = communityQuery.error?.status === 404;

  async function sharePreview() {
    const apiCommunity = communityQuery.community;
    if (!apiCommunity || isSharing) {
      return;
    }

    setIsSharing(true);
    try {
      // Community names come from the API. Keep shared text on one predictable line.
      const safeName =
        apiCommunity.name
          .replace(/[\u0000-\u001f\u007f]+/g, ' ')
          .replace(/\s+/g, ' ')
          .trim()
          .slice(0, 120) || 'this community';
      const slugPlaceholder = 'community-preview-slug';
      const previewUrl = Linking.createURL(
        `communities/${slugPlaceholder}`,
      ).replace(slugPlaceholder, encodeURIComponent(apiCommunity.slug));

      await Share.share({
        title: `Share ${safeName}`,
        message: `Take a look at ${safeName} on Community:\n${previewUrl}`,
      });
    } catch {
      Alert.alert('Unable to share', 'Please try again in a moment.');
    } finally {
      setIsSharing(false);
    }
  }

  return (
    <View style={styles.screen}>
      <Stack.Screen
        options={{
          headerShown: true,
          title: community?.name ?? 'Community preview',
          headerBackTitle: 'Discover',
          headerShadowVisible: false,
          headerStyle: { backgroundColor: colors.canvas },
          headerTintColor: colors.accent,
          headerTitleStyle: { color: colors.ink },
        }}
      />

      {communityQuery.status === 'loading' ? (
        <View style={styles.statePanel}>
          <ActivityIndicator color={colors.accent} />
          <Text style={styles.stateCopy}>Opening this circle…</Text>
        </View>
      ) : communityQuery.status === 'error' ? (
        <View style={styles.statePanel}>
          <View style={styles.stateIcon}>
            <AppSymbol
              color={colors.accent}
              name={isNotFound ? 'people' : 'search'}
              size={22}
            />
          </View>
          <Text accessibilityRole="header" style={styles.stateTitle}>
            {isNotFound ? 'This circle isn’t available' : 'Can’t open this circle'}
          </Text>
          <Text style={styles.stateCopy}>
            {isNotFound
              ? 'It may be invite-only, expired, or no longer available.'
              : communityQuery.error?.message}
          </Text>
          {!isNotFound ? (
            <MotionPressable
              accessibilityLabel="Retry opening this community"
              onPress={communityQuery.retry}
              style={styles.primaryAction}
            >
              <Text style={styles.primaryActionText}>Try again</Text>
            </MotionPressable>
          ) : null}
          <MotionPressable
            accessibilityLabel="Back to Discover"
            onPress={() => router.replace('/discover')}
            style={styles.secondaryAction}
          >
            <Text style={styles.secondaryActionText}>Back to Discover</Text>
          </MotionPressable>
        </View>
      ) : community && tone ? (
        <ScrollView
          contentContainerStyle={styles.content}
          contentInsetAdjustmentBehavior="automatic"
          showsVerticalScrollIndicator={false}
        >
          <View style={[styles.hero, { backgroundColor: colors.hero }]}>
            <View accessible={false} style={styles.heroRingOuter} />
            <View accessible={false} style={styles.heroRingInner} />
            <View style={styles.heroTopline}>
              <View style={styles.previewLabel}>
                <AppSymbol color={colors.highlight} name="sparkle" size={14} />
                <Text style={styles.previewLabelText}>PUBLIC PREVIEW</Text>
              </View>
              <View style={[styles.monogram, { backgroundColor: tone.background }]}>
                <Text style={[styles.monogramText, { color: tone.foreground }]}>
                  {community.monogram}
                </Text>
              </View>
            </View>

            <Text accessibilityRole="header" style={styles.title}>
              {community.name}
            </Text>
            <View style={styles.metaRow}>
              <Text style={styles.topic}>{community.topic}</Text>
              <View style={styles.metaDivider} />
              <Text style={styles.access}>{community.access}</Text>
            </View>
          </View>

          <MotionPressable
            accessibilityLabel={`Share public preview of ${community.name}`}
            accessibilityState={{ busy: isSharing }}
            disabled={isSharing}
            onPress={sharePreview}
            style={[styles.shareAction, isSharing && styles.shareActionDisabled]}
            testID="share-community-preview"
          >
            <AppSymbol color={colors.accentInk} name="share" size={18} />
            <Text style={styles.shareActionText}>
              {isSharing ? 'Preparing share…' : 'Share public preview'}
            </Text>
          </MotionPressable>

          <View style={styles.section}>
            <Text accessibilityRole="header" style={styles.sectionTitle}>
              About this circle
            </Text>
            <Text style={styles.description}>{community.description}</Text>
          </View>

          <View style={styles.accessNote}>
            <View style={styles.accessNoteIcon}>
              <AppSymbol color={colors.accent} name="people" size={18} />
            </View>
            <View style={styles.accessNoteCopy}>
              <Text style={styles.accessNoteTitle}>A place to learn together</Text>
              <Text style={styles.accessNoteBody}>
                This is a public preview. Joining will be available after account access is set up.
              </Text>
            </View>
          </View>

          {expiresAt ? (
            <Text style={styles.expiryNote}>
              This community is available until{' '}
              {new Date(expiresAt).toLocaleDateString()}.
            </Text>
          ) : null}
        </ScrollView>
      ) : null}
    </View>
  );
}

function makeStyles(colors: ReturnType<typeof useAppTheme>) {
  return StyleSheet.create({
    screen: {
      flex: 1,
      backgroundColor: colors.canvas,
    },
    content: {
      width: '100%',
      maxWidth: layout.readingWidth,
      alignSelf: 'center',
      gap: spacing.xl,
      paddingHorizontal: spacing.lg,
      paddingTop: spacing.lg,
      paddingBottom: spacing.xxxl,
    },
    hero: {
      position: 'relative',
      overflow: 'hidden',
      minHeight: 250,
      justifyContent: 'space-between',
      gap: spacing.lg,
      padding: spacing.lg,
      borderRadius: radius.xl,
      borderCurve: 'continuous',
    },
    heroRingOuter: {
      position: 'absolute',
      width: 220,
      height: 220,
      right: -92,
      top: 54,
      borderWidth: 1,
      borderColor: colors.heroOutline,
      borderRadius: 120,
    },
    heroRingInner: {
      position: 'absolute',
      width: 150,
      height: 150,
      right: -58,
      top: 89,
      borderWidth: 1,
      borderColor: colors.heroAccentOutline,
      borderRadius: 90,
    },
    shareAction: {
      minHeight: 48,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: spacing.sm,
      backgroundColor: colors.accentSoft,
      borderRadius: radius.full,
      borderCurve: 'continuous',
    },
    shareActionDisabled: {
      opacity: 0.65,
    },
    shareActionText: {
      color: colors.accentInk,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
    heroTopline: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: spacing.md,
    },
    previewLabel: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.xs,
    },
    previewLabelText: {
      color: colors.heroMuted,
      fontSize: typeScale.caption,
      fontWeight: '700',
      letterSpacing: 1,
    },
    monogram: {
      width: 48,
      height: 48,
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: 16,
      borderCurve: 'continuous',
    },
    monogramText: {
      fontSize: typeScale.body,
      fontWeight: '700',
    },
    title: {
      maxWidth: 400,
      color: colors.heroInk,
      fontSize: typeScale.display,
      lineHeight: 42,
      fontWeight: '700',
      letterSpacing: -1,
    },
    metaRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.sm,
    },
    topic: {
      color: colors.heroMuted,
      fontSize: typeScale.footnote,
      fontWeight: '600',
    },
    metaDivider: {
      width: 4,
      height: 4,
      borderRadius: 2,
      backgroundColor: colors.heroMuted,
    },
    access: {
      color: colors.highlight,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
    section: {
      gap: spacing.sm,
    },
    sectionTitle: {
      color: colors.ink,
      fontSize: typeScale.subheading,
      lineHeight: 24,
      fontWeight: '700',
    },
    description: {
      color: colors.inkMuted,
      fontSize: typeScale.body,
      lineHeight: 24,
    },
    accessNote: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      gap: spacing.md,
      padding: spacing.md,
      backgroundColor: colors.surface,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.hairline,
      borderRadius: radius.lg,
      borderCurve: 'continuous',
    },
    accessNoteIcon: {
      width: 40,
      height: 40,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors.accentSoft,
      borderRadius: radius.full,
    },
    accessNoteCopy: {
      flex: 1,
      gap: spacing.xxs,
      paddingTop: spacing.xxs,
    },
    accessNoteTitle: {
      color: colors.ink,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
    accessNoteBody: {
      color: colors.inkMuted,
      fontSize: typeScale.caption,
      lineHeight: 18,
    },
    expiryNote: {
      color: colors.inkSubtle,
      fontSize: typeScale.caption,
      textAlign: 'center',
    },
    statePanel: {
      flex: 1,
      alignItems: 'center',
      justifyContent: 'center',
      gap: spacing.md,
      paddingHorizontal: spacing.xl,
      paddingVertical: spacing.xxxl,
    },
    stateIcon: {
      width: 56,
      height: 56,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors.accentSoft,
      borderRadius: radius.full,
    },
    stateTitle: {
      color: colors.ink,
      fontSize: typeScale.subheading,
      fontWeight: '700',
      textAlign: 'center',
    },
    stateCopy: {
      maxWidth: 340,
      color: colors.inkMuted,
      fontSize: typeScale.body,
      lineHeight: 22,
      textAlign: 'center',
    },
    primaryAction: {
      minHeight: 46,
      justifyContent: 'center',
      paddingHorizontal: spacing.lg,
      backgroundColor: colors.accent,
      borderRadius: radius.full,
      borderCurve: 'continuous',
    },
    primaryActionText: {
      color: colors.heroInk,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
    secondaryAction: {
      minHeight: 44,
      justifyContent: 'center',
      paddingHorizontal: spacing.md,
    },
    secondaryActionText: {
      color: colors.accent,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
  });
}
