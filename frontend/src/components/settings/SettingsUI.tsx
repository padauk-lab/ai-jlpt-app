import type { ReactNode } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Switch, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';
import { router } from 'expo-router';
import { BackIcon } from '@/components/ui/Icons';
import { colors, fonts, radius, spacing, text } from '@/theme';

// Small building blocks shared by the Settings screens.

export function ScreenHeader({ title }: { title: string }) {
  return (
    <View style={styles.header}>
      <Pressable onPress={() => router.back()} accessibilityRole="button" accessibilityLabel="နောက်သို့" style={styles.back}>
        <BackIcon color={colors.ink} />
      </Pressable>
      <Text style={styles.headerTitle} numberOfLines={1}>
        {title}
      </Text>
    </View>
  );
}

export function Group({ title, children }: { title: string; children: ReactNode }) {
  return (
    <View style={styles.group}>
      <Text style={styles.groupTitle}>{title}</Text>
      <View style={styles.groupBox}>{children}</View>
    </View>
  );
}

type RowProps = {
  label: string;
  sub?: string;
  value?: string;
  danger?: boolean;
  onPress?: () => void;
  right?: ReactNode; // e.g. a switch, instead of the arrow
  first?: boolean; // no divider line above the first row
};

export function Row({ label, sub, value, danger, onPress, right, first }: RowProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={!onPress}
      accessibilityRole={onPress ? 'button' : undefined}
      style={({ pressed }) => [styles.row, !first && styles.rowDivider, pressed && styles.rowPressed]}
    >
      <View style={styles.rowText}>
        <Text style={[styles.rowLabel, danger && { color: colors.wrong }]}>{label}</Text>
        {sub && <Text style={styles.rowSub}>{sub}</Text>}
      </View>
      {value && <Text style={styles.rowValue}>{value}</Text>}
      {right ?? (onPress && !danger ? <Chevron /> : null)}
    </Pressable>
  );
}

export function Toggle({ value, onChange, label }: { value: boolean; onChange: (next: boolean) => void; label: string }) {
  return (
    <Switch
      value={value}
      onValueChange={onChange}
      accessibilityLabel={label}
      trackColor={{ false: colors.border, true: colors.ink }}
      thumbColor="#FFFFFF"
      ios_backgroundColor={colors.border}
    />
  );
}

export function Button({
  label,
  onPress,
  kind = 'primary',
  busy = false,
  disabled = false,
}: {
  label: string;
  onPress: () => void;
  kind?: 'primary' | 'secondary' | 'danger';
  busy?: boolean;
  disabled?: boolean;
}) {
  const off = disabled || busy;
  return (
    <Pressable
      onPress={onPress}
      disabled={off}
      accessibilityRole="button"
      accessibilityState={{ disabled: off }}
      style={({ pressed }) => [
        styles.button,
        kind === 'primary' && styles.primary,
        kind === 'secondary' && styles.secondary,
        kind === 'danger' && styles.danger,
        disabled && styles.disabled,
        pressed && { opacity: 0.85 },
      ]}
    >
      {busy ? (
        <ActivityIndicator color={kind === 'secondary' ? colors.ink : colors.onInk} />
      ) : (
        <Text style={[styles.buttonText, kind !== 'secondary' && { color: colors.onInk }]}>{label}</Text>
      )}
    </Pressable>
  );
}

export function Message({ text: message, kind = 'error' }: { text: string; kind?: 'error' | 'info' }) {
  return (
    <View style={[styles.message, kind === 'error' ? styles.messageError : styles.messageInfo]} accessibilityRole={kind === 'error' ? 'alert' : undefined}>
      <Text style={[styles.messageText, kind === 'error' ? { color: '#9E2F29' } : { color: '#3E2A12' }]}>{message}</Text>
    </View>
  );
}

function Chevron() {
  return (
    <Svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="#8C847E" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
      <Path d="M9 6l6 6-6 6" />
    </Svg>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: colors.divider,
    backgroundColor: colors.background,
  },
  back: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    ...text.label,
    flex: 1,
    fontSize: 18,
    lineHeight: 32,
    color: colors.ink,
  },
  group: {
    gap: 6,
  },
  groupTitle: {
    ...text.label,
    fontSize: 13,
    paddingLeft: spacing.xs,
    color: colors.inkMuted,
  },
  groupBox: {
    borderWidth: 1.5,
    borderColor: colors.divider,
    borderRadius: radius.card,
    overflow: 'hidden',
    backgroundColor: colors.background,
  },
  row: {
    minHeight: 54,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: spacing.lg,
    paddingVertical: 6,
  },
  rowDivider: {
    borderTopWidth: 1,
    borderTopColor: colors.track,
  },
  rowPressed: {
    backgroundColor: colors.surface,
  },
  rowText: {
    flex: 1,
  },
  rowLabel: {
    ...text.body,
    fontSize: 15,
    color: colors.ink,
  },
  rowSub: {
    ...text.small,
    fontSize: 12,
    lineHeight: 20,
    color: colors.inkMuted,
  },
  rowValue: {
    fontFamily: fonts.japanese,
    fontSize: 14,
    color: colors.inkMuted,
  },
  button: {
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.control,
  },
  primary: {
    backgroundColor: colors.ink,
  },
  secondary: {
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  danger: {
    backgroundColor: colors.wrong,
  },
  disabled: {
    opacity: 0.4,
  },
  buttonText: {
    fontFamily: fonts.burmeseBold,
    fontSize: 16,
    lineHeight: 28,
    color: colors.ink,
  },
  message: {
    padding: spacing.md,
    borderRadius: 12,
  },
  messageError: {
    backgroundColor: colors.wrongBg,
  },
  messageInfo: {
    backgroundColor: colors.goldSoft,
  },
  messageText: {
    ...text.small,
    fontSize: 14,
    lineHeight: 25,
  },
});
