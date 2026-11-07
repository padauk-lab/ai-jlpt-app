import { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, ActivityIndicator, Animated, Easing, Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import Svg, { Path, Text as SvgText } from 'react-native-svg';
import { getMockResult } from '@/api';
import type { MockResult } from '@/api/types';
import { OrnateFrame } from '@/components/OrnateFrame';
import { Torii } from '@/components/Torii';
import { Button } from '@/components/settings/SettingsUI';
import { colors, fonts, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';

const PART_LABELS: Record<MockResult['parts'][number]['part'], [string, string]> = {
  vocabulary: ['ဝေါဟာရ', '語彙'],
  grammar: ['သဒ္ဒါ', '文法'],
  reading: ['စာဖတ်', '読解'],
};

const WARNINGS: Record<string, string> = {
  language_knowledge_low: 'ဝေါဟာရ/သဒ္ဒါ အပိုင်း အမှတ် နည်းနေပါတယ်။ တကယ့် N1 မှာ အပိုင်းတိုင်း အနည်းဆုံး ၁၉/၆၀ လိုလို့ 合格予測 ကို ၁၅% အထိသာ ပြပါတယ်။',
  reading_low: 'စာဖတ် အပိုင်း အမှတ် နည်းနေပါတယ်။ တကယ့် N1 မှာ အပိုင်းတိုင်း အနည်းဆုံး ၁၉/၆၀ လိုလို့ 合格予測 ကို ၁၅% အထိသာ ပြပါတယ်။',
  both_low: 'အပိုင်း နှစ်ခုလုံး အမှတ် နည်းနေပါတယ်။ တကယ့် N1 မှာ အပိုင်းတိုင်း အနည်းဆုံး ၁၉/၆၀ လိုလို့ 合格予測 ကို ၁၅% အထိသာ ပြပါတယ်။',
};

// Ring made of one segment per question: gold for each correct answer.
function SegmentRing({ correct, total, size = 140 }: { correct: number; total: number; size?: number }) {
  const c = 70;
  const r = 56;
  const gap = 2.2;
  const segments = Array.from({ length: total }, (_, i) => {
    const a0 = ((-90 + (i * 360) / total + gap / 2) * Math.PI) / 180;
    const a1 = ((-90 + ((i + 1) * 360) / total - gap / 2) * Math.PI) / 180;
    const d = `M${(c + r * Math.cos(a0)).toFixed(2)} ${(c + r * Math.sin(a0)).toFixed(2)} A${r} ${r} 0 0 1 ${(c + r * Math.cos(a1)).toFixed(2)} ${(c + r * Math.sin(a1)).toFixed(2)}`;
    return <Path key={i} d={d} stroke={i < correct ? colors.goldDeep : '#E2D3B5'} strokeWidth={13} fill="none" />;
  });
  const percent = total > 0 ? Math.round((correct / total) * 100) : 0;
  return (
    <Svg width={size} height={size} viewBox="0 0 140 140" accessibilityLabel={`ရမှတ် ${percent}%`}>
      {segments}
      <SvgText x={70} y={80} textAnchor="middle" fontFamily={fonts.japaneseBold} fontSize={30} fill="#3E2A12">
        {`${percent}%`}
      </SvgText>
    </Svg>
  );
}

function Rod() {
  return (
    <View style={styles.rod}>
      <View style={styles.knob} />
      <View style={styles.rodBar} />
      <View style={styles.knob} />
    </View>
  );
}

// The mock test result (#26) on an unrolling palm-leaf scroll.
export default function MockResultScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [result, setResult] = useState<MockResult | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const unroll = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    getMockResult(Number(id))
      .then(setResult)
      .catch((error) => setProblem(errorMessage(error)));
  }, [id]);

  // Unroll the scroll once the result is here.
  useEffect(() => {
    if (!result) return;
    AccessibilityInfo.isReduceMotionEnabled().then((reduce) => {
      if (reduce) {
        unroll.setValue(1);
        return;
      }
      Animated.timing(unroll, { toValue: 1, duration: 1100, easing: Easing.out(Easing.cubic), useNativeDriver: Platform.OS !== 'web' }).start();
    });
  }, [result, unroll]);

  if (!result) {
    return (
      <SafeAreaView style={styles.center}>
        {problem ? <Text style={styles.problem}>{problem}</Text> : <ActivityIndicator color={colors.ink} />}
      </SafeAreaView>
    );
  }

  const minutes = Math.floor(result.time_used_seconds / 60);
  const seconds = result.time_used_seconds % 60;
  const timeUsed = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.hero}>
          <Torii width={64} withPlaque />
          <Text style={styles.title}>စမ်းသပ် စာမေးပွဲ ပြီးပါပြီ</Text>
          <Text style={styles.subtitle}>
            {result.submitted_by === 'timeout' ? 'အချိန် ကုန်လို့ အလိုအလျောက် တင်သွင်းခဲ့ပါတယ်' : `အချိန် ${timeUsed} သုံးခဲ့ပါတယ်`}
          </Text>
        </View>

        <View style={styles.scroll}>
          <Rod />
          <Animated.View style={[styles.paper, { opacity: unroll, transformOrigin: 'top', transform: [{ scaleY: unroll }] }]}>
            <View style={styles.scoreRow}>
              <SegmentRing correct={result.score.correct} total={result.score.total} />
              <View style={styles.framed}>
                <OrnateFrame label={`${result.score.correct} / ${result.score.total}`} width={150} />
                <Text style={styles.framedLabel}>မှန်ခဲ့သော မေးခွန်း</Text>
              </View>
            </View>

            <View style={styles.dots} />
            {result.parts.map((part) => (
              <View key={part.part} style={styles.part}>
                <View style={styles.partRow}>
                  <Text style={styles.partName}>
                    {PART_LABELS[part.part][0]} <Text style={styles.partJa}>{PART_LABELS[part.part][1]}</Text>
                  </Text>
                  <Text style={styles.partScore}>
                    {part.correct} / {part.total}
                  </Text>
                </View>
                <View style={styles.bar}>
                  <View style={[styles.barFill, { width: `${part.total ? (part.correct / part.total) * 100 : 0}%` }]} />
                </View>
              </View>
            ))}
            <View style={styles.dots} />

            <View style={styles.prediction}>
              <View style={{ flex: 1 }}>
                <Text style={styles.partName}>
                  အောင်မြင်နိုင်ခြေ <Text style={styles.partJa}>合格予測</Text>
                </Text>
                <Text style={styles.predictionNote}>
                  {result.counts_for_prediction ? 'ပထမအကြိမ် ဖြစ်လို့ ဒီရလဒ်ကို ထည့်တွက်ပါတယ်' : 'ပြန်ဖြေခြင်းမို့ 合格予測 ကို မပြောင်းပါ'}
                </Text>
              </View>
              <Text style={styles.predictionValue}>{result.pass_prediction === null ? '—' : `${result.pass_prediction}%`}</Text>
            </View>
            {result.pass_prediction_warning && (
              <Text style={styles.warning}>{WARNINGS[result.pass_prediction_warning]}</Text>
            )}
          </Animated.View>
          <Rod />
        </View>

        <View style={styles.buttons}>
          <Button label="မြေပုံသို့ ဆက်သွားမည်" onPress={() => router.replace('/home')} />
          <Button
            label="အဖြေများ ပြန်ကြည့်မည်"
            kind="secondary"
            onPress={() => router.push({ pathname: '/review/[id]', params: { id: String(result.attempt_id), kind: 'mock' } })}
          />
        </View>
        <Text style={styles.footnote}>စမ်းသပ်စာမေးပွဲမှာ အောင်မှတ် မရှိပါ။ နောက်အပိုင်း ပွင့်ပါပြီ။</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const PAPER = '#EFDDB0';
