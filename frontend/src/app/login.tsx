import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Logo } from '@/components/Logo';
import { RubyText, type RubyPiece } from '@/components/RubyText';
import { colors, fonts, radius, spacing, text } from '@/theme';

const TAGLINE: RubyPiece[] = [
  { text: '小', reading: 'ちい' },
  { text: 'さな' },
  { text: '継続', reading: 'けいぞく' },
  { text: 'が、' },
  { text: '大', reading: 'おお' },
  { text: 'きな' },
  { text: '到達', reading: 'とうたつ' },
  { text: 'になる。' },
];

type Mode = 'login' | 'register';

export default function LoginScreen() {
  const [mode, setMode] = useState<Mode>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const isRegister = mode === 'register';

  function handleSubmit() {
    // Next step: call POST /auth/login or POST /auth/register here.
    // For now, a new account goes to first-time setup (onboarding_completed: false).
    router.replace('/setup');
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <View style={styles.logoTile}>
            <Logo size={70} />
          </View>
          <Text style={styles.appName}>急合</Text>
          <View style={styles.goldBar} />
          <RubyText ruby={TAGLINE} size={16} />
          <Text style={styles.taglineMy}>နေ့စဉ် လေ့လာမှု အသေးအဖွဲများ၊ ကြီးမားသော တိုးတက်မှု။</Text>
        </View>

        <View style={styles.tabs}>
          <Tab label="အကောင့်ဝင်မည်" active={!isRegister} onPress={() => setMode('login')} />
          <Tab label="အကောင့်သစ်ဖွင့်မည်" active={isRegister} onPress={() => setMode('register')} />
        </View>

        {isRegister && (
          <View style={styles.field}>
            <Text style={styles.label}>အသုံးပြုသူအမည်</Text>
            <TextInput
              style={styles.input}
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              autoCorrect={false}
              placeholder="htet_pai"
              placeholderTextColor={colors.inkMuted}
            />
            <Text style={styles.hint}>စာလုံး 3 မှ 20 အထိ၊ အင်္ဂလိပ်စာ၊ ဂဏန်းနှင့် _ သာ</Text>
          </View>
        )}

        <View style={styles.field}>
          <Text style={styles.label}>အီးမေးလ်</Text>
          <TextInput
            style={styles.input}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
            autoCorrect={false}
            placeholder="you@example.com"
            placeholderTextColor={colors.inkMuted}
          />
        </View>

        <View style={styles.field}>
          <View style={styles.labelRow}>
            <Text style={styles.label}>စကားဝှက်</Text>
            {!isRegister && (
              <Pressable onPress={() => {}} hitSlop={8}>
                <Text style={styles.link}>မေ့နေပါသလား</Text>
              </Pressable>
            )}
          </View>
          <TextInput
            style={styles.input}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            autoCapitalize="none"
            autoComplete={isRegister ? 'new-password' : 'current-password'}
          />
          {isRegister && <Text style={styles.hint}>အနည်းဆုံး စာလုံး 8 လုံး</Text>}
        </View>

        <Pressable
          onPress={handleSubmit}
          style={({ pressed }) => [styles.primaryButton, pressed && styles.pressed]}
        >
          <Text style={styles.primaryButtonText}>
            {isRegister ? 'အကောင့်သစ်ဖွင့်မည်' : 'အကောင့်ဝင်မည်'}
          </Text>
        </Pressable>

        <View style={styles.dividerRow}>
          <View style={styles.dividerLine} />
          <Text style={styles.hint}>သို့မဟုတ်</Text>
          <View style={styles.dividerLine} />
        </View>

        {/* Later: replace with Google's official sign-in button. */}
        <Pressable
          onPress={() => {}}
          style={({ pressed }) => [styles.secondaryButton, pressed && styles.pressed]}
        >
          <Text style={styles.secondaryButtonText}>Google ဖြင့် ဝင်မည်</Text>
        </Pressable>

        <Text style={styles.terms}>
          ဆက်လက်ဆောင်ရွက်ခြင်းဖြင့် အသုံးပြုမှုစည်းမျဉ်းများ ကို လက်ခံပြီးဖြစ်ပါသည်။
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

type TabProps = {
  label: string;
  active: boolean;
  onPress: () => void;
};

function Tab({ label, active, onPress }: TabProps) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="tab"
      accessibilityState={{ selected: active }}
      style={[styles.tab, active && styles.tabActive]}
    >
      <Text style={[styles.tabText, active && styles.tabTextActive]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.goldSoft,
  },
  content: {
    paddingHorizontal: 28,
    paddingBottom: spacing.xl,
    gap: spacing.md,
    width: '100%',
    maxWidth: 480,
    alignSelf: 'center',
  },
  header: {
    alignItems: 'center',
    gap: spacing.sm,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.sm,
  },
  logoTile: {
    width: 92,
    height: 92,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: colors.goldDeep,
    borderRadius: radius.logo,
    backgroundColor: colors.background,
  },
  appName: {
    fontFamily: fonts.brand,
    fontSize: 32,
    lineHeight: 42,
    color: colors.brandRed,
  },
  goldBar: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.goldDeep,
  },
  taglineMy: {
    ...text.small,
    fontSize: 14,
    lineHeight: 24,
    color: colors.inkMuted,
    textAlign: 'center',
  },
  tabs: {
    flexDirection: 'row',
    borderBottomWidth: 1.5,
    borderBottomColor: colors.dividerWarm,
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
  field: {
    gap: spacing.xs,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    ...text.label,
    color: colors.ink,
  },
  link: {
    ...text.small,
    fontSize: 14,
    color: colors.ink,
    textDecorationLine: 'underline',
  },
  input: {
    height: 50,
    paddingHorizontal: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.borderWarm,
    borderRadius: radius.control,
    backgroundColor: colors.background,
    fontFamily: fonts.burmese,
    fontSize: 16,
    color: colors.ink,
  },
  hint: {
    ...text.small,
    color: colors.inkMuted,
  },
  primaryButton: {
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.xs,
    borderRadius: radius.control,
    backgroundColor: colors.ink,
  },
  primaryButtonText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 17,
    lineHeight: 28,
    color: colors.onInk,
  },
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: colors.dividerWarm,
  },
  secondaryButton: {
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.borderWarm,
    borderRadius: radius.control,
    backgroundColor: colors.background,
  },
  secondaryButtonText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 16,
    lineHeight: 26,
    color: colors.ink,
  },
  pressed: {
    opacity: 0.85,
  },
  terms: {
    ...text.small,
    color: colors.inkMuted,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
});
