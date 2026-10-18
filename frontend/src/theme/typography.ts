// Fonts and text sizes. Burmese needs tall lines (about 1.75x the size)
// so the marks above and below letters never touch the line above.
export const fonts = {
  burmese: 'NotoSansMyanmar_400Regular',
  burmeseBold: 'NotoSansMyanmar_600SemiBold',
  japanese: 'ZenKakuGothicNew_400Regular',
  japaneseBold: 'ZenKakuGothicNew_700Bold',
  brand: 'ShipporiMinchoB1_800ExtraBold', // only for the 急合 name
} as const;

export const text = {
  small: { fontFamily: fonts.burmese, fontSize: 13, lineHeight: 23 },
  label: { fontFamily: fonts.burmeseBold, fontSize: 14, lineHeight: 24 },
  body: { fontFamily: fonts.burmese, fontSize: 16, lineHeight: 28 },
  title: { fontFamily: fonts.burmeseBold, fontSize: 24, lineHeight: 40 },
  studyWord: { fontFamily: fonts.japaneseBold, fontSize: 22, lineHeight: 32 },
  furigana: { fontFamily: fonts.japanese, fontSize: 10, lineHeight: 14 },
  bigNumber: { fontFamily: fonts.japaneseBold, fontSize: 40, lineHeight: 48 },
} as const;
