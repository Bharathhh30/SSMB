import { useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import Animated, {
  Easing,
  FadeIn,
  FadeInDown,
  useReducedMotion,
} from 'react-native-reanimated';

import { AppSymbol } from '@/components/app-symbol';
import { MotionPressable } from '@/components/motion-pressable';
import {
  type ProfileDraft,
  toggleProfileInterest,
  validateProfileDraft,
} from '@/features/auth/profile-draft';
import { layout, motion, radius, spacing, typeScale, useAppTheme } from '@/theme';

const sampleInterests = [
  'Exam prep',
  'Technology',
  'Languages',
  'Creative projects',
  'Career growth',
  'Reading',
  'Science',
  'Design',
] as const;

const previewEase = Easing.bezier(0.23, 1, 0.32, 1);
const previewEntering = FadeInDown.withInitialValues({
  opacity: 0,
  transform: [{ translateY: motion.contentEntranceOffset }],
})
  .duration(motion.contentEntranceDuration)
  .easing(previewEase);
const reducedPreviewEntering = FadeIn.duration(
  motion.reducedContentEntranceDuration,
).easing(previewEase);

const initialDraft: ProfileDraft = {
  displayName: '',
  interests: [],
};

export function ProfilePreviewScreen() {
  const colors = useAppTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const router = useRouter();
  const reduceMotion = useReducedMotion();
  const [draft, setDraft] = useState<ProfileDraft>(initialDraft);
  const [nameError, setNameError] = useState<string>();
  const [showPreview, setShowPreview] = useState(false);

  function updateName(displayName: string) {
    setDraft((current) => ({ ...current, displayName }));
    setNameError(undefined);
    setShowPreview(false);
  }

  function toggleInterest(interest: string) {
    setDraft((current) => ({
      ...current,
      interests: toggleProfileInterest(current.interests, interest),
    }));
    setShowPreview(false);
  }

  function previewProfile() {
    const error = validateProfileDraft(draft);
    setNameError(error);
    setShowPreview(!error);
  }

  const displayName = draft.displayName.trim();
  const monogram = displayName.slice(0, 1).toLocaleUpperCase();

  return (
    <ScrollView
      contentContainerStyle={styles.content}
      contentInsetAdjustmentBehavior="automatic"
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.intro}>
        <View style={styles.eyebrowRow}>
          <AppSymbol color={colors.accent} name="sparkle" size={15} />
          <Text style={styles.eyebrow}>A SPACE THAT FEELS LIKE YOU</Text>
        </View>
        <Text accessibilityRole="header" style={styles.title}>
          Set up your profile.
        </Text>
        <Text style={styles.description}>
          Add a name and choose interests to see a local profile preview. Nothing here is saved or
          shared.
        </Text>
      </View>

      <View style={styles.form}>
        <View style={styles.field}>
          <Text style={styles.label}>Display name</Text>
          <TextInput
            accessibilityHint={nameError}
            accessibilityLabel="Profile display name"
            autoComplete="name"
            autoCorrect={false}
            onChangeText={updateName}
            placeholder="Your name"
            placeholderTextColor={colors.inkSubtle}
            returnKeyType="done"
            selectionColor={colors.accent}
            style={[styles.input, nameError ? styles.inputError : undefined]}
            textContentType="name"
            value={draft.displayName}
          />
          {nameError ? (
            <Text accessibilityLiveRegion="polite" style={styles.fieldError}>
              {nameError}
            </Text>
          ) : null}
        </View>

        <View style={styles.interestSection}>
          <View style={styles.interestHeading}>
            <Text style={styles.label}>What are you into?</Text>
            <Text style={styles.optionalLabel}>Optional</Text>
          </View>
          <Text style={styles.helper}>
            Pick a few things you’d like to learn or explore with others.
          </Text>

          <View style={styles.interestList}>
            {sampleInterests.map((interest) => {
              const selected = draft.interests.includes(interest);

              return (
                <MotionPressable
                  accessibilityLabel={interest}
                  accessibilityState={{ selected }}
                  key={interest}
                  onPress={() => toggleInterest(interest)}
                  style={[
                    styles.interestChip,
                    selected ? styles.interestChipSelected : undefined,
                  ]}
                >
                  {selected ? (
                    <AppSymbol color={colors.accentInk} name="check" size={13} />
                  ) : null}
                  <Text
                    style={[
                      styles.interestChipText,
                      selected ? styles.interestChipTextSelected : undefined,
                    ]}
                  >
                    {interest}
                  </Text>
                </MotionPressable>
              );
            })}
          </View>
          <Text style={styles.sampleNote}>
            These are sample interests for the prototype; the final list is still to be decided.
          </Text>
        </View>

        <MotionPressable
          accessibilityLabel="Preview profile draft"
          onPress={previewProfile}
          style={styles.primaryAction}
        >
          <Text style={styles.primaryActionText}>Preview profile</Text>
          <AppSymbol color={colors.highlightInk} name="arrowRight" size={17} />
        </MotionPressable>
      </View>

      {showPreview ? (
        <Animated.View
          entering={reduceMotion ? reducedPreviewEntering : previewEntering}
          style={styles.previewSection}
        >
          <Text accessibilityRole="header" style={styles.previewHeading}>
            Your profile draft
          </Text>
          <View style={styles.previewCard}>
            <View style={styles.previewIdentity}>
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>{monogram}</Text>
              </View>
              <View style={styles.previewNameBlock}>
                <Text style={styles.previewName}>{displayName}</Text>
                <Text style={styles.previewCaption}>Profile preview</Text>
              </View>
            </View>

            <View style={styles.previewDivider} />

            <Text style={styles.previewInterestHeading}>Interests</Text>
            {draft.interests.length > 0 ? (
              <View style={styles.previewInterests}>
                {draft.interests.map((interest) => (
                  <View key={interest} style={styles.previewInterest}>
                    <Text style={styles.previewInterestText}>{interest}</Text>
                  </View>
                ))}
              </View>
            ) : (
              <Text style={styles.previewEmpty}>No interests selected yet.</Text>
            )}
          </View>
          <Text accessibilityLiveRegion="polite" style={styles.localOnlyNote}>
            This draft exists only in this screen’s memory. It is not an account profile.
          </Text>
        </Animated.View>
      ) : null}

      <MotionPressable
        accessibilityLabel="Back to account welcome"
        onPress={() => router.replace('/account')}
        style={styles.backAction}
      >
        <Text style={styles.backActionText}>Back to account options</Text>
      </MotionPressable>
    </ScrollView>
  );
}

