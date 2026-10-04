import { Redirect } from 'expo-router';
import { Linking, Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card, Disclaimer, ErrorNote } from '@/components/ui';
import { useConversation } from '@/lib/conversation';
import { colors, font, formatShortUSD, formatUSD, radius, series, shadow, space } from '@/lib/theme';
import type { Assessment, Line, Option } from '@/lib/types';

const YEARS = { min: 1, max: 40 };
const CHART_YEARS = [0, 5, 10, 15, 20, 25, 30];
const TIMELINE_YEARS = 40;

const tint = (key: string) => series[key] ?? colors.muted;

function Goal({ result }: { result: Assessment }) {
  const covered = result.total_need ? Math.min(1, result.resources / result.total_need) : 1;
  return (
    <View style={styles.hero}>
      <Text style={styles.heroLabel}>Your coverage goal</Text>
      <Text style={styles.heroAmount}>{formatUSD(result.total_need)}</Text>
      <View style={styles.heroTrack} accessibilityLabel={`${Math.round(covered * 100)} percent already in place`}>
        <View style={[styles.heroFill, { width: `${Math.max(3, covered * 100)}%` }]} />
      </View>
      <View style={styles.heroStats}>
        <Stat label="Already in place" value={formatUSD(result.resources)} />
        <Stat label={result.fully_covered ? 'Goal covered' : 'Left to cover'} value={formatUSD(result.gap)} alignEnd />
      </View>
    </View>
  );
}

function Stat({ label, value, alignEnd }: { label: string; value: string; alignEnd?: boolean }) {
  return (
    <View style={alignEnd ? styles.statEnd : undefined}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statValue}>{value}</Text>
    </View>
  );
}

function Breakdown({ result }: { result: Assessment }) {
  return (
    <Card title="Why this number">
      <View style={styles.stack} accessibilityLabel="Share of each part of your coverage goal">
        {result.components.map((line) => (
          <View key={line.key} style={{ flex: line.amount, backgroundColor: tint(line.key) }} />
        ))}
      </View>
      {result.components.map((line) => (
        <Row key={line.key} line={line} share={line.amount / result.total_need} />
      ))}
      {result.offsets.length ? <Text style={styles.subhead}>What you already have</Text> : null}
      {result.offsets.map((line) => (
        <Row key={line.key} line={line} offset />
      ))}
    </Card>
  );
}

