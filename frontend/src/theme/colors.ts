// Colors for 急合 (design option B: white, red and gold).
// Screens use these names, never raw hex codes.
export const colors = {
  background: '#FFFFFF', // most screens
  goldSoft: '#FBF4E4', // login background, proverb card
  surface: '#FBFAF9', // cards on white screens
  ink: '#2A2522', // main text and primary buttons
  inkMuted: '#5A4F44', // secondary text, hints
  onInk: '#FFFFFF', // text on ink-colored buttons

  border: '#DDD6CF', // outlines on white screens
  borderWarm: '#CDAE68', // outlines on goldSoft
  divider: '#E7E2DC', // thin lines on white screens
  dividerWarm: '#D2B46E', // thin lines on goldSoft

  brandRed: '#C8102E', // the logo, the 急合 name and test gates ONLY
  gold: '#D9A441', // highlights, progress, rewards (never for small text)
  goldDeep: '#A97A1F', // gold details on goldSoft backgrounds
  lacquer: '#6B2E1A', // Myanmar lacquer red-brown: traditional titles, AI buttons
  ornament: '#B8913A', // gold lines of frames and flourishes
  paper: '#FBF7EE', // light panels on cards (AI answers, map road)
  paperEdge: '#E2D3B5', // edges of paper panels
  track: '#EFE9E1', // empty part of progress bars

  correct: '#2E7D4F', // quiz: right answer
  correctBg: '#E8F3EC',
  wrong: '#B42318', // quiz: wrong answer, error messages
  wrongBg: '#FBECEB',
} as const;
