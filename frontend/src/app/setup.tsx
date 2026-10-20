import { useState } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { submitOnboarding } from '@/api';
import type { OnboardingRequest } from '@/api/types';
import { PlanLoading } from '@/components/Loading';
import { Logo } from '@/components/Logo';
import { AlertIcon, CalendarIcon } from '@/components/ui/Icons';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { formatDateMy, upcomingJlptDates } from '@/utils/myanmar';

type Level = OnboardingRequest['last_level'];
type Errors = { level?: string; score?: string; date?: string };

const LEVELS: { value: Level; label: string }[] = [
  { value: 'N1', label: 'N1' },
  { value: 'N2', label: 'N2' },
  { value: 'not_taken', label: 'မဖြေရသေး' },
];

// First-time setup (#9): last level, score and exam date.
export default function SetupScreen() {
  const [level, setLevel] = useState<Level | null>(null);
  const [scoreText, setScoreText] = useState('');
  const [examDate, setExamDate] = useState<string | null>(null);
  const [undecided, setUndecided] = useState(false);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [errors, setErrors] = useState<Errors>({});
  const [submitting, setSubmitting] = useState(false);

  const needsScore = level === 'N1' || level === 'N2';

  // The same rules the backend checks (#9). The backend has the final say.
  function validate(): OnboardingRequest | null {
    const found: Errors = {};
    if (!level) found.level = 'အဆင့်ကို ရွေးပါ။';
    let score: number | null = null;
    if (needsScore) {
      const isWholeNumber = /^\d+$/.test(scoreText.trim());
      score = isWholeNumber ? Number(scoreText.trim()) : NaN;
      if (!isWholeNumber || score < 0 || score > 180) found.score = 'ရမှတ်ကို 0 မှ 180 အထိသာ ထည့်ပါ။';
    }
    if (!undecided && !examDate) found.date = 'ရက်စွဲကို ရွေးပါ၊ ဒါမှမဟုတ် "မဆုံးဖြတ်ရသေးပါ" ကို ရွေးပါ။';
    setErrors(found);
    if (Object.keys(found).length > 0 || !level) return null;
    return { last_level: level, last_score: needsScore ? score : null, exam_date: undecided ? null : examDate };
  }

  async function submit() {
    const answers = validate();
    if (!answers) return;
    setSubmitting(true);
    await submitOnboarding(answers);
    router.replace('/plan');
  }

  if (submitting) return <PlanLoading />;

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <View style={styles.logoTile}>
            <Logo size={48} />
          </View>
          <Text style={styles.title}>မေးခွန်း ၃ ခု ဖြေပေးပါ</Text>
          <Text style={styles.subtitle}>သင့်အတွက် လေ့လာမှု အစီအစဉ်ကို ပြုလုပ်ပေးပါမယ်။</Text>
        </View>

        <View style={styles.card}>
          <Label number={1} text="နောက်ဆုံး ဖြေဆိုခဲ့သော အဆင့်" />
          <View style={styles.segments} accessibilityRole="radiogroup">
            {LEVELS.map((item) => {
              const on = level === item.value;
              return (
                <Pressable
                  key={item.value}
                  onPress={() => {
                    setLevel(item.value);
                    if (item.value === 'not_taken') setScoreText('');
                  }}
                  accessibilityRole="radio"
                  accessibilityState={{ checked: on }}
                  style={[styles.segment, on && styles.segmentOn]}
                >
                  <Text style={[styles.segmentText, on && styles.segmentTextOn]}>{item.label}</Text>
                </Pressable>
              );
            })}
          </View>
          {errors.level && <ErrorText message={errors.level} />}
        </View>

        <View style={[styles.card, !needsScore && styles.cardDisabled]}>
          <Label number={2} text="ရရှိခဲ့သော ရမှတ်" />
          <View style={[styles.scoreBox, errors.score && styles.inputError]}>
            <TextInput
              value={scoreText}
              onChangeText={setScoreText}
              editable={needsScore}
              keyboardType="number-pad"
              maxLength={3}
              placeholder={needsScore ? '0' : '—'}
              placeholderTextColor={colors.inkMuted}
              accessibilityLabel="ရမှတ်"
              style={styles.scoreInput}
            />
            <Text style={styles.scoreMax}>/ 180</Text>
          </View>
          {errors.score ? (
            <ErrorText message={errors.score} />
          ) : (
            <Text style={styles.hint}>{needsScore ? '0 မှ 180 အထိ ကိန်းပြည့်' : 'မဖြေရသေးရင် ရမှတ် မလိုပါ'}</Text>
          )}
        </View>

        <View style={styles.card}>
          <Label number={3} text="စာမေးပွဲ ဖြေမည့်ရက်" />
          <Pressable
            onPress={() => setPickerOpen(true)}
            disabled={undecided}
            accessibilityRole="button"
            style={[styles.dateField, undecided && styles.fieldDisabled, errors.date && styles.inputError]}
          >
            <Text style={styles.dateText}>{examDate ? formatDateMy(examDate) : 'ရက်စွဲ ရွေးပါ'}</Text>
            <CalendarIcon color={colors.ink} />
          </Pressable>
          <Pressable
            onPress={() => setUndecided((value) => !value)}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: undecided }}
            style={styles.checkRow}
          >
            <View style={[styles.checkbox, undecided && styles.checkboxOn]} />
            <Text style={styles.checkText}>မဆုံးဖြတ်ရသေးပါ</Text>
          </Pressable>
          {errors.date ? (
            <ErrorText message={errors.date} />
          ) : (
            <Text style={styles.hint}>JLPT ကို ပုံမှန်အားဖြင့် ဇူလိုင်နဲ့ ဒီဇင်ဘာလ အစောပိုင်း တနင်္ဂနွေနေ့တွေမှာ ကျင်းပပါတယ်။</Text>
          )}
        </View>

        <Pressable onPress={submit} style={({ pressed }) => [styles.primaryButton, pressed && { opacity: 0.85 }]}>
          <Text style={styles.primaryText}>အစီအစဉ် ပြုလုပ်မည်</Text>
        </Pressable>
      </ScrollView>

      <Modal visible={pickerOpen} transparent animationType="fade" onRequestClose={() => setPickerOpen(false)}>
        <Pressable style={styles.backdrop} onPress={() => setPickerOpen(false)}>
          <View style={styles.sheet}>
            <Text style={styles.sheetTitle}>စာမေးပွဲ ရက်စွဲ</Text>
            {upcomingJlptDates(3).map((date) => (
              <Pressable
                key={date}
                onPress={() => {
                  setExamDate(date);
                  setPickerOpen(false);
                }}
                style={[styles.dateOption, examDate === date && styles.dateOptionOn]}
              >
                <Text style={styles.dateText}>{formatDateMy(date)}</Text>
              </Pressable>
            ))}
            <Text style={styles.hint}>တခြားရက်ကို နောက်ပိုင်း ပြက္ခဒိန်နဲ့ ရွေးနိုင်အောင် လုပ်ပေးပါမယ်။</Text>
          </View>
        </Pressable>
      </Modal>
    </SafeAreaView>
  );
}

