import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useFocusEffect } from 'expo-router';
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import { getSavedWords, moreExamples, saveWord, unsaveWord } from '@/api';
import type { Example, SavedWord } from '@/api/types';
import { getWordDetails } from '@/api/wordDetails';
import { CardFrame, LACQUER } from '@/components/saved/CardFrame';
import { MiniCard } from '@/components/saved/MiniCard';
import { type Details, SavedFlashCard } from '@/components/saved/SavedFlashCard';
import { BackIcon, FlipIcon, NextIcon, SparkIcon } from '@/components/ui/Icons';
import { Notice, useNotice } from '@/components/ui/Notice';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';
import { toMyanmarDigits } from '@/utils/myanmar';

const WEEK_MS = 7 * 24 * 60 * 60 * 1000;
type Mode = 'card' | 'grid';
type Filter = 'all' | 'week' | number; // a number = one session

// Saved words (#16 to #18) as traditional Burmese flash cards.
export default function SavedScreen() {
  const [words, setWords] = useState<SavedWord[] | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [mode, setMode] = useState<Mode>('card');
  const [filter, setFilter] = useState<Filter>('all');
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  // Removed words stay visible (so a mistake can be undone) until the list is loaded again.
  const [removed, setRemoved] = useState<Set<number>>(new Set());
  const [details, setDetails] = useState<Record<number, Details>>({});
  const [aiExamples, setAiExamples] = useState<Record<number, Example[]>>({});
  const [aiBusy, setAiBusy] = useState(false);
  const notice = useNotice();
  const firstSearch = useRef(true);

  const load = useCallback(async (query: string) => {
    setProblem(null);
    try {
      const data = await getSavedWords(query.trim() || undefined);
      setWords(data.words);
      setRemoved(new Set());
      setIndex(0);
      setFlipped(false);
    } catch (error) {
      setProblem(errorMessage(error));
    }
  }, []);

  // Start fresh whenever the tab comes into view (words may have been saved in a unit).
  useFocusEffect(
    useCallback(() => {
      setSearch('');
      setFilter('all');
      load('');
    }, [load]),
  );

  // Search as the user types, after a short pause (#16 ?search=).
  useEffect(() => {
    if (firstSearch.current) {
      firstSearch.current = false;
      return;
    }
    const timer = setTimeout(() => load(search), 350);
    return () => clearTimeout(timer);
  }, [search, load]);

  const sessions = useMemo(() => [...new Set((words ?? []).map((w) => w.session_number))].sort((a, b) => a - b), [words]);
  const shown = useMemo(() => {
    const all = words ?? [];
    if (filter === 'all') return all;
    if (filter === 'week') return all.filter((w) => Date.now() - new Date(w.saved_at).getTime() < WEEK_MS);
    return all.filter((w) => w.session_number === filter);
  }, [words, filter]);

  const current = shown[Math.min(index, Math.max(0, shown.length - 1))];

  // Load the full details (examples, definitions) when a card is turned over.
  const loadDetails = useCallback(async (word: SavedWord) => {
    setDetails((all) => ({ ...all, [word.word_id]: { state: 'loading' } }));
    try {
      const full = await getWordDetails(word);
      setDetails((all) => ({ ...all, [word.word_id]: { state: 'ready', word: full } }));
    } catch {
      setDetails((all) => ({ ...all, [word.word_id]: { state: 'error' } }));
    }
  }, []);

  function flip() {
    if (!current) return;
    if (!flipped && !details[current.word_id]) loadDetails(current);
    setFlipped(!flipped);
  }

  function go(step: number) {
    setFlipped(false);
    setIndex((i) => Math.min(Math.max(0, i + step), shown.length - 1));
  }

  function chooseFilter(next: Filter) {
    setFilter(next);
    setIndex(0);
    setFlipped(false);
  }

  function openCard(wordId: number) {
    setIndex(Math.max(0, shown.findIndex((w) => w.word_id === wordId)));
    setFlipped(false);
    setMode('card');
  }

  async function toggleSaved(word: SavedWord) {
    const wasRemoved = removed.has(word.word_id);
    const flipSet = (set: Set<number>) => {
      const next = new Set(set);
      if (next.has(word.word_id)) next.delete(word.word_id);
      else next.add(word.word_id);
      return next;
    };
    setRemoved(flipSet);
    try {
      if (wasRemoved) await saveWord(word.word_id);
      else await unsaveWord(word.word_id);
      notice.show(wasRemoved ? 'ပြန်သိမ်းပြီးပါပြီ' : 'သိမ်းထားသော စကားလုံးထဲက ဖယ်လိုက်ပါပြီ');
    } catch (error) {
      setRemoved(flipSet); // undo
      notice.show(errorMessage(error));
    }
  }

  // "More examples" (#27): 3 new AI sentences, added under the word's own examples.
  async function askMoreExamples(word: SavedWord) {
    setAiBusy(true);
    try {
      const result = await moreExamples('word', word.word_id);
      setAiExamples((all) => ({ ...all, [word.word_id]: [...(all[word.word_id] ?? []), ...result.examples] }));
      if (result.remaining_today <= 5) notice.show(`ယနေ့ ${toMyanmarDigits(result.remaining_today)} ကြိမ် ကျန်ပါတယ်`);
    } catch (error) {
      notice.show(errorMessage(error));
    } finally {
      setAiBusy(false);
    }
  }

  const searching = search.trim().length > 0;

  let body;
  if (problem) {
    body = <Text style={styles.message}>{problem}</Text>;
  } else if (!words) {
    body = <ActivityIndicator color={colors.ink} />;
  } else if (words.length === 0 && !searching) {
    body = (
      <View style={styles.emptyWrap}>
        <View style={styles.emptyCard}>
          <CardFrame>
            <View style={styles.emptyInner}>
              <Text style={styles.emptyTitle}>ကတ် မရှိသေးပါ</Text>
              <Text style={styles.emptyText}>ယူနစ်ထဲက ကတ်တွေမှာ စာညှပ် (bookmark) ကို နှိပ်ရင် ဒီမှာ ကတ်တစ်ချပ်အဖြစ် ရောက်လာပါမယ်။</Text>
            </View>
          </CardFrame>
        </View>
        <Pressable onPress={() => router.navigate('/home')} style={styles.darkButton}>
          <Text style={styles.darkButtonText}>လေ့လာမှုသို့ သွားမည်</Text>
        </Pressable>
      </View>
    );
  } else if (shown.length === 0) {
    body = <Text style={styles.message}>{searching ? `“${search.trim()}” ကို ရှာမတွေ့ပါ။` : 'ဒီအုပ်စုမှာ စကားလုံး မရှိပါ။'}</Text>;
  } else if (mode === 'grid') {
    body = (
      <View style={styles.grid}>
        {shown.map((w, i) =>
          i % 2 === 0 ? (
            <View key={w.word_id} style={styles.gridRow}>
              <MiniCard word={w} onPress={() => openCard(w.word_id)} />
              {shown[i + 1] ? <MiniCard word={shown[i + 1]} onPress={() => openCard(shown[i + 1].word_id)} /> : <View style={{ flex: 1 }} />}
            </View>
          ) : null,
        )}
      </View>
    );
  } else {
    const isRemoved = removed.has(current.word_id);
    body = (
      <View style={styles.cardArea}>
        <SavedFlashCard
          key={current.word_id}
          word={current}
          position={index + 1}
          total={shown.length}
          flipped={flipped}
          onFlip={flip}
          details={details[current.word_id] ?? { state: 'loading' }}
          aiExamples={aiExamples[current.word_id] ?? []}
          onRetry={() => loadDetails(current)}
        />

        {flipped && (
          <View style={styles.actions}>
            <Pressable onPress={() => askMoreExamples(current)} disabled={aiBusy} style={[styles.action, styles.aiAction]}>
              {aiBusy ? <ActivityIndicator color={LACQUER} /> : <SparkIcon color={LACQUER} />}
              <Text style={[styles.actionText, { color: LACQUER }]}>ဥပမာ ထပ်ကြည့်မည်</Text>
            </Pressable>
            <Pressable
              onPress={() => toggleSaved(current)}
              accessibilityState={{ selected: !isRemoved }}
              style={[styles.action, isRemoved && styles.removed]}
            >
              <Svg width={16} height={16} viewBox="0 0 24 24" fill={isRemoved ? 'none' : colors.gold} stroke={isRemoved ? colors.inkMuted : colors.goldDeep} strokeWidth={2} strokeLinejoin="round">
                <Path d="M6 3h12v18l-6-4.5L6 21z" />
              </Svg>
              <Text style={styles.actionText}>{isRemoved ? 'ပြန်သိမ်းမည်' : 'သိမ်းထားသည်'}</Text>
            </Pressable>
          </View>
        )}

        <View style={styles.nav}>
          <Pressable onPress={() => go(-1)} disabled={index === 0} accessibilityLabel="ရှေ့ကတ်" style={[styles.round, index === 0 && styles.disabled]}>
            <BackIcon color={colors.ink} size={20} />
          </Pressable>
          <Pressable onPress={flip} style={styles.flipButton}>
            <FlipIcon color={colors.ink} />
            <Text style={styles.actionText}>{flipped ? 'ရှေ့ဘက် ပြန်လှန်မည်' : 'လှန်ကြည့်မည်'}</Text>
          </Pressable>
          <Pressable
            onPress={() => go(1)}
            disabled={index >= shown.length - 1}
            accessibilityLabel="နောက်ကတ်"
            style={[styles.round, styles.roundDark, index >= shown.length - 1 && styles.disabled]}
          >
            <NextIcon color={colors.onInk} size={20} />
          </Pressable>
        </View>
      </View>
    );
  }

  const chip = (label: string, value: Filter) => {
    const on = filter === value;
    return (
      <Pressable key={String(value)} onPress={() => chooseFilter(value)} style={[styles.chip, on && styles.chipOn]}>
        <Text style={[styles.chipText, on && styles.chipTextOn]}>{label}</Text>
      </Pressable>
    );
  };

  return (
    <SafeAreaView style={styles.screen} edges={['top']}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Text style={styles.title}>
            မှတ်ထားသော စကားလုံး{' '}
            {words && <Text style={styles.count}>{toMyanmarDigits(words.length)}</Text>}
          </Text>
          <View style={styles.modes} accessibilityRole="tablist">
            <Pressable onPress={() => setMode('card')} accessibilityLabel="ကတ် တစ်ချပ်ချင်း" style={[styles.modeButton, mode === 'card' && styles.modeOn]}>
              <Svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke={mode === 'card' ? '#FFFFFF' : colors.inkMuted} strokeWidth={2}>
                <Rect x={6} y={3} width={12} height={18} rx={2.5} />
              </Svg>
            </Pressable>
            <Pressable onPress={() => setMode('grid')} accessibilityLabel="ကတ် အားလုံး" style={[styles.modeButton, mode === 'grid' && styles.modeOn]}>
              <Svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke={mode === 'grid' ? '#FFFFFF' : colors.inkMuted} strokeWidth={2}>
                <Rect x={4} y={4} width={6.5} height={6.5} rx={1.5} />
                <Rect x={13.5} y={4} width={6.5} height={6.5} rx={1.5} />
                <Rect x={4} y={13.5} width={6.5} height={6.5} rx={1.5} />
                <Rect x={13.5} y={13.5} width={6.5} height={6.5} rx={1.5} />
              </Svg>
            </Pressable>
          </View>
        </View>
        <View style={styles.searchBox}>
          <Svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke={colors.inkMuted} strokeWidth={2.2} strokeLinecap="round">
            <Circle cx={11} cy={11} r={7} />
            <Path d="M20 20l-3.5-3.5" />
          </Svg>
          <TextInput
            value={search}
            onChangeText={setSearch}
            placeholder="စကားလုံး ရှာမည်"
            placeholderTextColor={colors.inkMuted}
            autoCapitalize="none"
            autoCorrect={false}
            accessibilityLabel="စကားလုံး ရှာမည်"
            style={styles.searchInput}
          />
        </View>
        {words && words.length > 0 && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chips}>
            {chip(`အားလုံး ${toMyanmarDigits(words.length)}`, 'all')}
            {chip('ဒီအပတ်', 'week')}
            {sessions.map((n) => chip(`အပိုင်း ${toMyanmarDigits(n)}`, n))}
          </ScrollView>
        )}
      </View>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {body}
      </ScrollView>
      <Notice message={notice.message} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.goldSoft },
  header: { gap: 10, paddingHorizontal: 20, paddingTop: spacing.sm, paddingBottom: spacing.sm },
  titleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  title: { ...text.label, fontSize: 20, lineHeight: 34, color: colors.ink },
  count: { fontFamily: fonts.burmese, fontSize: 14, color: colors.inkMuted },
  modes: { flexDirection: 'row', gap: 2, padding: 3, borderRadius: 12, backgroundColor: '#F1E6D0' },
  modeButton: { width: 38, height: 32, alignItems: 'center', justifyContent: 'center', borderRadius: 9 },
  modeOn: { backgroundColor: colors.ink },
  searchBox: {
    height: 44,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: 14,
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: 22,
    backgroundColor: colors.background,
  },
  searchInput: { flex: 1, height: 42, fontFamily: fonts.burmese, fontSize: 15, color: colors.ink },
  chips: { gap: spacing.sm, paddingVertical: 2 },
  chip: { paddingHorizontal: 12, borderWidth: 1, borderColor: colors.paperEdge, borderRadius: 14, backgroundColor: colors.background },
  chipOn: { borderColor: colors.ink, backgroundColor: colors.ink },
  chipText: { ...text.small, fontSize: 12, lineHeight: 26, color: colors.inkMuted },
  chipTextOn: { color: colors.onInk, fontFamily: fonts.burmeseBold },
  content: { flexGrow: 1, justifyContent: 'center', paddingHorizontal: 20, paddingTop: spacing.lg, paddingBottom: spacing.xxl },
  message: { ...text.body, textAlign: 'center', color: colors.inkMuted },
  cardArea: { gap: 18, width: '100%', maxWidth: 400, alignSelf: 'center' },
  actions: { flexDirection: 'row', gap: 10 },
  action: {
    flex: 1,
    height: 46,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    borderWidth: 1.5,
    borderColor: colors.borderWarm,
    borderRadius: 23,
    backgroundColor: colors.background,
  },
  aiAction: { borderColor: colors.paperEdge, backgroundColor: '#FBF7EE' },
  removed: { borderStyle: 'dashed' },
  actionText: { ...text.label, fontSize: 14, color: colors.ink },
  nav: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  round: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.borderWarm,
    backgroundColor: colors.background,
  },
  roundDark: { borderColor: colors.ink, backgroundColor: colors.ink },
  disabled: { opacity: 0.35 },
  flipButton: {
    flex: 1,
    height: 52,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    borderWidth: 1.5,
    borderColor: colors.borderWarm,
    borderRadius: 26,
    backgroundColor: colors.background,
  },
  grid: { gap: 12, width: '100%', maxWidth: 520, alignSelf: 'center' },
  gridRow: { flexDirection: 'row', gap: 12 },
  emptyWrap: { alignItems: 'center', gap: spacing.xl },
  emptyCard: { width: 260, height: 300 },
  emptyInner: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.sm, paddingHorizontal: 30 },
  emptyTitle: { fontFamily: fonts.burmeseSerif, fontSize: 18, lineHeight: 38, color: LACQUER },
  emptyText: { ...text.small, fontSize: 13, lineHeight: 23, textAlign: 'center', color: colors.inkMuted },
  darkButton: { paddingHorizontal: spacing.xl, height: 50, justifyContent: 'center', borderRadius: radius.control, backgroundColor: colors.ink },
  darkButtonText: { fontFamily: fonts.burmeseBold, fontSize: 15, lineHeight: 26, color: colors.onInk },
});
