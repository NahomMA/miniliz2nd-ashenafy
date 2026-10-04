import { router } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';

import { Button, ErrorNote } from '@/components/ui';
import { api, errorMessage } from '@/lib/api';
import { useConversation } from '@/lib/conversation';
import { colors, font, formatUSD, radius, space } from '@/lib/theme';
import type { AssessmentSummary } from '@/lib/types';

export default function HistoryScreen() {
  const open = useConversation((state) => state.open);
  const [items, setItems] = useState<AssessmentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () =>
      api<{ items: AssessmentSummary[] }>('/assessments')
        .then((page) => setItems(page.items))
        .catch((e) => setError(errorMessage(e))),
    [],
  );

  const retry = () => {
    setError(null);
    void load();
  };

  useEffect(() => {
    void load();
  }, [load]);

  const view = async (item: AssessmentSummary) => {
    await open(item.id);
    router.dismissTo(item.done ? '/results' : '/');
  };

  if (error) {
    return (
      <View style={styles.center}>
        <ErrorNote message={error} />
        <Button label="Try again" variant="quiet" onPress={retry} />
      </View>
    );
  }
  if (items === null) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <FlatList
      data={items}
      keyExtractor={(item) => String(item.id)}
      contentContainerStyle={styles.list}
      ListEmptyComponent={<Text style={styles.muted}>No assessments yet. Finish a conversation and it will appear here.</Text>}
      renderItem={({ item }) => (
        <Pressable accessibilityRole="button" onPress={() => void view(item)} style={styles.item}>
          <View style={styles.itemText}>
            <Text style={styles.title}>{item.total_need === null ? 'In progress' : formatUSD(item.total_need)}</Text>
            <Text style={styles.muted}>{new Date(item.created_at).toLocaleString()}</Text>
          </View>
          <Text style={styles.open}>{item.done ? 'View' : 'Continue'}</Text>
        </Pressable>
      )}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: space.xl, gap: space.md },
  list: { padding: space.lg, gap: space.md },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: 64,
    backgroundColor: colors.card,
    borderRadius: radius,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space.lg,
  },
  itemText: { gap: space.xs },
  title: { fontSize: font.title, fontWeight: '700', color: colors.text },
  muted: { fontSize: font.small, color: colors.muted },
  open: { fontSize: font.body, fontWeight: '700', color: colors.primary },
});