function Label({ number, text: label }: { number: number; text: string }) {
  return (
    <View style={styles.labelRow}>
      <View style={styles.numberBadge}>
        <Text style={styles.numberText}>{number}</Text>
      </View>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

function ErrorText({ message }: { message: string }) {
  return (
    <View style={styles.errorRow} accessibilityRole="alert">
      <AlertIcon color={colors.wrong} />
      <Text style={styles.errorText}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.goldSoft,
  },
  content: {
    gap: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xxl,
    width: '100%',
    maxWidth: 520,
    alignSelf: 'center',
  },
  header: {
    alignItems: 'center',
    gap: spacing.sm,
    paddingTop: spacing.xl,
    paddingBottom: spacing.sm,
  },
  logoTile: {
    width: 64,
    height: 64,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: colors.goldDeep,
    borderRadius: 18,
    backgroundColor: colors.background,
  },
  title: {
    fontFamily: fonts.burmeseSerif,
    fontSize: 22,
    lineHeight: 40,
    color: colors.lacquer,
  },
  subtitle: {
    ...text.small,
    fontSize: 14,
    color: colors.inkMuted,
    textAlign: 'center',
  },
  card: {
    gap: 10,
    padding: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: radius.card,
    backgroundColor: colors.background,
  },
  cardDisabled: {
    opacity: 0.6,
  },
  labelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  numberBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.ink,
  },
  numberText: {
    fontFamily: fonts.japaneseBold,
    fontSize: 12,
    color: colors.onInk,
  },
  label: {
    ...text.label,
    fontSize: 15,
    lineHeight: 26,
    color: colors.ink,
  },
  segments: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  segment: {
    flex: 1,
    height: 46,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radius.control,
    backgroundColor: colors.background,
  },
  segmentOn: {
    borderColor: colors.ink,
    backgroundColor: colors.ink,
  },
  segmentText: {
    ...text.body,
    fontSize: 15,
    color: colors.ink,
  },
  segmentTextOn: {
    fontFamily: fonts.burmeseBold,
    color: colors.onInk,
  },
  scoreBox: {
    height: 52,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.borderWarm,
    borderRadius: radius.control,
    backgroundColor: colors.background,
  },
  scoreInput: {
    flex: 1,
    fontFamily: fonts.japaneseBold,
    fontSize: 20,
    color: colors.ink,
  },
  scoreMax: {
    fontFamily: fonts.japanese,
    fontSize: 16,
    color: colors.inkMuted,
  },
  inputError: {
    borderWidth: 2,
    borderColor: colors.wrong,
  },
  hint: {
    ...text.small,
    color: colors.inkMuted,
  },
  errorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  errorText: {
    ...text.label,
    fontSize: 13,
    flexShrink: 1,
    color: colors.wrong,
  },
  dateField: {
    height: 52,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.borderWarm,
    borderRadius: radius.control,
    backgroundColor: colors.background,
  },
  fieldDisabled: {
    opacity: 0.45,
  },
  dateText: {
    ...text.body,
    color: colors.ink,
  },
  checkRow: {
    minHeight: 40,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderWidth: 2,
    borderColor: colors.borderWarm,
    borderRadius: 6,
    backgroundColor: colors.background,
  },
  checkboxOn: {
    borderColor: colors.ink,
    backgroundColor: colors.ink,
  },
  checkText: {
    ...text.body,
    fontSize: 14,
    color: colors.ink,
  },
  primaryButton: {
    height: 54,
    marginTop: spacing.sm,
    borderRadius: radius.control,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.ink,
  },
  primaryText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 17,
    lineHeight: 28,
    color: colors.onInk,
  },
  backdrop: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(42, 37, 34, 0.4)',
  },
  sheet: {
    gap: spacing.sm,
    padding: spacing.xl,
    paddingBottom: spacing.xxl,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    backgroundColor: colors.background,
  },
  sheetTitle: {
    ...text.label,
    fontSize: 16,
    lineHeight: 28,
    color: colors.ink,
  },
  dateOption: {
    minHeight: 52,
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radius.control,
  },
  dateOptionOn: {
    borderColor: colors.ink,
    backgroundColor: colors.goldSoft,
  },
});
