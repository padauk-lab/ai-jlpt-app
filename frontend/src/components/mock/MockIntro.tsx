import { ScrollView, StyleSheet, Text, View } from 'react-native';
import Svg, { Path, Rect } from 'react-native-svg';
import { Torii } from '@/components/Torii';
import { Button } from '@/components/settings/SettingsUI';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { toMyanmarDigits } from '@/utils/myanmar';

type Props = {
  sessionNumber: number | null;
  resuming: boolean; // a test is already in progress: "continue" instead of "start"
  retake: boolean; // the first attempt is done: retakes don't change the prediction
  busy: boolean;
  problem: string | null;
  onStart: () => void;
};

const RULES = [
  'ဝေါဟာရနဲ့ သဒ္ဒါ (言語知識) မေးခွန်း ၄၅ ခု၊ စာဖတ် (読解) တို၊ အလယ်၊ ရှည် ၃ ပုဒ်။',
  'စတင်တာနဲ့ အချိန် ၃၀ မိနစ် စရေတွက်ပါတယ်။ app ပိတ်ထားလည်း အချိန် ဆက်သွားပြီး ပြန်ဝင်ရင် ဆက်ဖြေနိုင်ပါတယ်။',
  'အချိန် ကုန်ရင် ဖြေထားသလောက်နဲ့ အလိုအလျောက် တင်သွင်းပါမယ်။',
  'တင်သွင်းပြီးမှ အဖြေမှန်/မှား ကို ပြပါမယ်။',
];

// The start screen with the rules (contract "Mock test rules").
export function MockIntro({ sessionNumber, resuming, retake, busy, problem, onStart }: Props) {
  return (
    <ScrollView contentContainerStyle={styles.content}>
      <View style={styles.hero}>
        <Torii width={120} withPlaque />
        <Text style={styles.title}>
          စမ်းသပ် စာမေးပွဲ{sessionNumber ? ` ${toMyanmarDigits(sessionNumber)}` : ''}
        </Text>
        <Text style={styles.subtitle}>အပိုင်းရဲ့ နောက်ဆုံး တံခါး</Text>
      </View>

      <View style={styles.stats}>
        <Stat value="51" label="မေးခွန်း" />
        <Stat value="30:00" label="မိနစ်" />
        <Stat value="3" label="စာဖတ်ခန်း" />
      </View>

      <View style={styles.rules}>
        {RULES.map((rule) => (
          <View key={rule} style={styles.rule}>
            <Svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="#7A5A12" strokeWidth={2} strokeLinecap="round">
              <Rect x={5} y={3} width={14} height={18} rx={2} />
              <Path d="M9 8h6M9 12h6M9 16h3" />
            </Svg>
            <Text style={styles.ruleText}>{rule}</Text>
          </View>
        ))}
        <View style={styles.rule}>
          <Svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="#7A5A12" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <Path d="M12 3l2.6 5.6 6.1.7-4.5 4.2 1.2 6L12 16.6 6.6 19.5l1.2-6L3.3 9.3l6.1-.7z" />
          </Svg>
          <Text style={styles.ruleText}>
            {retake
              ? 'ဒါက ပြန်ဖြေခြင်းပါ။ 合格予測 (အောင်မြင်နိုင်ခြေ) ကို မပြောင်းပါ။'
              : 'ပထမအကြိမ် ရလဒ်ပဲ 合格予測 (အောင်မြင်နိုင်ခြေ) မှာ ထည့်တွက်ပါတယ်။'}
          </Text>
        </View>
      </View>

      {problem && <Text style={styles.problem}>{problem}</Text>}
      <Button label={resuming ? 'ဆက်ဖြေမည်' : retake ? 'ပြန်ဖြေမည်' : 'စတင်မည်'} onPress={onStart} busy={busy} />
      <Text style={styles.note}>အေးဆေးတဲ့ နေရာမှာ အချိန် ၃၀ မိနစ် ရတဲ့အခါ စပါ</Text>
    </ScrollView>
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

const styles = StyleSheet.create({
  content: { gap: spacing.lg, padding: 20, paddingBottom: spacing.xxl, width: '100%', maxWidth: 520, alignSelf: 'center' },
  hero: { alignItems: 'center', gap: 2, paddingTop: spacing.lg },
  title: { fontFamily: fonts.burmeseSerif, fontSize: 22, lineHeight: 46, color: colors.lacquer },
  subtitle: { ...text.small, fontSize: 13, color: colors.inkMuted },
  stats: { flexDirection: 'row', gap: spacing.sm },
  stat: { flex: 1, alignItems: 'center', paddingVertical: 10, borderRadius: 12, backgroundColor: colors.background },
  statValue: { fontFamily: fonts.japaneseBold, fontSize: 20, color: colors.ink },
  statLabel: { ...text.small, fontSize: 12, color: colors.inkMuted },
  rules: { gap: spacing.md },
  rule: { flexDirection: 'row', gap: spacing.md, alignItems: 'flex-start' },
  ruleText: { ...text.small, flex: 1, fontSize: 14, lineHeight: 25, color: colors.ink },
  problem: { ...text.small, fontSize: 14, lineHeight: 25, padding: spacing.md, borderRadius: radius.control, backgroundColor: colors.wrongBg, color: '#9E2F29' },
  note: { ...text.small, fontSize: 12, textAlign: 'center', color: colors.inkMuted },
});
