import { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, Easing, Platform, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Ellipse, Path, Rect, Text as SvgText } from 'react-native-svg';
import { colors, fonts, spacing, text } from '@/theme';

// "Generating plan": a small ox cart travels slowly along the road toward
// the 合格 torii gate, while the backend calculates the study plan.

const INK = '#2E2B2A';
const RIB = '#6E6762';
const RED = '#C8102E';
const NATIVE = Platform.OS !== 'web';

const SCENE_W = 342;
const CART_W = 124; // the cart drawing is 160 x 80, shown at 124 x 62
const CART_H = 62;
const SCALE = CART_W / 160;
const TRAVEL = 196; // how far the cart moves before it passes through the gate
const TRIP_MS = 8000;

function Wheel({ size, faded = false }: { size: number; faded?: boolean }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 30 30" opacity={faded ? 0.55 : 1}>
      <Circle cx={15} cy={15} r={13.5} stroke={INK} strokeWidth={2.6} fill={colors.goldSoft} />
      <Path d="M15 15 L26.61 15.00 M15 15 L25.05 20.80 M15 15 L20.80 25.05 M15 15 L15.00 26.61 M15 15 L9.20 25.05 M15 15 L4.95 20.80 M15 15 L3.39 15.00 M15 15 L4.95 9.20 M15 15 L9.19 4.95 M15 15 L15.00 3.39 M15 15 L20.80 4.95 M15 15 L25.05 9.19" stroke={INK} strokeWidth={1.2} />
      <Circle cx={15} cy={15} r={11.6} stroke={INK} strokeWidth={1} fill="none" />
      <Circle cx={15} cy={15} r={2.4} fill={INK} />
    </Svg>
  );
}

// The covered cart, the driver and the ox, without the wheels (they turn separately).
function CartBody() {
  return (
    <Svg width={CART_W} height={CART_H} viewBox="0 0 160 80" fill="none">
      <Path d="M6 48 L6 20 C 6 11, 12 8, 20 8 L 54 8.5 C 62 9, 66 15, 66 24 L 66 48 Z" fill={INK} />
      <Path d="M17 9 L17 47 M28 8.6 L28 47 M39 8.6 L39 47 M50 8.7 L50 47" stroke={RIB} strokeWidth={0.9} />
      <Path d="M60 12 C 64 14, 66 19, 66 25 L 66 48 L 59 48 L 59 22 C 59 17, 59.5 14, 60 12 Z" fill={colors.goldSoft} opacity={0.9} />
      <Rect x={3} y={47} width={66} height={5} rx={1} fill={INK} />
      <Path d="M64 50 L101 43" stroke={INK} strokeWidth={3} strokeLinecap="round" />
      <Ellipse cx={65.5} cy={26.5} rx={7} ry={1.8} fill={INK} />
      <Path d="M62 26.5 C 62 22.5, 69 22.5, 69 26.5 Z" fill={INK} />
      <Circle cx={65.5} cy={29.5} r={3} fill={INK} />
      <Path d="M61 33 C 63 31.5, 68 31.5, 69.5 34 L 71 41 L 74 42 L 74 46 L 62 46 Z" fill={INK} />
      <Path d="M69 38 L 82 25" stroke={INK} strokeWidth={1.3} strokeLinecap="round" />
      <Path
        d="M101 44 C 99 36, 104 31, 112 31 C 122 30.5, 132 31.5, 138 33 C 141 31, 145 30, 147 31 L 153 37 C 155 39, 154 42, 151 42 C 148 42, 146 41.5, 144 43 C 142 48, 139 52, 134 54 L 109 54.5 C 104 53.5, 101 49.5, 101 44 Z"
        fill={INK}
      />
      <Path d="M145 30.5 C 144.2 27.5, 145.5 25.5, 147.5 25.2 M149 31 C 150 28, 152 27, 153.6 27.6" stroke={INK} strokeWidth={1.6} strokeLinecap="round" />
      <Path d="M102 46 C 98 50, 98 56, 99 62 L 100.5 65" stroke={INK} strokeWidth={1.3} strokeLinecap="round" />
      <Path d="M110 53 L 108 71 M134 53 L 136 71 M115 53 L 116 71 M129 53 L 128 71" stroke={INK} strokeWidth={3.2} strokeLinecap="round" />
    </Svg>
  );
}

