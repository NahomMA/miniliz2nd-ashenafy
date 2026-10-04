import { Redirect } from 'expo-router';
import { Linking, Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card, Disclaimer, ErrorNote } from '@/components/ui';
import { useConversation } from '@/lib/conversation';
import { colors, font, formatUSD, radius, space } from '@/lib/theme';
import type { Assessment, Line, Option } from '@/lib/types';

const YEARS = { min: 1, max: 40 };
const CHART_YEARS = [0, 5, 10, 15, 20, 25, 30];

function Goal({ result }: { result: Assessment }) {
  const covered = result.total_need ? Math.min(1, result.resources / result.total_need) : 1;
  return (
    <Card>
      <Text style={styles.label}>Your coverage goal</Text>
      <Text style={styles.hero}>{formatUSD(result.total_need)}</Text>
      <View style={styles.track} accessibilityLabel={`${Math.round(covered * 100)} percent already in place`}>
        <View style={[styles.fill, { width: `${Math.max(2, covered * 100)}%` }]} />
      </View>
      <Text style={styles.body}>
        {result.fully_covered
          ? `The ${formatUSD(result.resources)} you already have covers this goal.`
          : `You already have ${formatUSD(result.resources)} in place. ${formatUSD(result.gap)} more would complete the goal.`}
      </Text>
    </Card>
  );
}

function Row({ line, total, sign }: { line: Line; total: number; sign: '+' | '−' }) {
  return (
    <View style={styles.row}>
      <View style={styles.rowHead}>
        <Text style={styles.rowLabel}>{line.label}</Text>
        <Text style={styles.rowAmount}>
          {sign === '−' ? '− ' : ''}
          {formatUSD(line.amount)}
        </Text>
      </View>
      <View style={styles.track}>
        <View
          style={[styles.fill, sign === '−' && { backgroundColor: colors.success }, { width: `${Math.max(2, (line.amount / total) * 100)}%` }]}
        />
      </View>
      <Text style={styles.muted}>{line.reason}</Text>
    </View>
  );
}

function StepButton({ symbol, label, disabled, onPress }: { symbol: string; label: string; disabled: boolean; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      disabled={disabled}
      onPress={onPress}
      style={[styles.stepButton, disabled && { opacity: 0.5 }]}>
      <Text style={styles.stepText}>{symbol}</Text>
    </Pressable>
  );
}

function Stepper({ label, value, onChange, disabled }: { label: string; value: number; onChange: (next: number) => void; disabled: boolean }) {
  const step = (delta: number) => onChange(Math.min(YEARS.max, Math.max(YEARS.min, value + delta)));
  return (
    <View style={styles.control}>
      <Text style={styles.controlLabel}>{label}</Text>
      <View style={styles.stepper}>
        <StepButton symbol="−" label="One year less" disabled={disabled} onPress={() => step(-1)} />
        <Text style={styles.stepValue}>{value}</Text>
        <StepButton symbol="+" label="One year more" disabled={disabled} onPress={() => step(1)} />
      </View>
    </View>
  );
}

function Timeline({ result }: { result: Assessment }) {
  const points = result.projection.years.filter((y) => CHART_YEARS.includes(y.year));
  const peak = Math.max(1, ...points.map((p) => p.remaining_need));
  return (
    <Card title="How your need changes">
      <View style={styles.chart}>
        {points.map((point) => (
          <View key={point.year} style={styles.barColumn}>
            <View style={styles.barArea}>
              <View style={[styles.bar, { height: `${Math.max(2, (point.remaining_need / peak) * 100)}%` }]} />
            </View>
            <Text style={styles.barLabel}>{point.year === 0 ? 'Now' : `${point.year}y`}</Text>
          </View>
        ))}
      </View>
      <Text style={styles.body}>{result.projection.reason}</Text>
    </Card>
  );
}

function OptionCard({ title, option, tint }: { title: string; option: Option; tint: string }) {
  return (
    <View style={[styles.option, { borderLeftColor: tint }]}>
      <Text style={styles.rowLabel}>{title}</Text>
      <Text style={styles.muted}>{option.what}</Text>
      {option.fits_when.map((text) => (
        <Text key={text} style={styles.body}>
          • {text}
        </Text>
      ))}
      {option.tradeoffs.map((text) => (
        <Text key={text} style={styles.muted}>
          Keep in mind: {text}
        </Text>
      ))}
    </View>
  );
}

