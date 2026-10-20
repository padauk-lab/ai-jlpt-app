import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import Svg, { Path } from 'react-native-svg';
import { explainAnswer, getQuizReview } from '@/api';
import type { Explanation, QuizReview, QuizReviewQuestion } from '@/api/types';
import { PromptText } from '@/components/quiz/PromptText';
import { BackIcon, SparkIcon } from '@/components/ui/Icons';
import { colors, fonts, spacing, text } from '@/theme';

type Filter = 'all' | 'wrong';

// Quiz review (#22): every question with the user's answer and the correct one.
export default function ReviewScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [review, setReview] = useState<QuizReview | null>(null);
  const [filter, setFilter] = useState<Filter>('all');

  useEffect(() => {
    getQuizReview(Number(id)).then((data) => {
      setReview(data);
      // Coming from "review my mistakes": start on the wrong ones if there are any.
      if (!data.passed && data.questions.some((q) => !q.is_correct)) setFilter('wrong');
    });
  }, [id]);

  if (!review) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator color={colors.ink} />
      </SafeAreaView>
    );
  }

  const wrongCount = review.questions.filter((q) => !q.is_correct).length;
  const shown = filter === 'all' ? review.questions : review.questions.filter((q) => !q.is_correct);

  return (
    <SafeAreaView style={styles.screen} edges={['top']}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Pressable onPress={() => router.back()} accessibilityRole="button" accessibilityLabel="နောက်သို့" style={styles.iconButton}>
            <BackIcon color={colors.ink} />
          </Pressable>
          <View>
            <Text style={styles.title}>အဖြေများ ပြန်ကြည့်ရန်</Text>
            <Text style={styles.subtitle}>စာမေးပွဲငယ် ၊ {review.score}%</Text>
          </View>
        </View>
        <View style={styles.tabs} accessibilityRole="tablist">
          <Tab label={`အားလုံး ${review.questions.length}`} active={filter === 'all'} onPress={() => setFilter('all')} />
          <Tab label={`မှားခဲ့သည် ${wrongCount}`} active={filter === 'wrong'} onPress={() => setFilter('wrong')} />
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.list}>
        {shown.length === 0 ? (
          <Text style={styles.empty}>မှားခဲ့တာ မရှိပါဘူး။ အားလုံး မှန်ပါတယ်။</Text>
        ) : (
          shown.map((question) => <QuestionCard key={question.id} question={question} />)
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function QuestionCard({ question }: { question: QuizReviewQuestion }) {
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [loading, setLoading] = useState(false);
  const optionText = (optionId: string | null) => question.options.find((o) => o.id === optionId)?.text ?? '—';

  async function why() {
    setLoading(true);
    setExplanation(await explainAnswer(question.id, question.selected_option_id ?? question.correct_option_id));
    setLoading(false);
  }

  return (
    <View style={styles.card}>
      <View style={styles.cardTop}>
        <Text style={styles.qNumber}>Q{question.number}</Text>
        <Text style={[styles.status, { color: question.is_correct ? colors.correct : colors.wrong }]}>
          {question.is_correct ? 'မှန်' : 'မှား'}
        </Text>
      </View>
      <PromptText ruby={question.prompt_ruby} />

      {!question.is_correct && <AnswerRow kind="wrong" label={question.selected_option_id ? 'သင့်အဖြေ' : 'မဖြေခဲ့ပါ'} value={optionText(question.selected_option_id)} />}
      <AnswerRow kind="right" label={question.is_correct ? 'သင့်အဖြေ' : 'အဖြေမှန်'} value={optionText(question.correct_option_id)} />

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
        <Pressable onPress={why} disabled={loading} style={styles.whyButton}>
          {loading ? <ActivityIndicator color={colors.lacquer} /> : <SparkIcon color={colors.lacquer} />}
          <Text style={styles.whyText}>ဘာကြောင့်လဲ?</Text>
        </Pressable>
      )}
    </View>
  );
}

function AnswerRow({ kind, label, value }: { kind: 'right' | 'wrong'; label: string; value: string }) {
  const color = kind === 'right' ? colors.correct : colors.wrong;
  return (
    <View style={[styles.answer, { backgroundColor: kind === 'right' ? colors.correctBg : colors.wrongBg }]}>
      <View style={[styles.answerIcon, { backgroundColor: color }]}>
        <Svg width={12} height={12} viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth={3.2} strokeLinecap="round" strokeLinejoin="round">
          <Path d={kind === 'right' ? 'M5 12.5l4.5 4.5L19 7.5' : 'M6 6l12 12M18 6L6 18'} />
        </Svg>
      </View>
      <Text style={styles.answerText}>{value}</Text>
      <Text style={[styles.answerLabel, { color }]}>{label}</Text>
    </View>
  );
}

function Tab({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} accessibilityRole="tab" accessibilityState={{ selected: active }} style={[styles.tab, active && styles.tabActive]}>
      <Text style={[styles.tabText, active && styles.tabTextActive]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.surface,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  header: {
    paddingHorizontal: spacing.md,
    borderBottomWidth: 1.5,
    borderBottomColor: colors.divider,
    backgroundColor: colors.background,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  iconButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    ...text.label,
    fontSize: 17,
    lineHeight: 30,
    color: colors.ink,
  },
  subtitle: {
    ...text.small,
    fontSize: 12,
    lineHeight: 20,
    color: colors.inkMuted,
  },
  tabs: {
    flexDirection: 'row',
    marginTop: spacing.xs,
  },
  tab: {
    flex: 1,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderBottomWidth: 3,
    borderBottomColor: 'transparent',
    marginBottom: -1.5,
  },
  tabActive: {
    borderBottomColor: colors.ink,
  },
  tabText: {
    ...text.body,
    fontSize: 15,
    color: colors.inkMuted,
  },
  tabTextActive: {
    fontFamily: fonts.burmeseBold,
    color: colors.ink,
  },
  list: {
    gap: spacing.md,
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
    width: '100%',
    maxWidth: 560,
    alignSelf: 'center',
  },
  empty: {
    ...text.body,
    marginTop: spacing.xl,
    textAlign: 'center',
    color: colors.inkMuted,
  },
  card: {
    gap: 10,
    padding: 14,
    borderWidth: 1.5,
    borderColor: colors.divider,
    borderRadius: 14,
    backgroundColor: colors.background,
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  qNumber: {
    fontFamily: fonts.japaneseBold,
    fontSize: 13,
    color: colors.inkMuted,
  },
  status: {
    ...text.label,
    fontSize: 12,
  },
  answer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 10,
  },
  answerIcon: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  answerText: {
    flex: 1,
    fontFamily: fonts.japanese,
    fontSize: 17,
    lineHeight: 26,
    color: colors.ink,
  },
  answerLabel: {
    ...text.label,
    fontSize: 12,
  },
  explain: {
    gap: 4,
    padding: spacing.md,
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: 10,
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
    height: 36,
    paddingHorizontal: spacing.md,
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: 18,
    backgroundColor: colors.paper,
  },
  whyText: {
    ...text.label,
    fontSize: 13,
    color: colors.lacquer,
  },
});
