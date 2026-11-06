import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';
import { colors, fonts } from '@/theme';
import { formatClock } from './useCountdown';

// The countdown in the top bar. It turns red in the last 5 minutes.
export function TimerChip({ seconds }: { seconds: number }) {
  const warn = seconds < 5 * 60;
  return (
    <View
      accessibilityRole="timer"
      accessibilityLabel={`ကျန်အချိန် ${Math.ceil(seconds / 60)} မိနစ်`}
      style={[styles.chip, { backgroundColor: warn ? colors.wrong : colors.ink }]}
    >
      <Svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
        <Circle cx={12} cy={13} r={8} />
        <Path d="M12 9v4l2.5 2M10 2h4" />
      </Svg>
      <Text style={styles.text}>{formatClock(seconds)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    height: 36,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    borderRadius: 18,
  },
  text: {
    fontFamily: fonts.japaneseBold,
    fontSize: 17,
    color: '#FFFFFF',
    fontVariant: ['tabular-nums'],
  },
});
