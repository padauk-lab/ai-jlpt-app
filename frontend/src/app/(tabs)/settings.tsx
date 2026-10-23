import { useCallback, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useFocusEffect } from 'expo-router';
import { ApiError, getMe, getNotifications, getPlan, logout, updateNotifications } from '@/api';
import type { Me, NotificationSettings, StudyPlan } from '@/api/types';
import { BaganBanner } from '@/components/settings/BaganBanner';
import { Group, Message, Row, Toggle } from '@/components/settings/SettingsUI';
import { Notice, useNotice } from '@/components/ui/Notice';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';
import { formatDateMy } from '@/utils/myanmar';

// Settings (#29 to #37), grouped like the contract: profile, study, notifications, account.
export default function SettingsScreen() {
  const [me, setMe] = useState<Me | null>(null);
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [notifications, setNotifications] = useState<NotificationSettings | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const notice = useNotice();

  const load = useCallback(async () => {
    setProblem(null);
    try {
      const user = await getMe();
      if (!user) {
        router.replace('/login');
        return;
      }
      const [studyPlan, notify] = await Promise.all([getPlan().catch(() => null), getNotifications()]);
      setMe(user);
      setPlan(studyPlan);
      setNotifications(notify);
    } catch (error) {
      setProblem(errorMessage(error));
    }
  }, []);

  // Reload when coming back from a settings page, so changes show at once.
  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  // Switches save straight away (#32); if saving fails, they flip back.
  async function changeNotification(change: Partial<NotificationSettings>) {
    if (!notifications) return;
    const before = notifications;
    const next = { ...notifications, ...change };
    setNotifications(next);
    try {
      setNotifications(await updateNotifications(next));
    } catch (error) {
      setNotifications(before);
      notice.show(errorMessage(error));
    }
  }

  async function handleLogout() {
    await logout().catch(() => undefined); // this phone forgets the login either way
    router.replace('/login');
  }

  if (problem) {
    return (
      <SafeAreaView style={styles.center}>
        <Message text={problem} />
      </SafeAreaView>
    );
  }

  if (!me || !notifications) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator color={colors.ink} />
      </SafeAreaView>
    );
  }

  const studySummary = plan?.exam_date ? `စာမေးပွဲ ${formatDateMy(plan.exam_date, false)}` : 'စာမေးပွဲ ရက်စွဲ မဆုံးဖြတ်ရသေး';

  return (
    <SafeAreaView style={styles.screen} edges={['top']}>
      <View style={styles.titleBar}>
        <Text style={styles.title}>ဆက်တင်</Text>
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.profile}>
          <BaganBanner height={140} />
          <View style={styles.profileRow}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>{me.username.slice(0, 1).toUpperCase()}</Text>
            </View>
            <View style={styles.profileText}>
              <Text style={styles.username}>{me.username}</Text>
              <Text style={styles.email}>{me.email}</Text>
            </View>
            <Text style={styles.method}>{me.login_method === 'google' ? 'Google' : 'အီးမေးလ်'}</Text>
          </View>
        </View>

        <Group title="ပရိုဖိုင်">
          <Row first label="အသုံးပြုသူအမည်" value={me.username} onPress={() => router.push('/account/username')} />
        </Group>

        <Group title="လေ့လာမှု">
          <Row first label="လေ့လာမှု ဆက်တင်" sub={studySummary} onPress={() => router.push('/account/study')} />
          {plan && <Row label="လေ့လာမှု အစီအစဉ်" value={`တစ်နေ့ ${plan.units_per_day} ယူနစ်`} onPress={() => router.push('/plan')} />}
        </Group>

        <Group title="အသိပေးချက်">
          <Row
            first
            label="နေ့စဉ် သတိပေးချက်"
            sub={notifications.reminder_time}
            right={
              <Toggle
                label="နေ့စဉ် သတိပေးချက်"
                value={notifications.daily_reminder}
                onChange={(on) => changeNotification({ daily_reminder: on })}
              />
            }
          />
          <Row
            label="ယနေ့ ဆိုရိုးစကား"
            right={
              <Toggle
                label="ယနေ့ ဆိုရိုးစကား"
                value={notifications.proverb_notification}
                onChange={(on) => changeNotification({ proverb_notification: on })}
              />
            }
          />
          <Row label="အချိန်နဲ့ အချိန်ဇုန်" value={notifications.timezone} onPress={() => router.push('/account/notifications')} />
        </Group>

        <Group title="အကောင့်">
          {me.login_method === 'email' && (
            <Row first label="စကားဝှက် ပြောင်းမည်" sub="မကြာမီ" onPress={() => notice.show('စကားဝှက် ပြောင်းခြင်းကို မကြာမီ ထည့်ပေးပါမယ်')} />
          )}
          <Row first={me.login_method !== 'email'} label="ထွက်မည်" onPress={handleLogout} />
        </Group>

        <Group title="သတိထားရန်">
          <Row first danger label="တိုးတက်မှုအားလုံး ပြန်စမည်" sub="အပိုင်း ၁ ကနေ ပြန်စပါမယ်" onPress={() => router.push('/account/reset')} />
          <Row danger label="အကောင့် ဖျက်မည်" onPress={() => router.push('/account/delete')} />
        </Group>

        <Text style={styles.version}>急合 1.0.0 ၊ Padauk Lab</Text>
      </ScrollView>
      <Notice message={notice.message} />
    </SafeAreaView>
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
    padding: spacing.xl,
    backgroundColor: colors.surface,
  },
  titleBar: {
    paddingHorizontal: 20,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
    backgroundColor: colors.background,
  },
  title: {
    ...text.label,
    fontSize: 20,
    lineHeight: 34,
    color: colors.ink,
  },
  content: {
    gap: 18,
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
    width: '100%',
    maxWidth: 560,
    alignSelf: 'center',
  },
  profile: {
    borderWidth: 1.5,
    borderColor: colors.paperEdge,
    borderRadius: radius.card,
    overflow: 'hidden',
    backgroundColor: colors.background,
  },
  profileRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: spacing.md,
    paddingHorizontal: spacing.lg,
    paddingBottom: 14,
  },
  avatar: {
    width: 62,
    height: 62,
    marginTop: -30,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: '#FFFFFF',
    borderRadius: 31,
    backgroundColor: colors.lacquer,
  },
  avatarText: {
    fontFamily: fonts.japaneseBold,
    fontSize: 24,
    color: '#F2D27A',
  },
  profileText: {
    flex: 1,
    paddingTop: spacing.sm,
  },
  username: {
    ...text.label,
    fontSize: 17,
    lineHeight: 28,
    color: colors.ink,
  },
  email: {
    fontFamily: fonts.japanese,
    fontSize: 13,
    lineHeight: 20,
    color: colors.inkMuted,
  },
  method: {
    ...text.small,
    fontSize: 12,
    lineHeight: 21,
    marginBottom: 4,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: colors.paperEdge,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: colors.goldSoft,
    color: colors.inkMuted,
  },
  version: {
    ...text.small,
    fontSize: 12,
    textAlign: 'center',
    color: '#8C847E',
  },
});