function Row({ line, share, offset }: { line: Line; share?: number; offset?: boolean }) {
  return (
    <View style={styles.row}>
      <View style={[styles.dot, { backgroundColor: tint(line.key) }]} />
      <View style={styles.rowText}>
        <View style={styles.rowHead}>
          <Text style={styles.rowLabel}>{line.label}</Text>
          <Text style={styles.rowAmount}>
            {offset ? '− ' : ''}
            {formatUSD(line.amount)}
          </Text>
        </View>
        <Text style={styles.muted}>
          {share !== undefined ? `${Math.max(1, Math.round(share * 100))}% of the goal. ` : ''}
          {line.reason}
        </Text>
      </View>
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
      style={({ pressed }) => [styles.stepButton, (disabled || pressed) && { opacity: 0.5 }]}>
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

function NeedOverTime({ result }: { result: Assessment }) {
  const points = result.projection.years.filter((y) => CHART_YEARS.includes(y.year));
  const peak = Math.max(1, ...points.map((p) => p.remaining_need));
  const firstCovered = points.find((p) => p.remaining_need <= result.resources)?.year;
  return (
    <Card title="How your need changes">
      <View style={styles.chart}>
        {points.map((point) => {
          const covered = point.remaining_need <= result.resources;
          const labelled = point.year === 0 || point.year === firstCovered;
          return (
            <View key={point.year} style={styles.barColumn}>
              <View style={styles.barArea}>
                {labelled ? <Text style={styles.barValue}>{covered ? 'Covered' : formatShortUSD(point.remaining_need)}</Text> : null}
                <View
                  style={[
                    styles.bar,
                    { height: `${Math.max(3, (point.remaining_need / peak) * 82)}%`, backgroundColor: covered ? colors.rose : colors.primary },
                  ]}
                />
              </View>
              <Text style={styles.barLabel}>{point.year === 0 ? 'Now' : `${point.year}y`}</Text>
            </View>
          );
        })}
      </View>
      <View style={styles.legend}>
        <Legend color={colors.primary} label="Still needed" />
        <Legend color={colors.rose} label="Covered by what you have" />
      </View>
      <Text style={styles.body}>{result.projection.reason}</Text>
    </Card>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <View style={styles.legendItem}>
      <View style={[styles.dot, { backgroundColor: color, marginTop: 0 }]} />
      <Text style={styles.muted}>{label}</Text>
    </View>
  );
}

function Span({ label, share, color, caption }: { label: string; share: number; color: string; caption: string }) {
  return (
    <View style={styles.span}>
      <Text style={styles.spanLabel}>{label}</Text>
      <View style={styles.spanTrack}>
        <View style={[styles.spanFill, { width: `${Math.max(6, share * 100)}%`, backgroundColor: color }]} />
      </View>
      <Text style={styles.spanCaption}>{caption}</Text>
    </View>
  );
}

function OptionPanel({ title, tag, option, color, soft, match }: { title: string; tag: string; option: Option; color: string; soft: string; match?: string }) {
  return (
    <View style={styles.panel}>
      <View style={[styles.panelHead, { backgroundColor: color }]}>
        <Text style={styles.panelTitle}>{title}</Text>
        <Text style={styles.panelTag}>{tag}</Text>
      </View>
      <View style={[styles.panelBody, { backgroundColor: soft }]}>
        {match ? (
          <View style={styles.match}>
            <Text style={styles.matchText}>★ {match}</Text>
          </View>
        ) : null}
        <Text style={styles.muted}>{option.what}</Text>
        {option.fits_when.map((text) => (
          <View key={text} style={styles.point}>
            <Text style={[styles.check, { color }]}>✓</Text>
            <Text style={styles.pointText}>{text}</Text>
          </View>
        ))}
        {option.tradeoffs.map((text) => (
          <View key={text} style={styles.caution}>
            <Text style={styles.cautionLabel}>Keep in mind</Text>
            <Text style={styles.cautionText}>{text}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

function TermOrPermanent({ result }: { result: Assessment }) {
  const term = result.projection.suggested_term_years;
  return (
    <Card title="Term or permanent?">
      <View style={styles.spans}>
        <Span label="Term" share={(term ?? 20) / TIMELINE_YEARS} color={colors.primary} caption={term ? `${term} years` : 'A set period'} />
        <Span label="Permanent" share={1} color={colors.accent} caption="For life" />
      </View>
      <OptionPanel
        title="Term"
        tag="FOR NEEDS THAT END"
        option={result.comparison.term}
        color={colors.primary}
        soft={colors.primarySoft}
        match={term ? `${term} years lines up with your need` : undefined}
      />
      <OptionPanel title="Permanent" tag="FOR NEEDS THAT LAST" option={result.comparison.permanent} color={colors.accent} soft={colors.accentSoft} />
      <Text style={styles.muted}>{result.comparison.note}</Text>
    </Card>
  );
}

function Sources({ result }: { result: Assessment }) {
  return (
    <Card title="How we calculated this">
      <Text style={styles.muted}>{result.method}</Text>
      {result.assumptions.map((item) => (
        <View key={item.key} style={styles.source}>
          <View style={styles.rowHead}>
            <Text style={styles.rowLabel}>{item.label}</Text>
            <Text style={styles.rowAmount}>{formatUSD(item.value)}</Text>
          </View>
          <Text style={styles.muted}>
            {item.source}
            {item.as_of ? ` (${item.as_of})` : ''}
          </Text>
          {item.url ? (
            <Pressable accessibilityRole="link" hitSlop={8} onPress={() => void Linking.openURL(item.url as string)}>
              <Text style={styles.link}>View source ↗</Text>
            </Pressable>
          ) : null}
        </View>
      ))}
    </Card>
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

  return (
    <SafeAreaView style={styles.screen} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Goal result={result} />
        <Breakdown result={result} />

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
              thumbColor={colors.card}
            />
          </View>
          <ErrorNote message={error} />
          {preview ? (
            <View style={styles.previewNote}>
              <Text style={[styles.body, styles.previewText]}>
                {delta === 0 ? 'Same goal as your saved plan.' : `${formatUSD(Math.abs(delta))} ${delta < 0 ? 'lower' : 'higher'} than your saved plan.`}
              </Text>
              <Pressable accessibilityRole="button" onPress={clearPreview} hitSlop={12}>
                <Text style={styles.link}>Reset</Text>
              </Pressable>
            </View>
          ) : null}
        </Card>

        <NeedOverTime result={result} />
        <TermOrPermanent result={result} />
        <Sources result={result} />
        <Disclaimer />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.lg },
  hero: { backgroundColor: colors.primary, borderRadius: 20, padding: space.xl, gap: space.md, ...shadow },
  heroLabel: { fontSize: 13, color: colors.rose, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 1 },
  heroAmount: { fontSize: font.hero, fontWeight: '800', color: colors.card, letterSpacing: -0.5 },
  heroTrack: { height: 10, borderRadius: 5, backgroundColor: colors.primaryDark, overflow: 'hidden' },
  heroFill: { height: '100%', borderRadius: 5, backgroundColor: colors.gold },
  heroStats: { flexDirection: 'row', justifyContent: 'space-between', gap: space.md },
  statEnd: { alignItems: 'flex-end' },
  statLabel: { fontSize: 13, color: colors.rose },
  statValue: { fontSize: font.title, fontWeight: '700', color: colors.card },
  body: { fontSize: font.body, lineHeight: 23, color: colors.text },
  muted: { fontSize: font.small, lineHeight: 20, color: colors.muted },
  stack: { flexDirection: 'row', height: 14, borderRadius: 7, overflow: 'hidden', gap: 2, marginBottom: space.xs },
  subhead: { fontSize: 13, fontWeight: '700', color: colors.muted, textTransform: 'uppercase', letterSpacing: 1, marginTop: space.sm },
  row: { flexDirection: 'row', gap: space.md, paddingVertical: space.sm },
  dot: { width: 12, height: 12, borderRadius: 6, marginTop: 6 },
  rowText: { flex: 1, gap: 2 },
  rowHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', gap: space.sm },
  rowLabel: { fontSize: font.body, fontWeight: '600', color: colors.text, flexShrink: 1 },
  rowAmount: { fontSize: font.body, fontWeight: '700', color: colors.text },
  control: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', minHeight: 52, gap: space.md },
  controlLabel: { fontSize: font.body, color: colors.text, flexShrink: 1 },
  stepper: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  stepButton: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.primarySoft, alignItems: 'center', justifyContent: 'center' },
  stepText: { fontSize: 22, color: colors.primary, fontWeight: '700' },
  stepValue: { fontSize: font.title, fontWeight: '700', color: colors.text, minWidth: 32, textAlign: 'center' },
  previewNote: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: space.md,
    backgroundColor: colors.goldSoft,
    borderRadius: radius,
    padding: space.md,
  },
  previewText: { flex: 1 },
  link: { color: colors.primary, fontSize: font.body, fontWeight: '700' },
  chart: { flexDirection: 'row', alignItems: 'flex-end', gap: space.sm, height: 160 },
  barColumn: { flex: 1, alignItems: 'center', gap: space.xs },
  barArea: { flex: 1, width: '100%', justifyContent: 'flex-end', alignItems: 'center' },
  bar: { width: '100%', borderTopLeftRadius: 4, borderTopRightRadius: 4 },
  barValue: { fontSize: 12, fontWeight: '700', color: colors.text, marginBottom: 2 },
  barLabel: { fontSize: 12, color: colors.muted },
  legend: { flexDirection: 'row', flexWrap: 'wrap', gap: space.lg },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  spans: { gap: space.sm, marginBottom: space.xs },
  span: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  spanLabel: { width: 84, fontSize: font.small, fontWeight: '600', color: colors.text },
  spanTrack: { flex: 1, height: 10, borderRadius: 5, backgroundColor: colors.border, overflow: 'hidden' },
  spanFill: { height: '100%', borderRadius: 5 },
  spanCaption: { width: 64, fontSize: font.small, color: colors.muted, textAlign: 'right' },
  panel: { borderRadius: radius, overflow: 'hidden' },
  panelHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: space.md, paddingHorizontal: space.lg },
  panelTitle: { fontSize: font.title, fontWeight: '800', color: colors.card },
  panelTag: { fontSize: 11, fontWeight: '700', letterSpacing: 1, color: colors.card, opacity: 0.85 },
  panelBody: { padding: space.lg, gap: space.md },
  match: { alignSelf: 'flex-start', backgroundColor: colors.gold, borderRadius: 999, paddingVertical: 5, paddingHorizontal: space.md },
  matchText: { color: colors.card, fontSize: font.small, fontWeight: '700' },
  point: { flexDirection: 'row', gap: space.sm },
  check: { fontSize: font.body, fontWeight: '800', lineHeight: 23 },
  pointText: { flex: 1, fontSize: font.body, lineHeight: 23, color: colors.text },
  caution: { backgroundColor: colors.card, borderRadius: 10, padding: space.md, gap: 2 },
  cautionLabel: { fontSize: 12, fontWeight: '700', color: colors.muted, textTransform: 'uppercase', letterSpacing: 0.5 },
  cautionText: { fontSize: font.small, lineHeight: 20, color: colors.text },
  source: { gap: 2, paddingTop: space.sm },
});
