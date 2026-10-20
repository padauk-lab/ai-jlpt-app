import { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, Platform, Easing, StyleSheet, View } from 'react-native';
import Svg, { Circle, G, Line } from 'react-native-svg';

type Burst = { left: number; top: number; size: number; line: string; dot: string; delay: number };

// Positions are shares of the area's width and height, so it fits any screen.
const BURSTS: Burst[] = [
  { left: 0.18, top: 0.3, size: 64, line: '#C8102E', dot: '#D9A441', delay: 0 },
  { left: 0.82, top: 0.22, size: 56, line: '#D9A441', dot: '#C8102E', delay: 600 },
  { left: 0.5, top: 0.08, size: 48, line: '#E8452C', dot: '#D9A441', delay: 1200 },
  { left: 0.86, top: 0.62, size: 40, line: '#D9A441', dot: '#E8452C', delay: 1600 },
  { left: 0.13, top: 0.7, size: 44, line: '#E8452C', dot: '#D9A441', delay: 900 },
];

const ROUNDS = 3;

function BurstShape({ size, line, dot }: { size: number; line: string; dot: string }) {
  const c = size / 2;
  const r = size * 0.42;
  const angles = Array.from({ length: 12 }, (_, i) => (i * 30 * Math.PI) / 180);
  return (
    <Svg width={size} height={size}>
      <G stroke={line} strokeWidth={2.6} strokeLinecap="round">
        {angles.map((a, i) => (
          <Line key={i} x1={c + 0.35 * r * Math.cos(a)} y1={c + 0.35 * r * Math.sin(a)} x2={c + r * Math.cos(a)} y2={c + r * Math.sin(a)} />
        ))}
      </G>
      {angles.map((a, i) => (
        <Circle key={i} cx={c + 1.15 * r * Math.cos(a + Math.PI / 12)} cy={c + 1.15 * r * Math.sin(a + Math.PI / 12)} r={2.2} fill={dot} />
      ))}
    </Svg>
  );
}

function AnimatedBurst({ burst, width, height }: { burst: Burst; width: number; height: number }) {
  const t = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const one = Animated.sequence([
      Animated.timing(t, { toValue: 0, duration: 0, useNativeDriver: Platform.OS !== 'web' }),
      Animated.timing(t, { toValue: 1, duration: 2200, easing: Easing.out(Easing.cubic), useNativeDriver: Platform.OS !== 'web' }),
    ]);
    const run = Animated.sequence([Animated.delay(burst.delay), Animated.loop(one, { iterations: ROUNDS })]);
    run.start();
    return () => run.stop();
  }, [t, burst.delay]);

  // rise up as a small spark, burst open, then fade away
  const translateY = t.interpolate({ inputRange: [0, 0.22, 1], outputRange: [70, 0, 6] });
  const scale = t.interpolate({ inputRange: [0, 0.22, 0.55, 1], outputRange: [0.05, 0.08, 1, 1.18] });
  const opacity = t.interpolate({ inputRange: [0, 0.05, 0.55, 1], outputRange: [0, 1, 1, 0] });

  return (
    <Animated.View
      style={{
        position: 'absolute',
        left: burst.left * width - burst.size / 2,
        top: burst.top * height - burst.size / 2,
        opacity,
        transform: [{ translateY }, { scale }],
      }}
    >
      <BurstShape size={burst.size} line={burst.line} dot={burst.dot} />
    </Animated.View>
  );
}

// Fireworks for a passed quiz. Decoration only, so screen readers skip it.
// With Reduce Motion on, the bursts are shown faint and still.
export function Fireworks() {
  const [size, setSize] = useState({ width: 0, height: 0 });
  const [reduceMotion, setReduceMotion] = useState<boolean | null>(null);

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduceMotion);
  }, []);

  return (
    <View
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={StyleSheet.absoluteFill}
      onLayout={(e) => setSize({ width: e.nativeEvent.layout.width, height: e.nativeEvent.layout.height })}
    >
      {size.width > 0 &&
        reduceMotion !== null &&
        BURSTS.map((burst, i) =>
          reduceMotion ? (
            <View
              key={i}
              style={{ position: 'absolute', opacity: 0.45, left: burst.left * size.width - burst.size / 2, top: burst.top * size.height - burst.size / 2 }}
            >
              <BurstShape size={burst.size} line={burst.line} dot={burst.dot} />
            </View>
          ) : (
            <AnimatedBurst key={i} burst={burst} width={size.width} height={size.height} />
          ),
        )}
    </View>
  );
}
