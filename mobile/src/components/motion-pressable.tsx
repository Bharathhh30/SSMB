import type { PropsWithChildren } from 'react';
import { Pressable, type PressableProps, type StyleProp, type ViewStyle } from 'react-native';
import Animated, { cubicBezier, useReducedMotion } from 'react-native-reanimated';

import { motion } from '@/theme';

type MotionPressableProps = PropsWithChildren<{
  accessibilityLabel?: string;
  accessibilityRole?: PressableProps['accessibilityRole'];
  accessibilityState?: PressableProps['accessibilityState'];
  disabled?: boolean;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
  testID?: string;
}>;

const pressCurve = cubicBezier(0.23, 1, 0.32, 1);

export function MotionPressable({
  accessibilityLabel,
  accessibilityRole = 'button',
  accessibilityState,
  children,
  disabled = false,
  onPress,
  style,
  testID,
}: MotionPressableProps) {
  const reduceMotion = useReducedMotion();

  return (
    <Pressable
      accessibilityLabel={accessibilityLabel}
      accessibilityRole={accessibilityRole}
      accessibilityState={{ ...accessibilityState, disabled }}
      disabled={disabled}
      onPress={onPress}
      pressRetentionOffset={{ top: 12, right: 12, bottom: 12, left: 12 }}
      testID={testID}
    >
      {({ pressed }) => (
        <Animated.View
          style={[
            style,
            !reduceMotion && {
              transform: [{ scale: pressed ? motion.pressScale : 1 }],
              transitionProperty: ['transform', 'backgroundColor'],
              transitionDuration: motion.pressDuration,
              transitionTimingFunction: pressCurve,
            },
          ]}
        >
          {children}
        </Animated.View>
      )}
    </Pressable>
  );
}
