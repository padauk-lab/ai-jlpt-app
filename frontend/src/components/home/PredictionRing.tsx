import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { colors, fonts } from '@/theme';

type Props = {
  value: number | null; // 0 to 100, or null before the first mock test
  size?: number;
};

// The pass prediction (合格予測) as a number inside a progress ring.
export function PredictionRing({ value, size = 68 }: Props) {
  const stroke = 7;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const filled = value === null ? 0 : (circumference * value) / 100;

  return (
    <View style={{ width: size, height: size }}>
      <Svg width={size} height={size} style={[StyleSheet.absoluteFill, { transform: [{ rotate: '-90deg' }] }]}>
        <Circle cx={size / 2} cy={size / 2} r={radius} stroke="#EFE9E1" strokeWidth={stroke} fill="none" />
        {value !== null && value > 0 && (
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={colors.goldDeep}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${filled} ${circumference}`}
            fill="none"
          />
        )}
      </Svg>
      <View style={[StyleSheet.absoluteFill, styles.center]}>
        <Text style={styles.number}>
          {value === null ? '—' : value}
          {value !== null && <Text style={styles.percent}>%</Text>}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  center: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  number: {
    fontFamily: fonts.japaneseBold,
    fontSize: 19,
    color: colors.ink,
  },
  percent: {
    fontSize: 11,
  },
});
