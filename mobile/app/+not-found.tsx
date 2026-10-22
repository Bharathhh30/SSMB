import { useRouter } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { MotionPressable } from '@/components/motion-pressable';
import { radius, spacing, typeScale, useAppTheme } from '@/theme';

export default function NotFoundScreen() {
  const colors = useAppTheme();
  const router = useRouter();

  return (
    <View style={[styles.container, { backgroundColor: colors.canvas }]}>
      <Text style={[styles.eyebrow, { color: colors.accent }]}>A LITTLE OFF THE MAP</Text>
      <Text style={[styles.title, { color: colors.ink }]}>This circle isn’t here.</Text>
      <Text style={[styles.copy, { color: colors.inkMuted }]}>
        The page may have moved. Let’s get you back to your community space.
      </Text>
      <MotionPressable
        accessibilityLabel="Back to home"
        onPress={() => router.replace('/')}
        style={[styles.action, { backgroundColor: colors.accent }]}
      >
        <Text style={[styles.actionText, { color: colors.heroInk }]}>Back to home</Text>
      </MotionPressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
    gap: spacing.md,
  },
  eyebrow: {
    fontSize: typeScale.caption,
    fontWeight: '700',
    letterSpacing: 1,
  },
  title: {
    fontSize: typeScale.title,
    fontWeight: '700',
    textAlign: 'center',
  },
  copy: {
    maxWidth: 320,
    fontSize: typeScale.body,
    lineHeight: 23,
    textAlign: 'center',
  },
  action: {
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
    borderRadius: radius.full,
    borderCurve: 'continuous',
    marginTop: spacing.xs,
  },
  actionText: {
    fontSize: typeScale.footnote,
    fontWeight: '700',
  },
});
