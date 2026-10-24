import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useFocusEffect } from 'expo-router';
import Svg, { Circle, Path } from 'react-native-svg';
import { getSavedWords, saveWord, unsaveWord } from '@/api';
import type { SavedWord } from '@/api/types';
import { ClosedNotebook, NotebookArea, OpenNotebook } from '@/components/saved/Notebook';
import { BackIcon, NextIcon } from '@/components/ui/Icons';
import { Notice, useNotice } from '@/components/ui/Notice';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';
import { toMyanmarDigits } from '@/utils/myanmar';

const WEEK_MS = 7 * 24 * 60 * 60 * 1000;

// Saved words (#16 to #18) as a traditional folding notebook.
export default function SavedScreen() {
  const [words, setWords] = useState<SavedWord[] | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const [index, setIndex] = useState(0);
  // Words removed while the book is open stay on their page (so a mistake can be undone)
  // until the list is loaded again.
  const [removed, setRemoved] = useState<Set<number>>(new Set());
  const notice = useNotice();
  const firstSearch = useRef(true);

  const load = useCallback(async (query: string) => {
    setProblem(null);
    try {
      const data = await getSavedWords(query.trim() || undefined);
      setWords(data.words);
      setRemoved(new Set());
      setIndex(0);
    } catch (error) {
      setProblem(errorMessage(error));
    }
  }, []);

  // Start fresh whenever the tab comes into view (words may have been saved in a unit).
  useFocusEffect(
    useCallback(() => {
      setOpen(false);
      setSearch('');
      load('');
    }, [load]),
  );

  // Search as the user types, after a short pause (#16 ?search=).
  useEffect(() => {
    if (firstSearch.current) {
      firstSearch.current = false;
      return;
    }
    const timer = setTimeout(() => {
      load(search).then(() => setOpen(search.trim().length > 0));
    }, 350);
    return () => clearTimeout(timer);
  }, [search, load]);

  async function toggleSaved(word: SavedWord) {
    const wasRemoved = removed.has(word.word_id);
    const flip = (current: Set<number>) => {
      const next = new Set(current);
      if (next.has(word.word_id)) next.delete(word.word_id);
      else next.add(word.word_id);
      return next;
    };
    setRemoved(flip);
    try {
      if (wasRemoved) await saveWord(word.word_id);
      else await unsaveWord(word.word_id);
      notice.show(wasRemoved ? 'မှတ်စုစာအုပ်ထဲ ပြန်သိမ်းပြီးပါပြီ' : 'မှတ်စုစာအုပ်ထဲက ဖယ်လိုက်ပါပြီ');
    } catch (error) {
      setRemoved(flip); // undo
      notice.show(errorMessage(error));
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
      <NotebookArea>
        <ClosedNotebook subtitle="ဗလာ" faded />
        <Text style={styles.emptyTitle}>မှတ်စုစာအုပ်ထဲမှာ စကားလုံး မရှိသေးပါ</Text>
        <Text style={styles.emptyText}>ယူနစ်ထဲက ကတ်တွေမှာ စာညှပ် (bookmark) ကို နှိပ်ရင် ဒီမှတ်စုစာအုပ်ထဲ ရောက်လာပါမယ်။</Text>
        <Pressable onPress={() => router.navigate('/home')} style={styles.darkButton}>
          <Text style={styles.darkButtonText}>လေ့လာမှုသို့ သွားမည်</Text>
        </Pressable>
      </NotebookArea>
    );
  } else if (words.length === 0) {
    body = <Text style={styles.message}>“{search.trim()}” ကို ရှာမတွေ့ပါ။</Text>;
  } else if (!open) {
    const thisWeek = words.filter((w) => Date.now() - new Date(w.saved_at).getTime() < WEEK_MS).length;
    const sessions = new Set(words.map((w) => w.session_number)).size;
    body = (
      <NotebookArea>
        <ClosedNotebook subtitle={`စကားလုံး ${toMyanmarDigits(words.length)} လုံး`} onPress={() => setOpen(true)} />
        <Text style={styles.hint}>မှတ်စုစာအုပ်ကို နှိပ်ပြီး ဖွင့်ပါ</Text>
        <View style={styles.stats}>
          <Stat value={words.length} label="စုစုပေါင်း" />
          <Stat value={thisWeek} label="ဒီအပတ်" />
          <Stat value={sessions} label="အပိုင်း" />
        </View>
      </NotebookArea>
    );
  } else {
    const word = words[Math.min(index, words.length - 1)];
    const isRemoved = removed.has(word.word_id);
    body = (
      <NotebookArea>
        <OpenNotebook word={word} position={index + 1} total={words.length} previous={words[index - 1]} next={words[index + 1]} />
        <View style={styles.controls}>
          <Pressable
            onPress={() => setIndex((i) => Math.max(0, i - 1))}
            disabled={index === 0}
            accessibilityRole="button"
            accessibilityLabel="ရှေ့စကားလုံး"
            style={[styles.round, index === 0 && styles.disabled]}
          >
            <BackIcon color={colors.ink} size={20} />
          </Pressable>
          <Pressable
            onPress={() => toggleSaved(word)}
            accessibilityRole="button"
            accessibilityState={{ selected: !isRemoved }}
            style={[styles.savedButton, isRemoved && styles.removed]}
          >
            <Svg width={16} height={16} viewBox="0 0 24 24" fill={isRemoved ? 'none' : colors.gold} stroke={isRemoved ? colors.inkMuted : colors.goldDeep} strokeWidth={2} strokeLinejoin="round">
              <Path d="M6 3h12v18l-6-4.5L6 21z" />
            </Svg>
            <Text style={styles.savedText}>{isRemoved ? 'ပြန်သိမ်းမည်' : 'သိမ်းထားသည်'}</Text>
          </Pressable>
          <Pressable
            onPress={() => setIndex((i) => Math.min(words.length - 1, i + 1))}
            disabled={index >= words.length - 1}
            accessibilityRole="button"
            accessibilityLabel="နောက်စကားလုံး"
            style={[styles.round, styles.roundDark, index >= words.length - 1 && styles.disabled]}
          >
            <NextIcon color={colors.onInk} size={20} />
          </Pressable>
        </View>
        <Pressable onPress={() => (searching ? setSearch('') : load('').then(() => setOpen(false)))}>
          <Text style={styles.closeLink}>{searching ? 'ရှာဖွေမှုကို ဖျက်မည်' : 'မှတ်စုစာအုပ်ကို ပိတ်မည်'}</Text>
        </Pressable>
      </NotebookArea>
    );
  }

  return (
    <SafeAreaView style={styles.screen} edges={['top']}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Text style={styles.title}>မှတ်ထားသော စကားလုံး</Text>
          {words && !searching && <Text style={styles.count}>{toMyanmarDigits(words.length)} လုံး</Text>}
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
      </View>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {body}
      </ScrollView>
      <Notice message={notice.message} />
    </SafeAreaView>
  );
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.goldSoft },
  header: { gap: 10, paddingHorizontal: 20, paddingTop: spacing.sm, paddingBottom: spacing.md },
  titleRow: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'space-between' },
  title: { ...text.label, fontSize: 20, lineHeight: 34, color: colors.ink },
  count: { ...text.small, fontSize: 14, color: colors.inkMuted },
  searchBox: {
    height: 46,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: 14,
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: 23,
    backgroundColor: colors.background,
  },
  searchInput: { flex: 1, height: 44, fontFamily: fonts.burmese, fontSize: 15, color: colors.ink },
  content: { flexGrow: 1, justifyContent: 'center', paddingHorizontal: 0, paddingVertical: spacing.xl },
  message: { ...text.body, textAlign: 'center', paddingHorizontal: spacing.xl, color: colors.inkMuted },
  hint: { ...text.small, color: colors.inkMuted },
  stats: { flexDirection: 'row', gap: spacing.sm, width: '100%', maxWidth: 350, paddingHorizontal: 20 },
  stat: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: 12,
    backgroundColor: colors.background,
  },
  statValue: { fontFamily: fonts.japaneseBold, fontSize: 18, lineHeight: 26, color: colors.ink },
  statLabel: { ...text.small, fontSize: 12, lineHeight: 21, color: colors.inkMuted },
  emptyTitle: { fontFamily: fonts.burmeseSerif, fontSize: 18, lineHeight: 38, color: colors.lacquer, textAlign: 'center' },
  emptyText: { ...text.small, fontSize: 14, lineHeight: 25, maxWidth: 320, textAlign: 'center', color: colors.inkMuted },
  darkButton: { paddingHorizontal: spacing.xl, height: 50, justifyContent: 'center', borderRadius: radius.control, backgroundColor: colors.ink },
  darkButtonText: { fontFamily: fonts.burmeseBold, fontSize: 15, lineHeight: 26, color: colors.onInk },
  controls: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, width: '100%', maxWidth: 390, paddingHorizontal: 20 },
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
  savedButton: {
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
  removed: { borderStyle: 'dashed' },
  savedText: { ...text.label, fontSize: 15, color: colors.ink },
  closeLink: { ...text.body, fontSize: 14, color: colors.inkMuted, textDecorationLine: 'underline' },
});
