import { useMemo } from 'react';
import { StyleSheet, Text } from 'react-native';

import { typeScale, useAppTheme } from '@/theme';

type ApiRequestReferenceProps = {
  requestId?: string;
};

export function ApiRequestReference({ requestId }: ApiRequestReferenceProps) {
  const colors = useAppTheme();
  const styles = useMemo(
    () =>
      StyleSheet.create({
        reference: {
          color: colors.inkSubtle,
          fontSize: typeScale.caption,
          textAlign: 'center',
        },
      }),
    [colors],
  );

  if (!requestId) {
    return null;
  }

  return (
    <Text accessibilityLabel={`Support reference ${requestId}`} selectable style={styles.reference}>
      Reference ID: {requestId}
    </Text>
  );
}
