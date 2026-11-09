import { StyleSheet, Text, TextInput, View, type TextInputProps } from 'react-native';
import { colors, fonts, radius, spacing, text } from '@/theme';

type Props = TextInputProps & {
  label: string;
  hint?: string; // shown under the input when there is no error
  error?: string;
};

// A labelled text input with a hint or an error underneath (used by the password screens).
export function TextField({ label, hint, error, style, ...input }: Props) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        placeholderTextColor={colors.inkMuted}
        style={[styles.input, error ? styles.inputError : null, style]}
        {...input}
      />
      {error ? (
        <Text accessibilityRole="alert" style={styles.error}>
          {error}
        </Text>
      ) : (
        hint && <Text style={styles.hint}>{hint}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  field: { gap: spacing.xs },
  label: { ...text.label, color: colors.ink },
  input: {
    height: 50,
    paddingHorizontal: spacing.lg,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radius.control,
    backgroundColor: colors.background,
    fontFamily: fonts.burmese,
    fontSize: 16,
    color: colors.ink,
  },
  inputError: { borderColor: colors.wrong },
  error: { ...text.label, fontSize: 13, lineHeight: 23, color: colors.wrong },
  hint: { ...text.small, color: colors.inkMuted },
});
