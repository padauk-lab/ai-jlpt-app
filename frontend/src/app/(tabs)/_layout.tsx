import { Tabs } from 'expo-router';
import { BookmarkIcon, HomeIcon, SettingsIcon } from '@/components/TabIcons';
import { colors, fonts } from '@/theme';

// The three bottom tabs from the product decisions: Home, Saved words, Settings.
export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.ink,
        tabBarInactiveTintColor: colors.inkMuted,
        tabBarLabelStyle: { fontFamily: fonts.burmese, fontSize: 12 },
        tabBarStyle: { borderTopColor: colors.divider, backgroundColor: colors.background },
      }}
    >
      <Tabs.Screen
        name="home"
        options={{ title: 'ပင်မ', tabBarIcon: ({ color }) => <HomeIcon color={color} /> }}
      />
      <Tabs.Screen
        name="saved"
        options={{ title: 'မှတ်ထားသော စကားလုံး', tabBarIcon: ({ color }) => <BookmarkIcon color={color} /> }}
      />
      <Tabs.Screen
        name="settings"
        options={{ title: 'ဆက်တင်', tabBarIcon: ({ color }) => <SettingsIcon color={color} /> }}
      />
    </Tabs>
  );
}