function makeStyles(colors: ReturnType<typeof useAppTheme>) {
  return StyleSheet.create({
    content: {
      width: '100%',
      maxWidth: layout.readingWidth,
      alignSelf: 'center',
      flexGrow: 1,
      gap: spacing.xl,
      paddingHorizontal: spacing.lg,
      paddingTop: spacing.xl,
      paddingBottom: spacing.xxxl,
    },
    intro: {
      gap: spacing.sm,
    },
    eyebrowRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.xs,
    },
    eyebrow: {
      color: colors.accent,
      fontSize: typeScale.caption,
      fontWeight: '700',
      letterSpacing: 1.1,
    },
    title: {
      color: colors.ink,
      fontSize: typeScale.title,
      lineHeight: 32,
      fontWeight: '700',
      letterSpacing: -0.5,
    },
    description: {
      color: colors.inkMuted,
      fontSize: typeScale.footnote,
      lineHeight: 21,
    },
    form: {
      gap: spacing.xl,
    },
    field: {
      gap: spacing.xs,
    },
    label: {
      color: colors.ink,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
    input: {
      minHeight: 54,
      paddingHorizontal: spacing.md,
      color: colors.ink,
      fontSize: typeScale.body,
      backgroundColor: colors.surface,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.hairline,
      borderRadius: radius.md,
      borderCurve: 'continuous',
    },
    inputError: {
      borderColor: colors.accent,
    },
    fieldError: {
      color: colors.accent,
      fontSize: typeScale.caption,
      lineHeight: 18,
    },
    interestSection: {
      gap: spacing.sm,
    },
    interestHeading: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: spacing.sm,
    },
    optionalLabel: {
      color: colors.inkSubtle,
      fontSize: typeScale.caption,
    },
    helper: {
      color: colors.inkMuted,
      fontSize: typeScale.caption,
      lineHeight: 18,
    },
    interestList: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: spacing.xs,
    },
    interestChip: {
      minHeight: 44,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: spacing.xxs,
      paddingHorizontal: spacing.md,
      backgroundColor: colors.surface,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.hairline,
      borderRadius: radius.full,
      borderCurve: 'continuous',
    },
    interestChipSelected: {
      backgroundColor: colors.accentSoft,
      borderColor: colors.accentSoft,
    },
    interestChipText: {
      color: colors.inkMuted,
      fontSize: typeScale.footnote,
      fontWeight: '600',
    },
    interestChipTextSelected: {
      color: colors.accentInk,
    },
    sampleNote: {
      color: colors.inkSubtle,
      fontSize: typeScale.caption,
      lineHeight: 17,
    },
    primaryAction: {
      minHeight: 54,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: spacing.sm,
      backgroundColor: colors.highlight,
      borderRadius: radius.full,
      borderCurve: 'continuous',
    },
    primaryActionText: {
      color: colors.highlightInk,
      fontSize: typeScale.body,
      fontWeight: '700',
    },
    previewSection: {
      gap: spacing.md,
    },
    previewHeading: {
      color: colors.ink,
      fontSize: typeScale.subheading,
      fontWeight: '700',
    },
    previewCard: {
      gap: spacing.md,
      padding: spacing.lg,
      backgroundColor: colors.surface,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.hairline,
      borderRadius: radius.xl,
      borderCurve: 'continuous',
    },
    previewIdentity: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: spacing.md,
    },
    avatar: {
      width: 54,
      height: 54,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors.accentSoft,
      borderRadius: radius.full,
    },
    avatarText: {
      color: colors.accentInk,
      fontSize: typeScale.title,
      fontWeight: '700',
    },
    previewNameBlock: {
      flex: 1,
      gap: spacing.xxs,
    },
    previewName: {
      color: colors.ink,
      fontSize: typeScale.subheading,
      fontWeight: '700',
    },
    previewCaption: {
      color: colors.inkSubtle,
      fontSize: typeScale.caption,
    },
    previewDivider: {
      height: StyleSheet.hairlineWidth,
      backgroundColor: colors.hairline,
    },
    previewInterestHeading: {
      color: colors.ink,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
    previewInterests: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: spacing.xs,
    },
    previewInterest: {
      minHeight: 32,
      justifyContent: 'center',
      paddingHorizontal: spacing.sm,
      backgroundColor: colors.surfaceMuted,
      borderRadius: radius.full,
    },
    previewInterestText: {
      color: colors.inkMuted,
      fontSize: typeScale.caption,
      fontWeight: '600',
    },
    previewEmpty: {
      color: colors.inkMuted,
      fontSize: typeScale.footnote,
    },
    localOnlyNote: {
      color: colors.inkSubtle,
      fontSize: typeScale.caption,
      lineHeight: 18,
      textAlign: 'center',
    },
    backAction: {
      minHeight: 44,
      alignSelf: 'center',
      justifyContent: 'center',
      paddingHorizontal: spacing.md,
    },
    backActionText: {
      color: colors.accent,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
  });
}