function Gate() {
  return (
    <Svg width={132} height={124} viewBox="0 0 100 94">
      <Ellipse cx={50} cy={89} rx={42} ry={5} fill="#2A2522" opacity={0.12} />
      <Path d="M3 9 Q50 19 97 9 L96 3 Q50 13 4 3 Z" fill="#2A2522" />
      <Path d="M6 11 Q50 21 94 11 L93 19 Q50 28 7 19 Z" fill={RED} />
      <Rect x={14} y={33} width={72} height={7} fill={RED} />
      <Rect x={22} y={20} width={9} height={64} fill={RED} />
      <Rect x={69} y={20} width={9} height={64} fill={RED} />
      <Rect x={19} y={82} width={15} height={6} fill="#2A2522" />
      <Rect x={66} y={82} width={15} height={6} fill="#2A2522" />
      <Rect x={40} y={19} width={20} height={17} rx={1.5} fill="#D9A441" stroke="#2A2522" strokeWidth={1.5} />
      <SvgText x={50} y={31} textAnchor="middle" fontFamily={fonts.brand} fontSize={8} fill="#6B2E1A">
        合格
      </SvgText>
    </Svg>
  );
}

export function PlanLoading() {
  const trip = useRef(new Animated.Value(0)).current; // 0 → 1 along the road, again and again
  const [reduceMotion, setReduceMotion] = useState<boolean | null>(null);

  useEffect(() => {
    let loop: Animated.CompositeAnimation | null = null;
    AccessibilityInfo.isReduceMotionEnabled().then((reduce) => {
      setReduceMotion(reduce);
      if (reduce) {
        trip.setValue(0.4); // stand still partway to the gate
        return;
      }
      loop = Animated.loop(Animated.timing(trip, { toValue: 1, duration: TRIP_MS, easing: Easing.linear, useNativeDriver: NATIVE }));
      loop.start();
    });
    return () => loop?.stop();
  }, [trip]);

  const translateX = trip.interpolate({ inputRange: [0, 1], outputRange: [-20, TRAVEL] });
  const opacity = trip.interpolate({ inputRange: [0, 0.08, 0.86, 1], outputRange: [0, 1, 1, 0] });
  // A wheel of about 22 px rolls one turn per ~68 px of road.
  const spin = trip.interpolate({ inputRange: [0, 1], outputRange: ['0deg', `${(216 / 68) * 360}deg`] });
  // The ox's slow walk makes the cart rock very slightly.
  const bob = trip.interpolate({ inputRange: [0, 0.25, 0.5, 0.75, 1], outputRange: [0, -1, 0, -1, 0] });

  const wheelSize = Math.round(30 * SCALE * 0.95);
  const wheelTop = 59 * SCALE - wheelSize / 2;

  return (
    <View style={styles.screen}>
      <View style={styles.scene} accessible accessibilityLabel="合格 တံခါးဆီ သွားနေသော နွားလှည်း">
        <Svg style={styles.road} width="100%" height={4}>
          <Path d={`M0 2 L${SCENE_W} 2`} stroke={colors.borderWarm} strokeWidth={2.5} strokeDasharray="7 6" />
        </Svg>
        <View style={styles.gate}>
          <Gate />
        </View>
        {reduceMotion !== null && (
          <Animated.View style={[styles.cart, { opacity, transform: [{ translateX }, { translateY: bob }] }]}>
            <CartBody />
            <Animated.View style={[styles.wheel, { left: 32 * SCALE - wheelSize / 2, top: wheelTop, transform: [{ rotate: spin }] }]}>
              <Wheel size={wheelSize} faded />
            </Animated.View>
            <Animated.View style={[styles.wheel, { left: 40 * SCALE - wheelSize / 2, top: wheelTop, transform: [{ rotate: spin }] }]}>
              <Wheel size={wheelSize} />
            </Animated.View>
          </Animated.View>
        )}
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
    gap: spacing.lg,
    padding: spacing.xl,
    backgroundColor: colors.goldSoft,
  },
  scene: {
    width: SCENE_W,
    maxWidth: '100%',
    height: 190,
    overflow: 'hidden',
  },
  road: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 13,
  },
  gate: {
    position: 'absolute',
    right: 6,
    bottom: 9,
  },
  cart: {
    position: 'absolute',
    left: 0,
    bottom: 8,
    width: CART_W,
    height: CART_H,
  },
  wheel: {
    position: 'absolute',
  },
  title: {
    fontFamily: fonts.burmeseSerif,
    fontSize: 20,
    lineHeight: 42,
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
