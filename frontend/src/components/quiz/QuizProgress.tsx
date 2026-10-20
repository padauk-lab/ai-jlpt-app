import { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, Easing, StyleSheet, View, type LayoutChangeEvent } from 'react-native';
import { PalmLeafStylus } from '@/components/PalmLeafStylus';
import { colors } from '@/theme';

const ICON_WIDTH = 46;

// The quiz progress bar. A palm-leaf book with a stylus rides along it
// to the current question, like someone writing an exam.
export function QuizProgress({ current, total }: { current: number; total: number }) {
  const [width, setWidth] = useState(0);
  const [reduceMotion, setReduceMotion] = useState(false);
  const share = useRef(new Animated.Value(0)).current;
  const target = total > 0 ? current / total : 0;

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduceMotion);
  }, []);

  useEffect(() => {
    if (reduceMotion) {
      share.setValue(target);
      return;
    }
    Animated.timing(share, {
      toValue: target,
      duration: 700,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false, // animates width, which the native driver cannot do
    }).start();
  }, [target, reduceMotion, share]);

  const onLayout = (event: LayoutChangeEvent) => setWidth(event.nativeEvent.layout.width);
  const fillWidth = share.interpolate({ inputRange: [0, 1], outputRange: [0, width] });
  const iconLeft = share.interpolate({
    inputRange: [0, 1],
    outputRange: [0, Math.max(0, width - ICON_WIDTH)],
    extrapolate: 'clamp',
  });

  return (
    <View
      style={styles.wrap}
      onLayout={onLayout}
      accessibilityRole="progressbar"
      accessibilityValue={{ min: 0, max: total, now: current }}
    >
      <View style={styles.track}>
        <Animated.View style={[styles.fill, { width: fillWidth }]} />
      </View>
      {width > 0 && (
        <Animated.View style={[styles.icon, { transform: [{ translateX: iconLeft }] }]}>
          <PalmLeafStylus width={ICON_WIDTH} />
        </Animated.View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flex: 1,
    height: 44,
    justifyContent: 'flex-end',
  },
  track: {
    height: 9,
    borderRadius: 5,
    overflow: 'hidden',
    backgroundColor: colors.track,
  },
  fill: {
    height: 9,
    borderRadius: 5,
    backgroundColor: colors.gold,
  },
  icon: {
    position: 'absolute',
    left: 0,
    bottom: 6,
  },
});