export default function ResultsScreen() {
  const { assessment, preview, profile, busy, error, whatIf, clearPreview } = useConversation();
  if (!assessment || !profile) return <Redirect href="/" />;

  const result = preview ?? assessment;
  const incomeLine = result.components.find((c) => c.key === 'income');
  const years = profile.annual_income && incomeLine ? Math.round(incomeLine.amount / profile.annual_income) : 0;
  const education = result.components.some((c) => c.key === 'education');
  const delta = result.total_need - assessment.total_need;
  const term = result.projection.suggested_term_years;

  return (
    <SafeAreaView style={styles.screen} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Goal result={result} />

        <Card title="Why this number">
          {result.components.map((line) => (
            <Row key={line.key} line={line} total={result.total_need} sign="+" />
          ))}
          {result.offsets.map((line) => (
            <Row key={line.key} line={line} total={result.total_need} sign="−" />
          ))}
        </Card>

        <Card title="Try a different plan">
          {profile.annual_income ? (
            <Stepper
              label="Years of income to replace"
              value={years}
              disabled={busy}
              onChange={(next) => void whatIf({ income_years_to_replace: next, fund_education: education })}
            />
          ) : null}
          <View style={styles.control}>
            <Text style={styles.controlLabel}>Include college costs</Text>
            <Switch
              accessibilityLabel="Include college costs"
              value={education}
              disabled={busy}
              onValueChange={(on) => void whatIf({ income_years_to_replace: years || undefined, fund_education: on })}
              trackColor={{ true: colors.primary, false: colors.border }}
            />
          </View>
          <ErrorNote message={error} />
          {preview ? (
            <View style={styles.previewNote}>
              <Text style={styles.body}>
                {delta === 0 ? 'Same goal as your saved plan.' : `${formatUSD(Math.abs(delta))} ${delta < 0 ? 'lower' : 'higher'} than your saved plan.`}
              </Text>
              <Pressable accessibilityRole="button" onPress={clearPreview} hitSlop={12}>
                <Text style={styles.link}>Reset</Text>
              </Pressable>
            </View>
          ) : null}
        </Card>

        <Timeline result={result} />

        <Card title="Term or permanent?">
          {term ? <Text style={styles.callout}>A {term}-year period lines up with your need.</Text> : null}
          <OptionCard title="Term" option={result.comparison.term} tint={colors.accent} />
          <OptionCard title="Permanent" option={result.comparison.permanent} tint={colors.success} />
          <Text style={styles.muted}>{result.comparison.note}</Text>
        </Card>

        <Card title="How we calculated this">
          <Text style={styles.muted}>{result.method}</Text>
          {result.assumptions.map((item) => (
            <Pressable
              key={item.key}
              accessibilityRole={item.url ? 'link' : 'text'}
              disabled={!item.url}
              onPress={() => item.url && void Linking.openURL(item.url)}>
              <Text style={styles.body}>
                {item.label}: {formatUSD(item.value)}
              </Text>
              <Text style={[styles.muted, item.url ? { textDecorationLine: 'underline' } : null]}>
                {item.source}
                {item.as_of ? ` (${item.as_of})` : ''}
              </Text>
            </Pressable>
          ))}
        </Card>

        <Disclaimer />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.lg },
  label: { fontSize: font.small, color: colors.muted, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.5 },
  hero: { fontSize: font.hero, fontWeight: '800', color: colors.primary },
  body: { fontSize: font.body, lineHeight: 23, color: colors.text },
  muted: { fontSize: font.small, lineHeight: 20, color: colors.muted },
  track: { height: 8, borderRadius: 4, backgroundColor: colors.primarySoft, overflow: 'hidden' },
  fill: { height: '100%', borderRadius: 4, backgroundColor: colors.primary },
  row: { gap: space.xs, paddingVertical: space.sm },
  rowHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', gap: space.sm },
  rowLabel: { fontSize: font.body, fontWeight: '600', color: colors.text, flexShrink: 1 },
  rowAmount: { fontSize: font.body, fontWeight: '700', color: colors.text },
  control: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', minHeight: 52, gap: space.md },
  controlLabel: { fontSize: font.body, color: colors.text, flexShrink: 1 },
  stepper: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  stepButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepText: { fontSize: 22, color: colors.primary, fontWeight: '700' },
  stepValue: { fontSize: font.title, fontWeight: '700', color: colors.text, minWidth: 32, textAlign: 'center' },
  previewNote: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: space.md,
    backgroundColor: colors.primarySoft,
    borderRadius: radius,
    padding: space.md,
  },
  link: { color: colors.primary, fontSize: font.body, fontWeight: '700' },
  chart: { flexDirection: 'row', alignItems: 'flex-end', gap: space.sm, height: 140 },
  barColumn: { flex: 1, alignItems: 'center', gap: space.xs },
  barArea: { flex: 1, width: '100%', justifyContent: 'flex-end' },
  bar: { width: '100%', backgroundColor: colors.accent, borderTopLeftRadius: 6, borderTopRightRadius: 6 },
  barLabel: { fontSize: 12, color: colors.muted },
  callout: {
    fontSize: font.body,
    fontWeight: '600',
    color: colors.success,
    backgroundColor: colors.successSoft,
    borderRadius: radius,
    padding: space.md,
  },
  option: { borderLeftWidth: 4, paddingLeft: space.md, gap: space.xs, paddingVertical: space.xs },
});
