// Spacing in steps of 4, so every screen lines up.
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
} as const;

// Corner roundness.
export const radius = {
  control: 10, // inputs and buttons
  card: 16, // cards and panels
  logo: 26, // the logo tile
} as const;
