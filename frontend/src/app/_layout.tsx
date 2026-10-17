import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import {
  NotoSansMyanmar_400Regular,
  NotoSansMyanmar_600SemiBold,
} from '@expo-google-fonts/noto-sans-myanmar';
import {
  ZenKakuGothicNew_400Regular,
  ZenKakuGothicNew_700Bold,
} from '@expo-google-fonts/zen-kaku-gothic-new';
import { ShipporiMinchoB1_800ExtraBold } from '@expo-google-fonts/shippori-mincho-b1';

// Keep the splash screen visible until the fonts are ready,
// so no screen ever flashes with the wrong font.
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    NotoSansMyanmar_400Regular,
    NotoSansMyanmar_600SemiBold,
    ZenKakuGothicNew_400Regular,
    ZenKakuGothicNew_700Bold,
    ShipporiMinchoB1_800ExtraBold,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded, fontError]);

  if (!fontsLoaded && !fontError) {
    return null;
  }

  return <Stack screenOptions={{ headerShown: false }} />;
}
