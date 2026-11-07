import { useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import Svg, { Path, Rect } from 'react-native-svg';
import { ApiError, getMockResult, saveMockAnswer, startMockTest, submitMockTest } from '@/api';
import type { MockAttempt, MockPassage, MockQuestion, QuizOption } from '@/api/types';
import { MockIntro } from '@/components/mock/MockIntro';
import { QuestionList } from '@/components/mock/QuestionList';
import { SubmitDialog } from '@/components/mock/SubmitDialog';
import { TimerChip } from '@/components/mock/TimerChip';
import { useCountdown } from '@/components/mock/useCountdown';
import { PromptText } from '@/components/quiz/PromptText';
import { RubyText } from '@/components/RubyText';
import { Button } from '@/components/settings/SettingsUI';
import { BackIcon, CloseIcon, NextIcon } from '@/components/ui/Icons';
import { Notice, useNotice } from '@/components/ui/Notice';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';
import { toMyanmarDigits } from '@/utils/myanmar';

type Item = { question: MockQuestion; passage: MockPassage | null };

const LENGTH_LABEL: Record<MockPassage['length'], [string, string]> = {
  short: ['စာဖတ် (တို)', '読解・短文'],
  medium: ['စာဖတ် (အလယ်)', '読解・中文'],
  long: ['စာဖတ် (ရှည်)', '読解・長文'],
};

// The mock test (#23 to #25): rules first, then 51 questions in one strict, server-timed test.
export default function MockTestScreen() {
  const params = useLocalSearchParams<{ id: string; session?: string; status?: string; attempts?: string }>();
  const mockTestId = Number(params.id);
  const [attempt, setAttempt] = useState<MockAttempt | null>(null);
  const [answers, setAnswers] = useState<Record<number, QuizOption['id']>>({});
  const [flagged, setFlagged] = useState<Set<number>>(new Set());
  const [index, setIndex] = useState(0);
  const [listOpen, setListOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [leaveOpen, setLeaveOpen] = useState(false);
  const [starting, setStarting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const notice = useNotice();
  const finishing = useRef(false);

  // Every question in order: 45 language knowledge, then the reading questions with their passage.
  const items: Item[] = useMemo(() => {
    if (!attempt) return [];
    const [knowledge, reading] = attempt.sections;
    return [
      ...knowledge.questions.map((question) => ({ question, passage: null })),
      ...reading.passages.flatMap((passage) => passage.questions.map((question) => ({ question, passage }))),
    ];
  }, [attempt]);
  const readingFrom = attempt ? attempt.sections[0].questions.length : 0;

  const secondsLeft = useCountdown(attempt?.ends_at ?? null, attempt?.server_time ?? null);
  const answeredCount = items.filter((item) => answers[item.question.id]).length;

  // Open the result. Called after submitting, or when the server says time is up.
  function openResult(attemptId: number) {
    router.replace({ pathname: '/mock-result/[id]', params: { id: String(attemptId) } });
  }

  async function start() {
    setProblem(null);
    setStarting(true);
    try {
      const data = await startMockTest(mockTestId);
      setAttempt(data);
      setAnswers(Object.fromEntries(Object.entries(data.saved_answers).map(([qid, option]) => [Number(qid), option])));
      setIndex(0);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) setProblem('ဒီစမ်းသပ်စာမေးပွဲမှာ မေးခွန်းတွေ မထည့်ရသေးပါ။');
      else setProblem(errorMessage(error));
    } finally {
      setStarting(false);
    }
  }

  async function submit() {
    if (!attempt || finishing.current) return;
    finishing.current = true;
    setSubmitting(true);
    try {
      await submitMockTest(attempt.attempt_id);
      openResult(attempt.attempt_id);
    } catch (error) {
      if (error instanceof ApiError && error.code === 'already_submitted') {
        openResult(attempt.attempt_id);
        return;
      }
      finishing.current = false;
      setSubmitting(false);
      setConfirmOpen(false);
      notice.show(errorMessage(error));
    }
  }

  // Time is up: the server submits with the answers saved so far (#25 returns that result).
  useEffect(() => {
    if (secondsLeft === 0 && attempt && !finishing.current) submit();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [secondsLeft, attempt]);

  // #24: save straight away. If saving fails, the choice goes back to what it was.
  async function choose(questionId: number, option: QuizOption['id']) {
    if (!attempt || finishing.current) return;
    const before = answers[questionId];
    setAnswers((all) => ({ ...all, [questionId]: option }));
    try {
      await saveMockAnswer(attempt.attempt_id, questionId, option);
    } catch (error) {
      if (error instanceof ApiError && error.code === 'attempt_finished') {
        // Time ran out on the server: the test is already submitted.
        getMockResult(attempt.attempt_id)
          .then(() => openResult(attempt.attempt_id))
          .catch(() => submit());
        return;
      }
      setAnswers((all) => {
        const next = { ...all };
        if (before) next[questionId] = before;
        else delete next[questionId];
        return next;
      });
      notice.show(errorMessage(error));
    }
  }

  function toggleFlag(questionId: number) {
    setFlagged((current) => {
      const next = new Set(current);
      if (next.has(questionId)) next.delete(questionId);
      else next.add(questionId);
      return next;
    });
  }

  // ---------- before the test: rules ----------
  if (!attempt) {
    const attempts = Number(params.attempts ?? 0);
    return (
      <SafeAreaView style={styles.introScreen}>
        <Pressable onPress={() => router.back()} accessibilityRole="button" accessibilityLabel="နောက်သို့" style={styles.introBack}>
          <BackIcon color={colors.ink} />
        </Pressable>
        <MockIntro
          sessionNumber={params.session ? Number(params.session) : null}
          resuming={params.status === 'in_progress'}
          retake={attempts > 0 && params.status !== 'in_progress'}
          busy={starting}
          problem={problem}
          onStart={start}
        />
      </SafeAreaView>
    );
  }

  if (items.length === 0 || secondsLeft === null) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator color={colors.ink} />
      </SafeAreaView>
    );
  }

  const item = items[Math.min(index, items.length - 1)];
  const { question, passage } = item;
  const isLast = index >= items.length - 1;
  const isFlagged = flagged.has(question.id);

  return (
    <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
      {/* Top bar: leave, timer, question number */}
      <View style={styles.topBar}>
        <Pressable onPress={() => setLeaveOpen(true)} accessibilityRole="button" accessibilityLabel="ထွက်မည်" style={styles.iconButton}>
          <CloseIcon color={colors.ink} />
        </Pressable>
        <TimerChip seconds={secondsLeft} />
        <View style={styles.counter}>
          <Text style={styles.counterMain}>
            {index + 1} / {items.length}
          </Text>
          <Text style={styles.counterSub}>ဖြေပြီး {toMyanmarDigits(answeredCount)}</Text>
        </View>
      </View>
      <View style={styles.track}>
        <View style={[styles.trackFill, { width: `${(answeredCount / items.length) * 100}%` }]} />
      </View>

      <ScrollView contentContainerStyle={styles.body} keyboardShouldPersistTaps="handled">
        {passage && (
          <>
            <View style={styles.sectionChip}>
              <Text style={styles.sectionChipText}>
                {LENGTH_LABEL[passage.length][0]} <Text style={styles.ja}>{LENGTH_LABEL[passage.length][1]}</Text>
              </Text>
            </View>
            {secondsLeft < 5 * 60 && (
              <View style={styles.warnBox} accessibilityRole="alert">
                <Text style={styles.warnText}>၅ မိနစ်အောက် ကျန်ပါပြီ</Text>
              </View>
            )}
            <View style={styles.passage}>
              <ScrollView nestedScrollEnabled contentContainerStyle={styles.passageInner}>
                <RubyText ruby={passage.text_ruby} size={16} align="left" />
              </ScrollView>
            </View>
          </>
        )}

        <View style={styles.questionHead}>
          <Text style={styles.questionNumber}>問 {question.number}</Text>
        </View>
        <View style={styles.prompt}>
          <PromptText ruby={question.prompt_ruby} underline={question.underline} />
        </View>

        <View accessibilityRole="radiogroup" style={styles.options}>
          {question.options.map((option) => {
            const selected = answers[question.id] === option.id;
            return (
              <Pressable
                key={option.id}
                onPress={() => choose(question.id, option.id)}
                accessibilityRole="radio"
                accessibilityState={{ checked: selected }}
                style={[styles.option, selected && styles.optionSelected]}
              >
                <View style={[styles.badge, selected && styles.badgeSelected]}>
                  <Text style={[styles.badgeText, selected && styles.badgeTextSelected]}>{option.id}</Text>
                </View>
                <Text style={[styles.optionText, passage && styles.optionTextSmall]}>{option.text}</Text>
              </Pressable>
            );
          })}
        </View>
        <Text style={styles.changeNote}>အဖြေကို အချိန်မကုန်ခင် ပြောင်းနိုင်ပါတယ်</Text>
      </ScrollView>

      {/* Bottom: previous, question list, next; flag for later */}
      <View style={styles.bottom}>
        <View style={styles.navRow}>
          <Pressable
            onPress={() => setIndex((i) => Math.max(0, i - 1))}
            disabled={index === 0}
            accessibilityLabel="ရှေ့မေးခွန်း"
            style={[styles.round, index === 0 && styles.disabled]}
          >
            <BackIcon color={colors.ink} size={20} />
          </Pressable>
          <Pressable onPress={() => setListOpen(true)} style={styles.listButton}>
            <Svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke={colors.ink} strokeWidth={2}>
              <Rect x={4} y={4} width={6} height={6} rx={1.5} />
              <Rect x={14} y={4} width={6} height={6} rx={1.5} />
              <Rect x={4} y={14} width={6} height={6} rx={1.5} />
              <Rect x={14} y={14} width={6} height={6} rx={1.5} />
            </Svg>
            <Text style={styles.listText}>မေးခွန်းစာရင်း</Text>
          </Pressable>
          <Pressable
            onPress={() => (isLast ? setConfirmOpen(true) : setIndex((i) => i + 1))}
            accessibilityLabel={isLast ? 'တင်သွင်းမည်' : 'နောက်မေးခွန်း'}
            style={[styles.round, styles.roundDark]}
          >
            <NextIcon color={colors.onInk} size={20} />
          </Pressable>
        </View>
        <Pressable
          onPress={() => toggleFlag(question.id)}
          accessibilityRole="checkbox"
          accessibilityState={{ checked: isFlagged }}
          style={[styles.flag, isFlagged && styles.flagOn]}
        >
          <Svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke={isFlagged ? '#7A5A12' : colors.inkMuted} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <Path d="M5 21V4M5 4h11l-2 4 2 4H5" />
          </Svg>
          <Text style={[styles.flagText, isFlagged && { color: '#7A5A12' }]}>နောက်မှ ပြန်ကြည့်မည်</Text>
        </Pressable>
      </View>

      <QuestionList
        visible={listOpen}
        total={items.length}
        readingFrom={readingFrom}
        current={index}
        answered={(i) => Boolean(answers[items[i].question.id])}
        flagged={(i) => flagged.has(items[i].question.id)}
        onJump={(i) => {
          setIndex(i);
          setListOpen(false);
        }}
        onSubmit={() => {
          setListOpen(false);
          setConfirmOpen(true);
        }}
        onClose={() => setListOpen(false)}
      />

      <SubmitDialog
        visible={confirmOpen}
        answered={answeredCount}
        total={items.length}
        secondsLeft={secondsLeft}
        busy={submitting}
        onSubmit={submit}
        onCancel={() => setConfirmOpen(false)}
      />

      {/* Leaving: the clock keeps running on the server, so warn first. */}
      <Modal visible={leaveOpen} transparent animationType="fade" onRequestClose={() => setLeaveOpen(false)}>
        <View style={styles.leaveBackdrop}>
          <View style={styles.leaveDialog}>
            <Text style={styles.leaveTitle}>ခဏ ထွက်မလား</Text>
            <Text style={styles.leaveText}>
              ဖြေထားတာတွေ သိမ်းထားပါတယ်။ ဒါပေမဲ့ အချိန်က ဆက်သွားနေပါမယ်။ မြေပုံကနေ ပြန်ဝင်ပြီး ဆက်ဖြေနိုင်ပါတယ်။
            </Text>
            <Button label="ဆက်ဖြေမည်" onPress={() => setLeaveOpen(false)} />
            <Button label="ထွက်မည်" kind="secondary" onPress={() => router.back()} />
          </View>
        </View>
      </Modal>

      <Notice message={notice.message} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  introScreen: { flex: 1, backgroundColor: colors.goldSoft },
  introBack: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center', marginLeft: spacing.sm },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  screen: { flex: 1, backgroundColor: colors.background },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.sm,
    paddingHorizontal: 14,
    paddingVertical: spacing.sm,
  },
  iconButton: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center' },
  counter: { alignItems: 'flex-end' },
  counterMain: { fontFamily: fonts.japaneseBold, fontSize: 15, color: colors.ink },
  counterSub: { ...text.small, fontSize: 11, lineHeight: 19, color: colors.inkMuted },
  track: { height: 4, backgroundColor: colors.track },
  trackFill: { height: 4, backgroundColor: colors.gold },
  body: { gap: 12, padding: 18, paddingBottom: spacing.xl, width: '100%', maxWidth: 640, alignSelf: 'center' },
  sectionChip: { alignSelf: 'flex-start', paddingHorizontal: 10, borderRadius: 12, backgroundColor: colors.goldSoft },
  sectionChipText: { ...text.label, fontSize: 12, lineHeight: 22, color: '#7A5A12' },
  ja: { fontFamily: fonts.japanese },
  warnBox: { padding: spacing.sm, paddingHorizontal: spacing.md, borderRadius: 10, backgroundColor: colors.wrongBg },
  warnText: { ...text.label, fontSize: 13, color: colors.wrong },
  passage: { height: 260, borderWidth: 1.5, borderColor: colors.paperEdge, borderRadius: 14, backgroundColor: '#FFFDF7' },
  passageInner: { padding: 14 },
  questionHead: { flexDirection: 'row', justifyContent: 'flex-end' },
  questionNumber: { fontFamily: fonts.japaneseBold, fontSize: 13, color: colors.inkMuted },
  prompt: { padding: spacing.lg, borderWidth: 1.5, borderColor: colors.divider, borderRadius: 14, backgroundColor: colors.surface },
  options: { gap: 10 },
  option: {
    minHeight: 54,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: 12,
    backgroundColor: colors.background,
  },
  optionSelected: { borderWidth: 2, borderColor: colors.ink, backgroundColor: colors.goldSoft },
  badge: {
    width: 30,
    height: 30,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: 15,
  },
  badgeSelected: { borderColor: colors.ink, backgroundColor: colors.ink },
  badgeText: { fontFamily: fonts.japaneseBold, fontSize: 14, color: colors.inkMuted },
  badgeTextSelected: { color: colors.onInk },
  optionText: { flex: 1, fontFamily: fonts.japanese, fontSize: 18, lineHeight: 28, color: colors.ink },
  optionTextSmall: { fontSize: 15, lineHeight: 24 },
  changeNote: { ...text.small, fontSize: 12, textAlign: 'center', color: colors.inkMuted },
  bottom: { gap: 10, paddingHorizontal: spacing.lg, paddingTop: spacing.md, paddingBottom: spacing.sm, borderTopWidth: 1, borderTopColor: colors.divider },
  navRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  round: {
    width: 52,
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: 26,
  },
  roundDark: { borderColor: colors.ink, backgroundColor: colors.ink },
  disabled: { opacity: 0.35 },
  listButton: {
    flex: 1,
    height: 52,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: 26,
  },
  listText: { ...text.label, fontSize: 15, color: colors.ink },
  flag: {
    alignSelf: 'center',
    height: 34,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: 17,
  },
  flagOn: { borderColor: colors.goldDeep, backgroundColor: colors.goldSoft },
  flagText: { ...text.label, fontSize: 13, color: colors.inkMuted },
  leaveBackdrop: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 22, backgroundColor: 'rgba(42,37,34,0.45)' },
  leaveDialog: { width: '100%', maxWidth: 400, gap: spacing.md, padding: 20, borderRadius: radius.card + 4, backgroundColor: colors.background },
  leaveTitle: { fontFamily: fonts.burmeseSerif, fontSize: 19, lineHeight: 40, color: colors.lacquer, textAlign: 'center' },
  leaveText: { ...text.small, fontSize: 14, lineHeight: 25, textAlign: 'center', color: colors.inkMuted },
});
