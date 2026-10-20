import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { QuizFinish } from '@/api/types';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { Fireworks } from './Fireworks';
import { ResultGate } from './ResultGate';
import { ShrineRope } from './ShrineRope';

type Props = {
  result: QuizFinish;
  quizName: string;
  onContinue: () => void;
  onReview: () => void;
  onRetake: () => void;
};

// Quiz result (#21). Passed: the rope is released and fireworks go up.
// Not passed: the rope stays tied, with a gentle, encouraging message.
export function QuizResult({ result, quizName, onContinue, onReview, onRetake }: Props) {
  const { passed, score, correct, total, best_score, pass_mark } = result;
  const needed = Math.ceil((pass_mark / 100) * total) - correct;

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.top}>
          {passed && <Fireworks />}
          <ResultGate open={passed} />
          <Text style={[styles.title, !passed && styles.titleSoft]}>
            {passed ? 'အောင်ပါပြီ' : 'နောက်တစ်ကြိမ် ကြိုးစားကြည့်ရအောင်'}
          </Text>
          <Text style={styles.sub}>
            {passed ? `${quizName} ကို ဖြတ်ကျော်ပြီးပါပြီ` : `အောင်ဖို့ နောက်ထပ် ${Math.max(1, needed)} ခုပဲ လိုပါတော့တယ်`}
          </Text>
          <Text style={styles.score}>
            {score}
            <Text style={styles.percent}>%</Text>
          </Text>
        </View>

        <View style={styles.rope}>
          <ShrineRope released={passed} />
        </View>

        <View style={styles.stats}>
          <Stat value={`${correct} / ${total}`} label="မှန်" />
          <Stat value={String(total - correct)} label="မှား" />
          <Stat value={`${best_score}%`} label="အကောင်းဆုံး" />
        </View>

        <View style={[styles.note, passed ? styles.noteOpen : styles.noteClosed]}>
          <Text style={[styles.noteText, passed && styles.noteTextOpen]}>
            {passed
              ? 'နောက်ယူနစ်များ ပွင့်ပါပြီ'
              : `နောက်ယူနစ်များကို ဖွင့်ဖို့ ${pass_mark}% လိုပါတယ်။ အကြိမ်အကန့်အသတ် မရှိ ပြန်ဖြေနိုင်ပါတယ်။`}
          </Text>
        </View>
      </ScrollView>

      <View style={styles.buttons}>
        {passed ? (
          <>
            <Button label="ဆက်လေ့လာမည်" kind="primary" onPress={onContinue} />
            <Button label="အဖြေများ ပြန်ကြည့်မည်" kind="secondary" onPress={onReview} />
            <Button label="ပြန်ဖြေမည်" kind="link" onPress={onRetake} />
          </>
        ) : (
          <>
            <Button label="မှားခဲ့တာတွေ ပြန်ကြည့်မည်" kind="primary" onPress={onReview} />
            <Button label="ပြန်ဖြေမည်" kind="secondary" onPress={onRetake} />
            <Button label="မြေပုံသို့ ပြန်မည်" kind="link" onPress={onContinue} />
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function Button({ label, kind, onPress }: { label: string; kind: 'primary' | 'secondary' | 'link'; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => [styles.button, kind === 'primary' && styles.primary, kind === 'secondary' && styles.secondary, kind === 'link' && styles.link, pressed && { opacity: 0.85 }]}
    >
      <Text style={[styles.buttonText, kind === 'primary' && styles.primaryText, kind === 'link' && styles.linkText]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    gap: spacing.md,
    paddingBottom: spacing.lg,
    width: '100%',
    maxWidth: 520,
    alignSelf: 'center',
  },
  top: {
    alignItems: 'center',
    gap: spacing.sm,
    paddingTop: spacing.xl,
    paddingHorizontal: spacing.xl,
  },
  title: {
    fontFamily: fonts.burmeseSerif,
    fontSize: 24,
    lineHeight: 50,
    color: colors.lacquer,
    textAlign: 'center',
  },
  titleSoft: {
    fontSize: 20,
    lineHeight: 42,
  },
  sub: {
    ...text.small,
    fontSize: 14,
    color: colors.inkMuted,
    textAlign: 'center',
  },
  score: {
    marginTop: spacing.sm,
    fontFamily: fonts.japaneseBold,
    fontSize: 52,
    lineHeight: 60,
    color: colors.ink,
  },
  percent: {
    fontSize: 22,
  },
  rope: {
    width: '100%',
  },
  stats: {
    flexDirection: 'row',
    gap: spacing.sm,
    paddingHorizontal: spacing.xl,
  },
  stat: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: colors.surface,
  },
  statValue: {
    fontFamily: fonts.japaneseBold,
    fontSize: 18,
    lineHeight: 26,
    color: colors.ink,
  },
  statLabel: {
    ...text.small,
    fontSize: 12,
    lineHeight: 21,
    color: colors.inkMuted,
  },
  note: {
    marginHorizontal: spacing.xl,
    padding: spacing.md,
    borderRadius: 12,
  },
  noteOpen: {
    backgroundColor: colors.goldSoft,
  },
  noteClosed: {
    borderWidth: 1.5,
    borderColor: colors.divider,
    backgroundColor: colors.surface,
  },
  noteText: {
    ...text.small,
    fontSize: 14,
    lineHeight: 25,
    color: colors.inkMuted,
  },
  noteTextOpen: {
    fontFamily: fonts.burmeseBold,
    color: '#7A5A12',
  },
  buttons: {
    gap: 10,
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.sm,
    paddingBottom: spacing.lg,
    width: '100%',
    maxWidth: 520,
    alignSelf: 'center',
  },
  button: {
    height: 52,
    borderRadius: radius.control,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primary: {
    backgroundColor: colors.ink,
  },
  secondary: {
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  link: {
    height: 44,
  },
  buttonText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 16,
    lineHeight: 28,
    color: colors.ink,
  },
  primaryText: {
    color: colors.onInk,
  },
  linkText: {
    fontFamily: fonts.burmese,
    fontSize: 15,
    color: colors.inkMuted,
    textDecorationLine: 'underline',
  },
});
