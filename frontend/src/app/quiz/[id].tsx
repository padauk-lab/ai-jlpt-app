import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import { answerQuestion, explainAnswer, resetFakeQuiz, startQuiz } from '@/api';
import type { AnswerResult, Explanation, QuizAttempt, QuizOption } from '@/api/types';
import { PromptText } from '@/components/quiz/PromptText';
import { QuizProgress } from '@/components/quiz/QuizProgress';
import { CloseIcon, SparkIcon } from '@/components/ui/Icons';
import Svg, { Path } from 'react-native-svg';
import { colors, fonts, spacing, text } from '@/theme';

const PASS_MARK = 70; // contract: quizzes need 70% or more

// Question types from the contract, with a Burmese name and the JLPT name.
const TYPE_LABELS: Record<string, [string, string]> = {
  kanji_reading: ['ခန်းဂျီ အသံထွက်', '漢字読み'],
  context: ['စကားလုံး အသုံး', '文脈規定'],
  grammar: ['သဒ္ဒါ', '文法'],
};

export default function QuizScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [index, setIndex] = useState(0);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [explaining, setExplaining] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);
  const [finished, setFinished] = useState(false);

  const begin = useCallback(async () => {
    resetFakeQuiz();
    setAttempt(null);
    setIndex(0);
    setResult(null);
    setExplanation(null);
    setCorrectCount(0);
    setFinished(false);
    setAttempt(await startQuiz(Number(id)));
  }, [id]);

  useEffect(() => {
    begin();
  }, [begin]);

  if (!attempt) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator color={colors.ink} />
      </SafeAreaView>
    );
  }

  const total = attempt.questions.length;

  if (finished) {
    const score = Math.round((correctCount / total) * 100);
    const passed = score >= PASS_MARK;
    return (
      <SafeAreaView style={styles.resultScreen}>
        <Text style={styles.resultTitle}>{passed ? 'အောင်ပါပြီ' : 'ထပ်ကြိုးစားကြည့်ပါ'}</Text>
        <Text style={styles.resultScore}>{score}%</Text>
        <Text style={styles.muted}>
          {total} ခုအနက် {correctCount} ခု မှန်ပါတယ် ၊ အောင်မှတ် {PASS_MARK}%
        </Text>
        <View style={styles.resultButtons}>
          <Pressable onPress={begin} style={styles.secondaryButton}>
            <Text style={styles.secondaryText}>ပြန်ဖြေမည်</Text>
          </Pressable>
          <Pressable onPress={() => router.back()} style={styles.primaryButton}>
            <Text style={styles.primaryText}>မြေပုံသို့ ပြန်မည်</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  const question = attempt.questions[index];
  const [typeMy, typeJa] = TYPE_LABELS[question.type] ?? ['မေးခွန်း', ''];
  const answered = result !== null;

  async function choose(option: QuizOption['id']) {
    if (answered || !attempt) return;
    const res = await answerQuestion(attempt.attempt_id, question.id, option);
    setResult(res);
    if (res.is_correct) setCorrectCount((n) => n + 1);
  }

  async function why() {
    if (!result) return;
    setExplaining(true);
    setExplanation(await explainAnswer(question.id, result.selected_option_id));
    setExplaining(false);
  }

  function next() {
    if (index + 1 >= total) {
      // Next step: POST /quiz-attempts/{id}/finish (#21) for the official score.
      setFinished(true);
      return;
    }
    setIndex(index + 1);
    setResult(null);
    setExplanation(null);
  }

  const correctText = result ? question.options.find((o) => o.id === result.correct_option_id)?.text : '';

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.topRow}>
        <Pressable onPress={() => router.back()} accessibilityRole="button" accessibilityLabel="ပိတ်မည်" style={styles.iconButton}>
          <CloseIcon color={colors.ink} />
        </Pressable>
        <QuizProgress current={index + (answered ? 1 : 0)} total={total} />
        <Text style={styles.count}>
          {index + 1} / {total}
        </Text>
      </View>

      <ScrollView contentContainerStyle={styles.body}>
        <View style={styles.typeChip}>
          <Text style={styles.typeText}>
            {typeMy} <Text style={styles.typeJa}>{typeJa}</Text>
          </Text>
        </View>
        <View style={styles.prompt}>
          <PromptText ruby={question.prompt_ruby} underline={question.underline} />
        </View>

        <View style={styles.options}>
          {question.options.map((option) => {
            const isCorrect = answered && option.id === result.correct_option_id;
            const isWrongPick = answered && option.id === result.selected_option_id && !result.is_correct;
            const faded = answered && !isCorrect && !isWrongPick;
            return (
              <Pressable
                key={option.id}
                onPress={() => choose(option.id)}
                disabled={answered}
                accessibilityRole="button"
                accessibilityState={{ disabled: answered, selected: isWrongPick || isCorrect }}
                style={[styles.option, isCorrect && styles.optionCorrect, isWrongPick && styles.optionWrong, faded && styles.optionFaded]}
              >
                <View style={[styles.badge, isCorrect && styles.badgeCorrect, isWrongPick && styles.badgeWrong]}>
                  {isCorrect ? <Mark kind="check" /> : isWrongPick ? <Mark kind="cross" /> : <Text style={styles.badgeText}>{option.id}</Text>}
                </View>
                <Text style={styles.optionText}>{option.text}</Text>
                {isCorrect && <Text style={[styles.optionTag, { color: colors.correct }]}>အဖြေမှန်</Text>}
                {isWrongPick && <Text style={[styles.optionTag, { color: colors.wrong }]}>သင့်အဖြေ</Text>}
              </Pressable>
            );
          })}
        </View>
      </ScrollView>

      {answered && (
        <View style={[styles.feedback, { borderTopColor: result.is_correct ? colors.correct : colors.wrong }]}>
          <View style={styles.feedbackRow}>
            <Text style={[styles.feedbackTitle, { color: result.is_correct ? colors.correct : colors.wrong }]}>
              {result.is_correct ? 'မှန်ပါတယ်' : 'မှားပါတယ်'}
            </Text>
            {!result.is_correct && (
              <Text style={styles.muted}>
                အဖြေမှန်: <Text style={styles.correctText}>{correctText}</Text>
              </Text>
            )}
          </View>

          {explanation ? (
            <View style={styles.explain}>
              <View style={styles.explainHead}>
                <SparkIcon color={colors.lacquer} />
                <Text style={styles.explainLabel}>ဘာကြောင့်လဲ</Text>
              </View>
              <Text style={styles.explainText}>{explanation.why_correct_my}</Text>
              {explanation.why_selected_wrong_my && <Text style={styles.explainText}>{explanation.why_selected_wrong_my}</Text>}
            </View>
          ) : (
            <Pressable onPress={why} disabled={explaining} style={styles.whyButton}>
              {explaining ? <ActivityIndicator color={colors.lacquer} /> : <SparkIcon color={colors.lacquer} />}
              <Text style={styles.whyText}>ဘာကြောင့်လဲ?</Text>
            </Pressable>
          )}

          <Pressable onPress={next} style={styles.primaryButton}>
            <Text style={styles.primaryText}>{index + 1 >= total ? 'ရလဒ် ကြည့်မည်' : 'ရှေ့ဆက်မည်'}</Text>
          </Pressable>
        </View>
      )}
    </SafeAreaView>
  );
}

