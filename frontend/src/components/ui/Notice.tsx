import { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, spacing, text } from '@/theme';

// A short message that disappears by itself, e.g. "coming soon".
// (React Native's Alert does nothing on the web, so we draw our own.)
export function useNotice(durationMs = 2200) {
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(() => setMessage(null), durationMs);
    return () => clearTimeout(timer);
  }, [message, durationMs]);

  return { message, show: setMessage };
}

export function Notice({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <View style={styles.wrap} pointerEvents="none">
      <Text accessibilityLiveRegion="polite" style={styles.text}>
        {message}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    position: 'absolute',
    left: spacing.xl,
    right: spacing.xl,
    bottom: 110,
    alignItems: 'center',
  },
  text: {
    ...text.small,
    overflow: 'hidden',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: 20,
    backgroundColor: colors.ink,
    color: colors.onInk,
    textAlign: 'center',
  },
});
