import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getNotifications, updateNotifications } from '@/api';
import type { NotificationSettings } from '@/api/types';
import { Group, Message, Row, ScreenHeader, Toggle } from '@/components/settings/SettingsUI';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';

const TIMES = ['07:00', '12:00', '18:00', '20:00', '21:00', '22:00'];

// Notification settings (#31, #32). Every change is saved straight away.
export default function NotificationsScreen() {
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  // The phone's own time zone, e.g. "Asia/Tokyo".
  const phoneZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  useEffect(() => {
    getNotifications()
      .then(setSettings)
      .catch((error) => setProblem(errorMessage(error)));
  }, []);

  async function change(part: Partial<NotificationSettings>) {
    if (!settings) return;
    const before = settings;
    const next = { ...settings, ...part };
    setSettings(next);
    setProblem(null);
    try {
      setSettings(await updateNotifications(next));
    } catch (error) {
      setSettings(before); // undo
      setProblem(errorMessage(error));
    }
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScreenHeader title="အသိပေးချက်" />
      {!settings ? (
        <View style={styles.center}>{problem ? <Message text={problem} /> : <ActivityIndicator color={colors.ink} />}</View>
      ) : (
        <ScrollView contentContainerStyle={styles.content}>
          {problem && <Message text={problem} />}
          <Group title="နေ့စဉ် သတိပေးချက်">
            <Row
              first
              label="ပန်းတိုင် မပြည့်သေးရင် သတိပေးမည်"
              sub="ယနေ့ ယူနစ် မပြီးသေးတဲ့ နေ့တွေမှာသာ ပို့ပါမယ်"
              right={<Toggle label="နေ့စဉ် သတိပေးချက်" value={settings.daily_reminder} onChange={(on) => change({ daily_reminder: on })} />}
            />
          </Group>

          <View style={styles.block}>
            <Text style={styles.blockTitle}>ပို့မည့်အချိန်</Text>
            <View style={styles.times} accessibilityRole="radiogroup">
              {TIMES.map((time) => {
                const on = settings.reminder_time === time;
                return (
                  <Pressable
                    key={time}
                    onPress={() => change({ reminder_time: time })}
                    accessibilityRole="radio"
                    accessibilityState={{ checked: on }}
                    style={[styles.time, on && styles.timeOn]}
                  >
                    <Text style={[styles.timeText, on && styles.timeTextOn]}>{time}</Text>
                  </Pressable>
                );
              })}
            </View>
          </View>

          <Group title="ယနေ့ ဆိုရိုးစကား">
            <Row
              first
              label="နေ့စဉ် ဆိုရိုးစကား တစ်ခု"
              sub="ကြိုးစားအားထုတ်မှုဆိုင်ရာ ဆိုရိုးစကား"
              right={<Toggle label="ယနေ့ ဆိုရိုးစကား" value={settings.proverb_notification} onChange={(on) => change({ proverb_notification: on })} />}
            />
          </Group>

          <Group title="အချိန်ဇုန်">
            <Row first label="လက်ရှိ" value={settings.timezone} />
            {phoneZone && phoneZone !== settings.timezone && (
              <Row label={`ဖုန်းရဲ့ အချိန်ဇုန် (${phoneZone}) ကို သုံးမည်`} onPress={() => change({ timezone: phoneZone })} />
            )}
          </Group>
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.surface },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  content: { gap: 18, padding: spacing.lg, paddingBottom: spacing.xxl, width: '100%', maxWidth: 560, alignSelf: 'center' },
  block: { gap: 6 },
  blockTitle: { ...text.label, fontSize: 13, paddingLeft: spacing.xs, color: colors.inkMuted },
  times: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  time: {
    minWidth: 76,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radius.control,
    backgroundColor: colors.background,
  },
  timeOn: { borderColor: colors.ink, backgroundColor: colors.ink },
  timeText: { fontFamily: fonts.japaneseBold, fontSize: 15, color: colors.ink },
  timeTextOn: { color: colors.onInk },
});
