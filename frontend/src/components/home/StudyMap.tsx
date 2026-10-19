import { Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';
import type { SessionDetail } from '@/api/types';
import { Torii } from '@/components/Torii';
import { CheckIcon, LockIcon, PlayIcon } from '@/components/TabIcons';
import { colors, fonts } from '@/theme';
import { BaganBackground, MAP_HEIGHT, MAP_WIDTH } from './BaganBackground';
import { buildMapLayout, pathThrough, type MapStop } from './mapLayout';

type Props = {
  session: SessionDetail;
  onOpenStop: (stop: MapStop) => void;
};

const SAND = '#F1E6D0';
const ROAD = '#FBF7EE';
const ROAD_EDGE = '#E0D0B0';
const NEXT_MARKER = { x: 112, y: 25 };

export function StudyMap({ session, onOpenStop }: Props) {
  const { stops, currentIndex, goldUntil } = buildMapLayout(session);
  const current = currentIndex >= 0 ? stops[currentIndex] : undefined;
  const last = stops[stops.length - 1];

  return (
    <View style={styles.sand}>
      <View style={styles.frame}>
        <View style={StyleSheet.absoluteFill}>
          <BaganBackground />
        </View>

        <Svg width={MAP_WIDTH} height={MAP_HEIGHT} style={StyleSheet.absoluteFill}>
          <Path d={pathThrough(stops)} stroke={ROAD_EDGE} strokeWidth={22} strokeLinecap="round" strokeLinejoin="round" fill="none" />
          <Path d={pathThrough(stops)} stroke={ROAD} strokeWidth={15} strokeLinecap="round" strokeLinejoin="round" fill="none" />
          <Path
            d={`M ${last.x} ${last.y} L ${NEXT_MARKER.x} ${NEXT_MARKER.y}`}
            stroke="#B9A47E"
            strokeWidth={4}
            strokeDasharray="2 10"
            strokeLinecap="round"
          />
          {goldUntil > 0 && (
            <Path
              d={pathThrough(stops.slice(0, goldUntil + 1))}
              stroke={colors.gold}
              strokeWidth={15}
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
          )}
        </Svg>

        <View style={styles.nextSession}>
          <LockIcon color={colors.inkMuted} size={13} />
          <Text style={styles.nextSessionText}>အပိုင်း {session.number + 1}</Text>
        </View>

        {stops.map((stop) => (
          <Stop key={stop.key} stop={stop} onPress={() => onOpenStop(stop)} />
        ))}

        {current && <ContinueBubble stop={current} onPress={() => onOpenStop(current)} />}
      </View>
    </View>
  );
}

function Stop({ stop, onPress }: { stop: MapStop; onPress: () => void }) {
  const locked = stop.state === 'locked';

  if (stop.kind === 'unit') {
    if (stop.state === 'current') {
      return (
        <Pressable
          onPress={onPress}
          accessibilityLabel={`ယူနစ် ${stop.label} ကို စတင်မည်`}
          style={[styles.place, { left: stop.x - 47, top: stop.y - 47 }]}
        >
          <View style={styles.currentHalo}>
            <View style={styles.currentRing}>
              <View style={styles.currentCircle}>
                <Text style={styles.currentText}>{stop.label}</Text>
              </View>
            </View>
          </View>
        </Pressable>
      );
    }
    return (
      <Pressable
        onPress={onPress}
        disabled={locked}
        accessibilityLabel={`ယူနစ် ${stop.label}`}
        accessibilityState={{ disabled: locked }}
        style={[
          styles.place,
          styles.unit,
          locked ? styles.unitLocked : styles.unitDone,
          { left: stop.x - 28, top: stop.y - 28 },
        ]}
      >
        <Text style={locked ? styles.unitLockedText : styles.unitDoneText}>{stop.label}</Text>
      </Pressable>
    );
  }

  const width = stop.kind === 'mock' ? 88 : 64;
  const height = Math.round(width * 0.94);
  const labelOnLeft = stop.x < 195;
  const labelWidth = stop.kind === 'mock' ? 110 : 80;

  return (
    <>
      <Pressable
        onPress={onPress}
        disabled={locked}
        accessibilityLabel={stop.label}
        accessibilityState={{ disabled: locked }}
        style={[styles.place, { left: stop.x - width / 2, top: stop.y - height / 2, opacity: locked ? 0.8 : 1 }]}
      >
        <Torii width={width} withPlaque={stop.kind === 'mock'} />
        {stop.state !== 'current' && (
          <View style={[styles.badge, stop.state === 'done' && styles.badgeDone]}>
            {stop.state === 'done' ? <CheckIcon color={colors.ink} /> : <LockIcon color={colors.inkMuted} />}
          </View>
        )}
      </Pressable>
      <Text
        style={[
          styles.testLabel,
          {
            width: labelWidth,
            top: stop.y - 12,
            left: labelOnLeft ? Math.max(4, stop.x - width / 2 - labelWidth - 8) : stop.x + width / 2 + 10,
            textAlign: labelOnLeft ? 'right' : 'left',
          },
        ]}
      >
        {stop.label}
      </Text>
    </>
  );
}

function ContinueBubble({ stop, onPress }: { stop: MapStop; onPress: () => void }) {
  const onRight = stop.x < 250;
  const label = stop.kind === 'unit' ? 'ဆက်လေ့လာမည်' : 'စာမေးပွဲ ဖြေမည်';
  const gap = stop.kind === 'unit' ? 46 : 52;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.bubble,
        { top: stop.y - 20 },
        onRight ? { left: stop.x + gap } : { right: MAP_WIDTH - stop.x + gap },
        pressed && { opacity: 0.85 },
      ]}
    >
      <PlayIcon color={colors.onInk} />
      <Text style={styles.bubbleText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  sand: {
    backgroundColor: SAND,
    alignItems: 'center',
    overflow: 'hidden',
  },
  frame: {
    width: MAP_WIDTH,
    height: MAP_HEIGHT,
  },
  place: {
    position: 'absolute',
  },
  unit: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  unitDone: {
    backgroundColor: colors.gold,
    borderWidth: 3,
    borderColor: '#FFFFFF',
  },
  unitDoneText: {
    fontFamily: fonts.japaneseBold,
    fontSize: 20,
    color: colors.ink,
  },
  unitLocked: {
    backgroundColor: ROAD,
    borderWidth: 2,
    borderColor: ROAD_EDGE,
  },
  unitLockedText: {
    fontFamily: fonts.japanese,
    fontSize: 19,
    color: '#8C847E',
  },
  currentHalo: {
    width: 94,
    height: 94,
    borderRadius: 47,
    backgroundColor: '#F6EAD0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  currentRing: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
  },
  currentCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 4,
    borderColor: '#FFFFFF',
    backgroundColor: colors.ink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  currentText: {
    fontFamily: fonts.japaneseBold,
    fontSize: 26,
    color: colors.onInk,
  },
  badge: {
    position: 'absolute',
    right: -6,
    bottom: -4,
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: ROAD_EDGE,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeDone: {
    backgroundColor: colors.gold,
    borderColor: '#FFFFFF',
  },
  testLabel: {
    position: 'absolute',
    fontFamily: fonts.burmeseBold,
    fontSize: 12,
    lineHeight: 20,
    color: '#4A4440',
  },
  nextSession: {
    position: 'absolute',
    left: NEXT_MARKER.x - 55,
    top: NEXT_MARKER.y - 20,
    width: 110,
    height: 40,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: ROAD_EDGE,
    backgroundColor: ROAD,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  nextSessionText: {
    fontFamily: fonts.burmese,
    fontSize: 13,
    lineHeight: 22,
    color: colors.inkMuted,
  },
  bubble: {
    position: 'absolute',
    height: 40,
    paddingHorizontal: 14,
    borderRadius: 20,
    backgroundColor: colors.ink,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  bubbleText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 14,
    lineHeight: 24,
    color: colors.onInk,
  },
});
