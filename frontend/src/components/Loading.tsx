import { useEffect, useRef } from 'react';
import { AccessibilityInfo, Animated, StyleSheet, Text, View } from 'react-native';
import { Logo } from '@/components/Logo';
import { colors, fonts, spacing, text } from '@/theme';

// "Generating plan": the logo with three gently bouncing gold dots.
export function PlanLoading() {
  const beat = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    let loop: Animated.CompositeAnimation | null = null;
    AccessibilityInfo.isReduceMotionEnabled().then((reduce) => {
      if (reduce) return;
      loop = Animated.loop(Animated.timing(beat, { toValue: 3, duration: 1200, useNativeDriver: true }));
      loop.start();
    });
    return () => loop?.stop();
  }, [beat]);

  const dot = (i: number) => ({
    opacity: beat.interpolate({ inputRange: [i, i + 0.5, i + 1, 3], outputRange: [0.3, 1, 0.3, 0.3], extrapolate: 'clamp' }),
    transform: [{ translateY: beat.interpolate({ inputRange: [i, i + 0.5, i + 1, 3], outputRange: [0, -6, 0, 0], extrapolate: 'clamp' }) }],
  });

  return (
    <View style={styles.screen}>
      <View style={styles.tile}>
        <Logo size={86} />
      </View>
      <View style={styles.dots}>
        {[0, 1, 2].map((i) => (
          <Animated.View key={i} style={[styles.dot, dot(i)]} />
        ))}
      </View>
      <Text accessibilityRole="text" accessibilityLiveRegion="polite" style={styles.title}>
        သင့်အတွက် အစီအစဉ်ကို ပြင်ဆင်နေပါတယ်
      </Text>
      <Text style={styles.sub}>ကျန်ရက်နဲ့ ယူနစ်တွေကို တွက်ချက်နေပါတယ်…</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.xl,
    padding: spacing.xxl,
    backgroundColor: colors.goldSoft,
  },
  tile: {
    width: 112,
    height: 112,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: colors.goldDeep,
    borderRadius: 31,
    backgroundColor: colors.background,
  },
  dots: {
    flexDirection: 'row',
    gap: 10,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.goldDeep,
  },
  title: {
    fontFamily: fonts.burmeseSerif,
    fontSize: 20,
    lineHeight: 36,
    color: colors.lacquer,
    textAlign: 'center',
  },
  sub: {
    ...text.small,
    fontSize: 14,
    marginTop: -spacing.md,
    color: colors.inkMuted,
    textAlign: 'center',
  },
});
