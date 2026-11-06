import { Modal, StyleSheet, Text, View } from 'react-native';
import { Torii } from '@/components/Torii';
import { Button } from '@/components/settings/SettingsUI';
import { colors, fonts, spacing, text } from '@/theme';
import { toMyanmarDigits } from '@/utils/myanmar';
import { formatClock } from './useCountdown';

type Props = {
  visible: boolean;
  answered: number;
  total: number;
  secondsLeft: number;
  busy: boolean;
  onSubmit: () => void;
  onCancel: () => void;
};

// "Are you sure?" before submitting (#25). Checking again is the safe choice.
export function SubmitDialog({ visible, answered, total, secondsLeft, busy, onSubmit, onCancel }: Props) {
  const unanswered = total - answered;
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onCancel}>
      <View style={styles.backdrop}>
        <View style={styles.dialog} accessibilityViewIsModal>
          <Torii width={72} withPlaque />
          <Text style={styles.title}>တင်သွင်းမှာ သေချာပါသလား</Text>
          <View style={styles.stats}>
            <Stat value={`${answered} / ${total}`} label="ဖြေပြီး" />
            <Stat value={String(unanswered)} label="မဖြေရသေး" warn={unanswered > 0} />
            <Stat value={formatClock(secondsLeft)} label="ကျန်အချိန်" />
          </View>
          <Text style={styles.note}>မဖြေရသေးတာတွေ မှားတယ်လို့ တွက်ပါမယ်။ တင်သွင်းပြီးရင် ပြန်ပြင်လို့ မရပါ။</Text>
          <View style={styles.buttons}>
            <Button label="တင်သွင်းမည်" onPress={onSubmit} busy={busy} />
            <Button label="ပြန်စစ်မည်" kind="secondary" onPress={onCancel} disabled={busy} />
          </View>
        </View>
      </View>
    </Modal>
  );
}

function Stat({ value, label, warn = false }: { value: string; label: string; warn?: boolean }) {
  return (
    <View style={[styles.stat, warn && { backgroundColor: colors.wrongBg }]}>
      <Text style={[styles.statValue, warn && { color: colors.wrong }]}>{value}</Text>
      <Text style={[styles.statLabel, warn && { color: colors.wrong }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 22, backgroundColor: 'rgba(42,37,34,0.45)' },
  dialog: { width: '100%', maxWidth: 400, alignItems: 'center', gap: 10, padding: 20, paddingTop: 24, borderRadius: 20, backgroundColor: colors.background },
  title: { fontFamily: fonts.burmeseSerif, fontSize: 19, lineHeight: 40, color: colors.lacquer, textAlign: 'center' },
  stats: { flexDirection: 'row', gap: spacing.sm, alignSelf: 'stretch' },
  stat: { flex: 1, alignItems: 'center', paddingVertical: 10, borderRadius: 12, backgroundColor: colors.surface },
  statValue: { fontFamily: fonts.japaneseBold, fontSize: 17, color: colors.ink },
  statLabel: { ...text.small, fontSize: 12, color: colors.inkMuted },
  note: { ...text.small, fontSize: 14, lineHeight: 25, textAlign: 'center', color: colors.inkMuted },
  buttons: { alignSelf: 'stretch', gap: spacing.sm, marginTop: spacing.xs },
});
