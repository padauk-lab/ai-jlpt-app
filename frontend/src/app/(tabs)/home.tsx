import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { getDashboard, getSession, getTodayProverb } from '@/api';
import type { Dashboard, Proverb, SessionDetail } from '@/api/types';
import { HomeHeader } from '@/components/home/HomeHeader';
import { StudyMap } from '@/components/home/StudyMap';
import { buildMapLayout, type MapStop } from '@/components/home/mapLayout';
import { colors, fonts, spacing, text } from '@/theme';

type HomeData = {
  dashboard: Dashboard;
  session: SessionDetail;
  proverb: Proverb | null;
};

export default function HomeScreen() {
  const [data, setData] = useState<HomeData | null>(null);
  const [failed, setFailed] = useState(false);
  const scrollRef = useRef<ScrollView>(null);

  const load = useCallback(async () => {
    setFailed(false);
    try {
      const dashboard = await getDashboard();
      // Show the session the user is working on: the "continue" session,
      // or the first one that is not finished.
      const sessionId =
        dashboard.continue?.session_id ??
        dashboard.sessions.find((s) => s.status !== 'completed')?.id ??
        dashboard.sessions[dashboard.sessions.length - 1].id;
      const [session, proverb] = await Promise.all([
        getSession(sessionId),
        getTodayProverb().catch(() => null), // the proverb is nice to have, not required
      ]);
      setData({ dashboard, session, proverb });
    } catch {
      setFailed(true);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Open the map scrolled to the next unit, like a game level map.
  const scrollToCurrent = useCallback(() => {
    if (!data) return;
    const { stops, currentIndex } = buildMapLayout(data.session);
    const target = currentIndex >= 0 ? stops[currentIndex].y : 0;
    scrollRef.current?.scrollTo({ y: Math.max(0, target - 260), animated: false });
  }, [data]);

  function openStop(stop: MapStop) {
    if (stop.state === 'locked') return;
    if (stop.kind === 'unit') {
      router.push({ pathname: '/unit/[id]', params: { id: String(stop.id) } });
    } else if (stop.kind === 'quiz') {
      router.push({ pathname: '/quiz/[id]', params: { id: String(stop.id) } });
    }
    // The mock test screen is designed next (#23 to #26).
  }

  if (failed) {
    return (
      <SafeAreaView style={styles.center}>
        <Text style={styles.message}>ဒေတာ ရယူ၍ မရပါ။ ပြန်ကြိုးစားပါ။</Text>
        <Pressable onPress={load} style={styles.retry}>
          <Text style={styles.retryText}>ပြန်ကြိုးစားမည်</Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  if (!data) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator color={colors.ink} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.screen} edges={['top']}>
      <HomeHeader dashboard={data.dashboard} session={data.session} proverb={data.proverb} />
      <ScrollView ref={scrollRef} onContentSizeChange={scrollToCurrent} style={styles.scroll}>
        <StudyMap session={data.session} onOpenStop={openStop} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scroll: {
    flex: 1,
    backgroundColor: '#F1E6D0',
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.lg,
    padding: spacing.xl,
    backgroundColor: colors.background,
  },
  message: {
    ...text.body,
    color: colors.ink,
    textAlign: 'center',
  },
  retry: {
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    borderRadius: 10,
    backgroundColor: colors.ink,
  },
  retryText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 16,
    lineHeight: 26,
    color: colors.onInk,
  },
});