function Mark({ kind }: { kind: 'check' | 'cross' }) {
  return (
    <Svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
      <Path d={kind === 'check' ? 'M5 12.5l4.5 4.5L19 7.5' : 'M6 6l12 12M18 6L6 18'} />
    </Svg>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
  },
  iconButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  count: {
    minWidth: 48,
    paddingBottom: 2,
    fontFamily: fonts.japaneseBold,
    fontSize: 14,
    textAlign: 'right',
    color: colors.ink,
  },
  body: {
    gap: spacing.lg,
    padding: 20,
    width: '100%',
    maxWidth: 560,
    alignSelf: 'center',
  },
  typeChip: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 2,
    borderRadius: 12,
    backgroundColor: colors.goldSoft,
  },
  typeText: {
    ...text.label,
    fontSize: 12,
    lineHeight: 21,
    color: '#7A5A12',
  },
  typeJa: {
    fontFamily: fonts.japanese,
  },
  prompt: {
    padding: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.divider,
    borderRadius: 14,
    backgroundColor: colors.surface,
  },
  options: {
    gap: 10,
  },
  option: {
    minHeight: 58,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    paddingHorizontal: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: 12,
    backgroundColor: colors.background,
  },
  optionCorrect: {
    borderWidth: 2,
    borderColor: colors.correct,
    backgroundColor: colors.correctBg,
  },
  optionWrong: {
    borderWidth: 2,
    borderColor: colors.wrong,
    backgroundColor: colors.wrongBg,
  },
  optionFaded: {
    opacity: 0.55,
  },
  badge: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.border,
  },
  badgeCorrect: {
    borderColor: colors.correct,
    backgroundColor: colors.correct,
  },
  badgeWrong: {
    borderColor: colors.wrong,
    backgroundColor: colors.wrong,
  },
  badgeText: {
    fontFamily: fonts.japaneseBold,
    fontSize: 14,
    color: colors.inkMuted,
  },
  optionText: {
    flex: 1,
    fontFamily: fonts.japanese,
    fontSize: 20,
    lineHeight: 30,
    color: colors.ink,
  },
  optionTag: {
    ...text.label,
    fontSize: 13,
  },
  feedback: {
    gap: spacing.md,
    paddingHorizontal: 20,
    paddingTop: spacing.lg,
    paddingBottom: spacing.lg,
    borderTopWidth: 3,
    backgroundColor: colors.background,
  },
  feedbackRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  feedbackTitle: {
    ...text.label,
    fontSize: 17,
    lineHeight: 30,
  },
  muted: {
    ...text.small,
    fontSize: 14,
    color: colors.inkMuted,
  },
  correctText: {
    fontFamily: fonts.japaneseBold,
    color: colors.ink,
  },
  explain: {
    gap: 6,
    padding: spacing.md,
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: 12,
    backgroundColor: colors.paper,
  },
  explainHead: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  explainLabel: {
    ...text.label,
    fontSize: 13,
    color: colors.lacquer,
  },
  explainText: {
    ...text.small,
    fontSize: 14,
    lineHeight: 25,
    color: colors.ink,
  },
  whyButton: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    height: 40,
    paddingHorizontal: 14,
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: 20,
    backgroundColor: colors.paper,
  },
  whyText: {
    ...text.label,
    color: colors.lacquer,
  },
  primaryButton: {
    height: 52,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.ink,
  },
  primaryText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 16,
    lineHeight: 28,
    color: colors.onInk,
  },
  secondaryButton: {
    height: 52,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.border,
  },
  secondaryText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 16,
    lineHeight: 28,
    color: colors.ink,
  },
  resultScreen: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    padding: spacing.xl,
    backgroundColor: colors.background,
  },
  resultTitle: {
    fontFamily: fonts.burmeseSerif,
    fontSize: 24,
    lineHeight: 42,
    color: colors.lacquer,
  },
  resultScore: {
    fontFamily: fonts.japaneseBold,
    fontSize: 56,
    lineHeight: 68,
    color: colors.ink,
  },
  resultButtons: {
    alignSelf: 'stretch',
    gap: spacing.md,
    marginTop: spacing.lg,
  },
});
