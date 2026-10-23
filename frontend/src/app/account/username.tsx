import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { ApiError, getMe, updateUsername } from '@/api';
import { Button, Message, ScreenHeader } from '@/components/settings/SettingsUI';
import { colors, fonts, radius, spacing, text } from '@/theme';
import { errorMessage } from '@/utils/errors';

const USERNAME_RULE = /^[A-Za-z0-9_]{3,20}$/;

// Change the username (#30).
export default function UsernameScreen() {
  const [username, setUsername] = useState('');
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    getMe().then((me) => me && setUsername(me.username));
  }, []);

  async function save() {
    if (!USERNAME_RULE.test(username)) {
      setProblem('စာလုံး 3 မှ 20 ၊ အင်္ဂလိပ်စာ၊ ဂဏန်းနှင့် _ သာ ရပါတယ်။');
      return;
    }
    setProblem(null);
    setBusy(true);
    try {
      await updateUsername(username);
      router.back();
    } catch (error) {
      setBusy(false);
      setProblem(error instanceof ApiError && error.code === 'username_taken' ? 'ဒီအမည်ကို တခြားသူ သုံးပြီးသားပါ။' : errorMessage(error));
    }
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScreenHeader title="အသုံးပြုသူအမည်" />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.field}>
          <Text style={styles.label}>အသုံးပြုသူအမည် အသစ်</Text>
          <TextInput
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
            autoCorrect={false}
            maxLength={20}
            style={styles.input}
          />
          <Text style={styles.hint}>စာလုံး 3 မှ 20 အထိ၊ အင်္ဂလိပ်စာ၊ ဂဏန်းနှင့် _ သာ</Text>
        </View>
        {problem && <Message text={problem} />}
        <Button label="သိမ်းမည်" onPress={save} busy={busy} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { gap: spacing.lg, padding: 20, width: '100%', maxWidth: 520, alignSelf: 'center' },
  field: { gap: spacing.xs },
  label: { ...text.label, color: colors.ink },
  input: {
    height: 50,
    paddingHorizontal: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radius.control,
    fontFamily: fonts.japanese,
    fontSize: 16,
    color: colors.ink,
  },
  hint: { ...text.small, color: colors.inkMuted },
});