const DARK = '#3E2A12';

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.goldSoft },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl, backgroundColor: colors.goldSoft },
  problem: { ...text.body, textAlign: 'center', color: colors.ink },
  content: { gap: spacing.lg, padding: 20, paddingBottom: spacing.xxl, width: '100%', maxWidth: 520, alignSelf: 'center' },
  hero: { alignItems: 'center', gap: 2 },
  title: { fontFamily: fonts.burmeseSerif, fontSize: 21, lineHeight: 44, color: colors.lacquer, textAlign: 'center' },
  subtitle: { ...text.small, fontSize: 13, color: colors.inkMuted, textAlign: 'center' },
  scroll: { paddingHorizontal: 2 },
  rod: { height: 22, marginHorizontal: -12, flexDirection: 'row', alignItems: 'center', zIndex: 2 },
  knob: { width: 16, height: 22, borderRadius: 8, backgroundColor: colors.lacquer },
  rodBar: { flex: 1, height: 16, borderRadius: 3, backgroundColor: '#7A3A22' },
  paper: {
    gap: 14,
    marginVertical: -4,
    paddingHorizontal: 16,
    paddingVertical: 20,
    borderLeftWidth: 2,
    borderRightWidth: 2,
    borderColor: '#C9A75E',
    backgroundColor: PAPER,
  },
  scoreRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: spacing.sm },
  framed: { alignItems: 'center', gap: 2 },
  framedLabel: { ...text.small, fontSize: 12, color: '#6B5A3E' },
  dots: { height: 1, backgroundColor: '#C9A75E' },
  part: { gap: 4 },
  partRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  partName: { ...text.label, fontSize: 14, color: DARK },
  partJa: { fontFamily: fonts.japanese, color: '#6B5A3E' },
  partScore: { fontFamily: fonts.japaneseBold, fontSize: 15, color: DARK },
  bar: { height: 8, borderRadius: 4, overflow: 'hidden', backgroundColor: '#E2CFA0' },
  barFill: { height: 8, borderRadius: 4, backgroundColor: colors.goldDeep },
  prediction: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  predictionNote: { ...text.small, fontSize: 12, lineHeight: 21, color: '#6B5A3E' },
  predictionValue: { fontFamily: fonts.japaneseBold, fontSize: 26, color: colors.lacquer },
  warning: { ...text.small, fontSize: 13, lineHeight: 23, padding: spacing.md, borderRadius: 10, backgroundColor: colors.wrongBg, color: '#9E2F29' },
  buttons: { gap: spacing.sm },
  footnote: { ...text.small, fontSize: 12, textAlign: 'center', color: colors.inkMuted },
});
