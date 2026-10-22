import { useMemo, useRef, useState } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { usePathname, useRouter } from 'expo-router';

import { MotionPressable } from '@/components/motion-pressable';
import {
  type CredentialsDraft,
  type CredentialsErrors,
  type CredentialsMode,
  validateCredentials,
} from '@/features/auth/validation';
import { layout, radius, spacing, typeScale, useAppTheme } from '@/theme';

type FieldName = keyof CredentialsDraft;

const initialDraft: CredentialsDraft = {
  displayName: '',
  email: '',
  password: '',
};

export function CredentialsScreen() {
  const colors = useAppTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const pathname = usePathname();
  const router = useRouter();
  const mode: CredentialsMode = pathname.endsWith('/sign-up') ? 'sign-up' : 'sign-in';
  const [draft, setDraft] = useState<CredentialsDraft>(initialDraft);
  const [errors, setErrors] = useState<CredentialsErrors>({});
  const [notice, setNotice] = useState('');
  const nameRef = useRef<TextInput>(null);
  const emailRef = useRef<TextInput>(null);
  const passwordRef = useRef<TextInput>(null);
  const isSignUp = mode === 'sign-up';

  function updateField(field: FieldName, value: string) {
    setDraft((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
    setNotice('');
  }

  function handleSubmit() {
    const nextErrors = validateCredentials(mode, draft);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      setNotice('');
      return;
    }

    setNotice(
      'This is only a prototype. Your details were not sent or persisted, and no account was created.',
    );
  }

  return (
    <ScrollView
      contentContainerStyle={styles.content}
      contentInsetAdjustmentBehavior="automatic"
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
        <View style={styles.intro}>
          <Text style={styles.eyebrow}>A SMALL STEP, A GOOD START</Text>
          <Text accessibilityRole="header" style={styles.title}>
            {isSignUp ? 'Let’s get to know you.' : 'Good to have you back.'}
          </Text>
          <Text style={styles.description}>
            {isSignUp
              ? 'This draft shows the account setup flow. It is not connected to an authentication service.'
              : 'This draft shows the sign-in flow. It is not connected to an authentication service.'}
          </Text>
        </View>

        <View style={styles.form}>
          {isSignUp ? (
            <FormField
              autoComplete="name"
              error={errors.displayName}
              inputRef={nameRef}
              label="Name"
              onChangeText={(value) => updateField('displayName', value)}
              onSubmitEditing={() => emailRef.current?.focus()}
              placeholder="What should we call you?"
              returnKeyType="next"
              textContentType="name"
              value={draft.displayName}
            />
          ) : null}

          <FormField
            autoCapitalize="none"
            autoComplete="email"
            autoCorrect={false}
            error={errors.email}
            inputRef={emailRef}
            keyboardType="email-address"
            label="Email"
            onChangeText={(value) => updateField('email', value)}
            onSubmitEditing={() => passwordRef.current?.focus()}
            placeholder="you@example.com"
            returnKeyType="next"
            textContentType="emailAddress"
            value={draft.email}
          />

          <FormField
            autoCapitalize="none"
            autoComplete={isSignUp ? 'new-password' : 'current-password'}
            error={errors.password}
            inputRef={passwordRef}
            label="Password"
            onChangeText={(value) => updateField('password', value)}
            onSubmitEditing={handleSubmit}
              placeholder={isSignUp ? 'Choose a password' : 'Enter your password'}
            returnKeyType="done"
            secureTextEntry
            textContentType={isSignUp ? 'newPassword' : 'password'}
            value={draft.password}
          />

          <MotionPressable
            accessibilityLabel={isSignUp ? 'Continue with account setup' : 'Continue with sign-in'}
            onPress={handleSubmit}
            style={styles.primaryAction}
          >
            <Text style={styles.primaryActionText}>Continue</Text>
          </MotionPressable>
        </View>

        {notice ? (
          <Text accessibilityLiveRegion="polite" style={styles.notice}>
            {notice}
          </Text>
        ) : null}

        <View style={styles.switchRow}>
          <Text style={styles.switchPrompt}>
            {isSignUp ? 'Already have an account?' : 'New to the community?'}
          </Text>
          <MotionPressable
            accessibilityLabel={isSignUp ? 'Go to sign in' : 'Create a new account'}
            onPress={() => router.replace(isSignUp ? '/account/sign-in' : '/account/sign-up')}
            style={styles.switchAction}
          >
            <Text style={styles.switchActionText}>{isSignUp ? 'Sign in' : 'Sign up'}</Text>
          </MotionPressable>
        </View>

        <Text style={styles.disclaimer}>
          Local UI prototype · No credentials are transmitted or persisted
        </Text>
    </ScrollView>
  );
}

type FormFieldProps = {
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
  autoComplete?: 'email' | 'name' | 'new-password' | 'current-password';
  autoCorrect?: boolean;
  error?: string;
  inputRef: React.RefObject<TextInput | null>;
  keyboardType?: 'default' | 'email-address';
  label: string;
  onChangeText: (value: string) => void;
  onSubmitEditing: () => void;
  placeholder: string;
  returnKeyType: 'next' | 'done';
  secureTextEntry?: boolean;
  textContentType?: 'name' | 'emailAddress' | 'newPassword' | 'password';
  value: string;
};

function FormField({
  autoCapitalize = 'sentences',
  autoComplete,
  autoCorrect,
  error,
  inputRef,
  keyboardType = 'default',
  label,
  onChangeText,
  onSubmitEditing,
  placeholder,
  returnKeyType,
  secureTextEntry,
  textContentType,
  value,
}: FormFieldProps) {
  const colors = useAppTheme();
  const styles = useMemo(() => makeStyles(colors), [colors]);
  const inputStyle = error ? [styles.input, styles.inputError] : styles.input;

  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        accessibilityHint={error}
        accessibilityLabel={label}
        autoCapitalize={autoCapitalize}
        autoComplete={autoComplete}
        autoCorrect={autoCorrect}
        onChangeText={onChangeText}
        onSubmitEditing={onSubmitEditing}
        placeholder={placeholder}
        placeholderTextColor={colors.inkSubtle}
        ref={inputRef}
        returnKeyType={returnKeyType}
        secureTextEntry={secureTextEntry}
        selectionColor={colors.accent}
        style={inputStyle}
        textContentType={textContentType}
        value={value}
      />
      {error ? (
        <Text accessibilityLiveRegion="polite" style={styles.fieldError}>
          {error}
        </Text>
      ) : null}
    </View>
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
      lineHeight: 20,
    },
    form: {
      gap: spacing.md,
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
    primaryAction: {
      minHeight: 54,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: colors.accent,
      borderRadius: radius.full,
      borderCurve: 'continuous',
    },
    primaryActionText: {
      color: colors.heroInk,
      fontSize: typeScale.body,
      fontWeight: '700',
    },
    notice: {
      padding: spacing.md,
      color: colors.accentInk,
      fontSize: typeScale.footnote,
      lineHeight: 20,
      backgroundColor: colors.accentSoft,
      borderRadius: radius.md,
      borderCurve: 'continuous',
    },
    switchRow: {
      minHeight: 44,
      flexDirection: 'row',
      flexWrap: 'wrap',
      alignItems: 'center',
      justifyContent: 'center',
      columnGap: spacing.xxs,
    },
    switchPrompt: {
      color: colors.inkMuted,
      fontSize: typeScale.footnote,
    },
    switchAction: {
      minHeight: 44,
      justifyContent: 'center',
      paddingHorizontal: spacing.xxs,
    },
    switchActionText: {
      color: colors.accent,
      fontSize: typeScale.footnote,
      fontWeight: '700',
    },
    disclaimer: {
      color: colors.inkSubtle,
      fontSize: typeScale.caption,
      lineHeight: 18,
      textAlign: 'center',
    },
  });
}
