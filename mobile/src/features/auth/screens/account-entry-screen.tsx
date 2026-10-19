import { useMemo } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';

import { AppSymbol } from '@/components/app-symbol';
import { MotionPressable } from '@/components/motion-pressable';
import { layout, radius, spacing, typeScale, useAppTheme } from '@/theme';

export function AccountEntryScreen() {
  const colors = useAppTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const router = useRouter();

  return (
    <ScrollView
      contentContainerStyle={styles.content}
      contentInsetAdjustmentBehavior="automatic"
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.brandMark}>
        <AppSymbol color={colors.highlight} name="people" size={27} />
      </View>

      <View style={styles.intro}>
        <Text style={styles.eyebrow}>YOUR NEXT CHAPTER, TOGETHER</Text>
        <Text accessibilityRole="header" style={styles.title}>
          Make space for{'\n'}good things.
        </Text>
        <Text style={styles.description}>
          Find your people, share what you’re learning, and make steady progress side by side.
        </Text>
      </View>

      <View style={styles.actions}>
        <MotionPressable
          accessibilityLabel="Create an account"
          onPress={() => router.push('/account/sign-up')}
          style={styles.primaryAction}
        >
          <Text style={styles.primaryActionText}>Create an account</Text>
          <AppSymbol color={colors.highlightInk} name="arrowRight" size={17} />
        </MotionPressable>

        <MotionPressable
          accessibilityLabel="Sign in to an existing account"
          onPress={() => router.push('/account/sign-in')}
          style={styles.secondaryAction}
        >
          <Text style={styles.secondaryActionText}>I already have an account</Text>
        </MotionPressable>
      </View>

      <View style={styles.prototypeNote}>
        <Text style={styles.prototypeTitle}>A local first look</Text>
        <Text style={styles.prototypeCopy}>
          These account screens are a visual prototype. No account is created, and sign-in is not
          connected yet.
        </Text>
      </View>

      <MotionPressable
        accessibilityLabel="Preview profile setup"
        onPress={() => router.push('/account/profile')}
        style={styles.profilePreviewAction}
      >
        <Text style={styles.profilePreviewActionText}>Explore profile setup</Text>
        <AppSymbol color={colors.accent} name="arrowRight" size={16} />
      </MotionPressable>

      <MotionPressable
        accessibilityLabel="Continue browsing as a guest"
        onPress={() => router.replace('/')}
        style={styles.guestAction}
      >
        <Text style={styles.guestActionText}>Keep exploring as a guest</Text>
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
      justifyContent: 'center',
      gap: spacing.xl,
      paddingHorizontal: spacing.lg,
      paddingTop: spacing.xl,
      paddingBottom: spacing.xxxl,
    },
    brandMark: {
      width: 58,
      height: 58,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors.hero,
      borderRadius: radius.lg,
      borderCurve: 'continuous',
    },
    intro: {
      gap: spacing.sm,
    },
    eyebrow: {
      color: colors.accent,
      fontSize: typeScale.caption,
      fontWeight: '700',
      letterSpacing: 1.1,
    },
    title: {
      color: colors.ink,
      fontSize: typeScale.display,
      lineHeight: 42,
      fontWeight: '700',
      letterSpacing: -1,
    },
    description: {
      maxWidth: 390,
      color: colors.inkMuted,
      fontSize: typeScale.body,
      lineHeight: 23,
    },
    actions: {
      gap: spacing.xs,
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
    secondaryAction: {
      minHeight: 50,
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: spacing.md,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.hairline,
      borderRadius: radius.full,
      borderCurve: 'continuous',
    },
    secondaryActionText: {
      color: colors.ink,
      fontSize: typeScale.footnote,
      fontWeight: '600',
    },
    prototypeNote: {
      gap: spacing.xxs,
      padding: spacing.md,
      backgroundColor: colors.surface,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: colors.hairline,
      borderRadius: radius.md,
      borderCurve: 'continuous',
    },
    prototypeTitle: {
      color: colors.ink,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
    prototypeCopy: {
      color: colors.inkMuted,
      fontSize: typeScale.caption,
      lineHeight: 18,
    },
    profilePreviewAction: {
      minHeight: 44,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      gap: spacing.xs,
      paddingHorizontal: spacing.md,
    },
    profilePreviewActionText: {
      color: colors.accent,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
    guestAction: {
      minHeight: 44,
      alignSelf: 'center',
      justifyContent: 'center',
      paddingHorizontal: spacing.md,
    },
    guestActionText: {
      color: colors.accent,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
  });
}
