import { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, Platform, Easing, StyleSheet, View } from 'react-native';
import Svg, { Circle, Ellipse, G, Path, Rect } from 'react-native-svg';

// A shimenawa (しめ縄), the sacred straw rope of a shrine, across the screen.
// Not passed: tied tight with a big knot in the middle, like a lock.
// Passed: released, both halves swing down from their posts.

const W = 342;
const H = 106;
const LEFT_POST = { x: 10, y: 24 };
const RIGHT_POST = { x: 332, y: 24 };
const SAG = { x: 171, y: 48 };

const STRAW = { base: '#B48A45', twist: '#E6CB8E', knot: '#8F6A2E' };
const PALE = { base: '#C9B08A', twist: '#EFE0BF', knot: '#A88B55' };

function point(t: number) {
  const a = (1 - t) * (1 - t);
  const b = 2 * (1 - t) * t;
  const c = t * t;
  return {
    x: a * LEFT_POST.x + b * SAG.x + c * RIGHT_POST.x,
    y: a * LEFT_POST.y + b * SAG.y + c * RIGHT_POST.y,
  };
}

const FULL_ROPE = `M${LEFT_POST.x} ${LEFT_POST.y} Q${SAG.x} ${SAG.y} ${RIGHT_POST.x} ${RIGHT_POST.y}`;
const LEFT_HALF = `M${LEFT_POST.x} ${LEFT_POST.y} C 22 50, 18 70, 34 92`;
const RIGHT_HALF = `M${RIGHT_POST.x} ${RIGHT_POST.y} C 320 50, 324 70, 308 92`;

function Rope({ d, colors, width = 12 }: { d: string; colors: typeof STRAW; width?: number }) {
  return (
    <>
      <Path d={d} stroke={colors.base} strokeWidth={width} strokeLinecap="round" fill="none" />
      <Path d={d} stroke={colors.twist} strokeWidth={width} strokeDasharray="2.6 3.4" fill="none" />
    </>
  );
}

// 紙垂 (shide): the white zigzag paper streamers that hang from the rope.
function Shide({ x, y }: { x: number; y: number }) {
  return (
    <Path
      transform={`translate(${x - 3.6} ${y}) scale(1.5)`}
      d="M0 0 l3.2 0 l-1.6 3.4 l3.2 0 l-1.6 3.4 l3.2 0 l-3.4 4.2 l1.4 -3.2 l-3.2 0 l1.6 -3.4 l-3.2 0 Z"
      fill="#FFFFFF"
      stroke="#B8A57A"
      strokeWidth={0.6}
      strokeLinejoin="round"
    />
  );
}

export function ShrineRope({ released }: { released: boolean }) {
  return released ? <ReleasedRope /> : <TiedRope />;
}

function TiedRope() {
  const c = PALE;
  const middle = point(0.5);
  return (
    <View style={styles.box} accessible accessibilityLabel="ကြိုးကို အလယ်မှာ ချည်ထားဆဲ">
      <Svg width="100%" height="100%" viewBox={`0 0 ${W} ${H}`} fill="none">
        <Rope d={FULL_ROPE} colors={c} />
        {[0.18, 0.32, 0.68, 0.82].map((t) => {
          const p = point(t);
          return <Shide key={t} x={p.x} y={p.y + 6} />;
        })}
        <Circle cx={LEFT_POST.x} cy={LEFT_POST.y} r={7.5} fill={c.knot} />
        <Circle cx={RIGHT_POST.x} cy={RIGHT_POST.y} r={7.5} fill={c.knot} />
        <G transform={`translate(${middle.x} ${middle.y})`}>
          <Rope d="M-6 3 C -10 18, -16 30, -13 42" colors={c} width={7} />
          <Rope d="M6 3 C 10 18, 16 30, 13 42" colors={c} width={7} />
          <Ellipse cx={-15} cy={-3} rx={14} ry={8} rotation={-18} origin="-15, -3" stroke={c.knot} strokeWidth={6} />
          <Ellipse cx={15} cy={-3} rx={14} ry={8} rotation={18} origin="15, -3" stroke={c.knot} strokeWidth={6} />
          <Rect x={-9} y={-10} width={18} height={18} rx={6} fill={c.knot} />
          <Path d="M-6 -7 L6 5 M-6 0 L1 7 M-1 -8 L6 -1" stroke={c.twist} strokeWidth={1.6} strokeLinecap="round" />
        </G>
      </Svg>
    </View>
  );
}

function ReleasedRope() {
  const c = STRAW;
  const swing = useRef(new Animated.Value(0)).current;
  const [reduceMotion, setReduceMotion] = useState(false);

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then((reduce) => {
      setReduceMotion(reduce);
      if (reduce) {
        swing.setValue(1);
        return;
      }
      Animated.timing(swing, {
        toValue: 1,
        duration: 1400,
        easing: Easing.out(Easing.back(2)),
        useNativeDriver: Platform.OS !== 'web',
      }).start();
    });
  }, [swing]);

  const leftTurn = swing.interpolate({ inputRange: [0, 1], outputRange: ['-14deg', '0deg'] });
  const rightTurn = swing.interpolate({ inputRange: [0, 1], outputRange: ['14deg', '0deg'] });
  const origin = (x: number, y: number) => `${(x / W) * 100}% ${(y / H) * 100}%`;

  return (
    <View style={styles.box} accessible accessibilityLabel="ကြိုးကို ဖြေလိုက်ပြီ">
      <Animated.View
        style={[StyleSheet.absoluteFill, { transformOrigin: origin(LEFT_POST.x, LEFT_POST.y), transform: [{ rotate: reduceMotion ? '0deg' : leftTurn }] }]}
      >
        <Svg width="100%" height="100%" viewBox={`0 0 ${W} ${H}`} fill="none">
          <Rope d={LEFT_HALF} colors={c} />
          <Shide x={24} y={60} />
        </Svg>
      </Animated.View>
      <Animated.View
        style={[StyleSheet.absoluteFill, { transformOrigin: origin(RIGHT_POST.x, RIGHT_POST.y), transform: [{ rotate: reduceMotion ? '0deg' : rightTurn }] }]}
      >
        <Svg width="100%" height="100%" viewBox={`0 0 ${W} ${H}`} fill="none">
          <Rope d={RIGHT_HALF} colors={c} />
          <Shide x={318} y={60} />
        </Svg>
      </Animated.View>
      <Svg width="100%" height="100%" viewBox={`0 0 ${W} ${H}`} fill="none" style={StyleSheet.absoluteFill}>
        <Circle cx={LEFT_POST.x} cy={LEFT_POST.y} r={7.5} fill={c.knot} />
        <Circle cx={RIGHT_POST.x} cy={RIGHT_POST.y} r={7.5} fill={c.knot} />
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    width: '100%',
    aspectRatio: W / H,
  },
});
