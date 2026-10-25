import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import { completeUnit, getUnit, saveWord, unsaveWord } from '@/api';
import type { UnitDetail } from '@/api/types';
import { OrnateFrame } from '@/components/OrnateFrame';
import { BackIcon, NextIcon } from '@/components/ui/Icons';
import Svg, { Path } from 'react-native-svg';
import { Notice, useNotice } from '@/components/ui/Notice';
import { FlipCard } from '@/components/unit/FlipCard';
import { GrammarCard } from '@/components/unit/GrammarCard';
import { colors, fonts, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';
import { toMyanmarDigits } from '@/utils/myanmar';

type Tab = 'words' | 'grammar';

export default function UnitScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [unit, setUnit] = useState<UnitDetail | null>(null);
  const [tab, setTab] = useState<Tab>('words');
  const [index, setIndex] = useState(0);
  const [saved, setSaved] = useState<Set<number>>(new Set());
  // Which words (and the grammar) the user has marked "studied". Kept only while the
  // screen is open: if the app closes, the marks start again (no backend change).
  const [studied, setStudied] = useState<Set<number>>(new Set());
  const [grammarStudied, setGrammarStudied] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const notice = useNotice();

  useEffect(() => {
    // Start fresh for each unit (going from Unit 5 straight to Unit 6 reuses this screen).
    setUnit(null);
    setLoadError(null);
    setTab('words');
    setIndex(0);
    setFinishing(false);
    getUnit(Number(id))
      .then((data) => {
        setUnit(data);
        setSaved(new Set(data.words.filter((w) => w.bookmarked).map((w) => w.id)));
        // A finished unit is open for review: everything counts as studied.
        const done = data.status === 'completed';
        setStudied(new Set(done ? data.words.map((w) => w.id) : []));
        setGrammarStudied(done);
      })
      .catch((error) => setLoadError(errorMessage(error)));
  }, [id]);

  if (!unit) {
    return (
      <SafeAreaView style={styles.center}>
        {loadError ? (
          <>
            <Text style={styles.muted}>{loadError}</Text>
            <Pressable onPress={() => router.back()} style={styles.backLink}>
              <Text style={styles.backLinkText}>နောက်သို့</Text>
            </Pressable>
          </>
        ) : (
          <ActivityIndicator color={colors.ink} />
        )}
      </SafeAreaView>
    );
  }

  if (unit.words.length === 0) {
    return (
      <SafeAreaView style={styles.center}>
        <Text style={styles.muted}>ဒီယူနစ်ရဲ့ စကားလုံးတွေ မထည့်ရသေးပါ။</Text>
        <Pressable onPress={() => router.back()} style={styles.backLink}>
          <Text style={styles.backLinkText}>နောက်သို့</Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  const word = unit.words[index];
  const total = unit.words.length;

  // #17 save / #18 remove. The star changes at once; if the server says no, it changes back.
  async function toggleSaved(wordId: number) {
    const wasSaved = saved.has(wordId);
    const flip = (current: Set<number>) => {
      const next = new Set(current);
      if (next.has(wordId)) next.delete(wordId);
      else next.add(wordId);
      return next;
    };
    setSaved(flip);
    try {
      if (wasSaved) await unsaveWord(wordId);
      else await saveWord(wordId);
      if (!wasSaved) notice.show('မှတ်စုစာအုပ်ထဲ သိမ်းပြီးပါပြီ');
    } catch (error) {
      setSaved(flip); // undo
      notice.show(errorMessage(error));
    }
  }

  function toggleStudied(wordId: number) {
    setStudied((current) => {
      const next = new Set(current);
      if (next.has(wordId)) next.delete(wordId);
      else next.add(wordId);
      return next;
    });
  }

  const isCompleted = unit.status === 'completed';
  const studiedCount = unit.words.filter((w) => studied.has(w.id)).length;
  const grammarDone = !unit.grammar || grammarStudied; // no grammar loaded yet: nothing to mark
  const ready = studiedCount === total && grammarDone;

  // #15 Mark as done, then go straight to what the backend says comes next.
  async function markDone() {
    if (!unit || !ready) return;
    setFinishing(true);
    try {
      const result = await completeUnit(unit.id);
      const next = result.next;
      if (next?.type === 'unit') {
        router.replace({ pathname: '/unit/[id]', params: { id: String(next.id) } });
      } else if (next?.type === 'quiz') {
        router.replace({ pathname: '/quiz/[id]', params: { id: String(next.id) } });
      } else {
        router.back(); // mock test (screen not built yet) or nothing next: back to the map
      }
    } catch (error) {
      setFinishing(false);
      notice.show(errorMessage(error));
    }
  }

  const showMoreExamples = () => notice.show('AI ဥပမာများ မကြာမီ ရပါမယ်');

  return (
    <SafeAreaView style={styles.screen} edges={['top']}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Pressable onPress={() => router.back()} accessibilityRole="button" accessibilityLabel="နောက်သို့" style={styles.iconButton}>
            <BackIcon color={colors.ink} />
          </Pressable>
          <OrnateFrame label={`ယူနစ် ${toMyanmarDigits(unit.number)}`} width={180} />
          <Text numberOfLines={1} style={styles.sessionLabel}>
            အပိုင်း {toMyanmarDigits(unit.session_number)}
          </Text>
        </View>
        <View style={styles.tabs} accessibilityRole="tablist">
          <TabButton
            label="ဝေါဟာရ"
            count={`${toMyanmarDigits(studiedCount)}/${toMyanmarDigits(total)}`}
            active={tab === 'words'}
            onPress={() => setTab('words')}
          />
          {unit.grammar && (
            <TabButton label="သဒ္ဒါ" count={grammarStudied ? '✓' : '—'} active={tab === 'grammar'} onPress={() => setTab('grammar')} />
          )}
        </View>
      </View>

      {tab === 'words' ? (
        <ScrollView contentContainerStyle={styles.body}>
          <View style={styles.counterRow}>
            <Text style={styles.counter}>
              {index + 1} <Text style={styles.counterTotal}>/ {total}</Text>
            </Text>
            <Text style={styles.muted}>
              လေ့လာပြီး {toMyanmarDigits(studiedCount)}/{toMyanmarDigits(total)}
            </Text>
          </View>
          <View style={styles.track}>
            <View style={[styles.fill, { width: `${((index + 1) / total) * 100}%` }]} />
          </View>

          <FlipCard
            key={word.id}
            word={word}
            saved={saved.has(word.id)}
            studied={studied.has(word.id)}
            onToggleSaved={() => toggleSaved(word.id)}
            onMoreExamples={showMoreExamples}
          />

          <View style={styles.navRow}>
            <Pressable
              onPress={() => setIndex((i) => Math.max(0, i - 1))}
              disabled={index === 0}
              accessibilityRole="button"
              accessibilityLabel="ရှေ့ကတ်"
              style={[styles.round, index === 0 && styles.disabled]}
            >
              <BackIcon color={colors.ink} size={20} />
            </Pressable>
            <StudiedButton on={studied.has(word.id)} onPress={() => toggleStudied(word.id)} />
            <Pressable
              onPress={() => setIndex((i) => Math.min(total - 1, i + 1))}
              disabled={index === total - 1}
              accessibilityRole="button"
              accessibilityLabel="နောက်ကတ်"
              style={[styles.round, styles.roundDark, index === total - 1 && styles.disabled]}
            >
              <NextIcon color={colors.onInk} size={20} />
            </Pressable>
          </View>
        </ScrollView>
      ) : (
        <ScrollView contentContainerStyle={styles.body}>
          {unit.grammar && (
            <>
              <GrammarCard grammar={unit.grammar} onMoreExamples={showMoreExamples} />
              <StudiedButton on={grammarStudied} onPress={() => setGrammarStudied((on) => !on)} label="သဒ္ဒါ လေ့လာပြီး" />
            </>
          )}
        </ScrollView>
      )}

      <Notice message={notice.message} />

      <SafeAreaView edges={['bottom']} style={styles.doneBar}>
        {isCompleted ? (
          <>
            <Text style={styles.doneNote}>ပြီးဆုံးပြီးသော ယူနစ် ၊ စိတ်ကြိုက် ပြန်လေ့လာနိုင်ပါတယ်</Text>
            <Pressable onPress={() => router.back()} style={({ pressed }) => [styles.doneButton, pressed && { opacity: 0.85 }]}>
              <Text style={styles.doneText}>မြေပုံသို့ ပြန်မည်</Text>
            </Pressable>
          </>
        ) : (
          <>
            <View style={styles.doneProgress}>
              <Text style={[styles.doneStep, studiedCount === total && styles.doneStepOn]}>
                စကားလုံး {toMyanmarDigits(studiedCount)}/{toMyanmarDigits(total)}
              </Text>
              {unit.grammar && <Text style={[styles.doneStep, grammarStudied && styles.doneStepOn]}>+ သဒ္ဒါ {grammarStudied ? '✓' : ''}</Text>}
            </View>
            <Pressable
              onPress={markDone}
              disabled={!ready || finishing}
              accessibilityRole="button"
              accessibilityState={{ disabled: !ready || finishing }}
              accessibilityHint={ready ? undefined : 'စကားလုံးနဲ့ သဒ္ဒါ အားလုံး လေ့လာပြီးမှ နှိပ်လို့ရပါမယ်'}
              style={({ pressed }) => [styles.doneButton, !ready && styles.disabled, (pressed || finishing) && { opacity: 0.85 }]}
            >
              <Text style={styles.doneText}>{finishing ? '…' : 'ယူနစ် ပြီးပါပြီ'}</Text>
            </Pressable>
            {!ready && <Text style={styles.doneHint}>စကားလုံးနဲ့ သဒ္ဒါ အားလုံးကို "လေ့လာပြီး" လို့ မှတ်ပြီးမှ နှိပ်လို့ရပါမယ်</Text>}
          </>
        )}
      </SafeAreaView>
    </SafeAreaView>
  );
}

// "Studied" (လေ့လာပြီး): tap to mark, tap again to unmark.
function StudiedButton({ on, onPress, label = 'လေ့လာပြီး' }: { on: boolean; onPress: () => void; label?: string }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="checkbox"
      accessibilityState={{ checked: on }}
      style={[styles.studiedButton, on && styles.studiedOn]}
    >
      <View style={[styles.studiedCheck, on && styles.studiedCheckOn]}>
        {on && (
          <Svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke={colors.ink} strokeWidth={3.2} strokeLinecap="round" strokeLinejoin="round">
            <Path d="M5 12.5l4.5 4.5L19 7.5" />
          </Svg>
        )}
      </View>
      <Text style={[styles.studiedText, on && styles.studiedTextOn]}>{label}</Text>
    </Pressable>
  );
}

function TabButton({ label, count, active, onPress }: { label: string; count: string; active: boolean; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="tab"
      accessibilityState={{ selected: active }}
      style={[styles.tab, active && styles.tabActive]}
    >
      <Text style={[styles.tabText, active && styles.tabTextActive]}>
        {label} <Text style={styles.tabCount}>{count}</Text>
      </Text>
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
    gap: spacing.md,
    padding: spacing.xl,
  },
  backLink: {
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: 10,
    backgroundColor: colors.ink,
  },
  backLinkText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 15,
    lineHeight: 26,
    color: colors.onInk,
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
    justifyContent: 'space-between',
  },
  iconButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sessionLabel: {
    ...text.small,
    fontSize: 12,
    minWidth: 44,
    textAlign: 'right',
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
  tabCount: {
    fontSize: 12,
    color: colors.inkMuted,
  },
  body: {
    gap: spacing.md,
    padding: 20,
    paddingBottom: spacing.xxl,
    width: '100%',
    maxWidth: 520,
    alignSelf: 'center',
  },
  counterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  counter: {
    fontFamily: fonts.japaneseBold,
    fontSize: 15,
    color: colors.ink,
  },
  counterTotal: {
    fontFamily: fonts.japanese,
    color: colors.inkMuted,
  },
  muted: {
    ...text.small,
    color: colors.inkMuted,
  },
  track: {
    height: 6,
    borderRadius: 3,
    overflow: 'hidden',
    backgroundColor: colors.track,
  },
  fill: {
    height: 6,
    backgroundColor: colors.gold,
  },
  navRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  round: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  roundDark: {
    borderColor: colors.ink,
    backgroundColor: colors.ink,
  },
  disabled: {
    opacity: 0.35,
  },
  studiedButton: {
    flex: 1,
    height: 52,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    borderRadius: 26,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  studiedOn: {
    borderColor: colors.goldDeep,
    backgroundColor: colors.goldSoft,
  },
  studiedCheck: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: colors.border,
  },
  studiedCheckOn: {
    borderColor: colors.gold,
    backgroundColor: colors.gold,
  },
  studiedText: {
    ...text.label,
    fontSize: 15,
    color: colors.ink,
  },
  studiedTextOn: {
    color: '#7A5A12',
  },
  doneProgress: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  doneStep: {
    ...text.label,
    fontSize: 13,
    color: colors.inkMuted,
  },
  doneStepOn: {
    color: '#7A5A12',
  },
  doneHint: {
    ...text.small,
    fontSize: 12,
    lineHeight: 21,
    marginTop: spacing.xs,
    textAlign: 'center',
    color: colors.inkMuted,
  },
  doneNote: {
    ...text.small,
    fontSize: 13,
    marginBottom: spacing.sm,
    textAlign: 'center',
    color: colors.inkMuted,
  },

  doneBar: {
    paddingHorizontal: 20,
    paddingTop: spacing.md,
    paddingBottom: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.divider,
    backgroundColor: colors.background,
  },
  doneButton: {
    height: 52,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.ink,
  },
  doneText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 16,
    lineHeight: 28,
    color: colors.onInk,
  },
});
