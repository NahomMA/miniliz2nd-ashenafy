import { router } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { Button, ErrorNote } from "@/components/ui";
import { api, errorMessage } from "@/lib/api";
import { useConversation } from "@/lib/conversation";
import { colors, font, formatUSD, shadow, space } from "@/lib/theme";
import type { AssessmentSummary } from "@/lib/types";

const DATE = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

function Item({
  item,
  onPress,
}: {
  item: AssessmentSummary;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.item, pressed && { opacity: 0.7 }]}
    >
      <View
        style={[styles.stripe, !item.done && { backgroundColor: colors.gold }]}
      />
      <View style={styles.itemText}>
        <Text style={styles.caption}>
          {item.done ? "Coverage goal" : "In progress"}
        </Text>
        <Text style={styles.amount}>
          {item.total_need === null
            ? "Not finished yet"
            : formatUSD(item.total_need)}
        </Text>
        <Text style={styles.muted}>
          {DATE.format(new Date(item.created_at))}
        </Text>
      </View>
      <View
        style={[
          styles.chip,
          !item.done && { backgroundColor: colors.goldSoft },
        ]}
      >
        <Text style={[styles.chipText, !item.done && { color: colors.text }]}>
          {item.done ? "View" : "Continue"}
        </Text>
      </View>
    </Pressable>
  );
}

export default function HistoryScreen() {
  const open = useConversation((state) => state.open);
  const [items, setItems] = useState<AssessmentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () =>
      api<{ items: AssessmentSummary[] }>("/assessments")
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
    router.dismissTo(item.done ? "/results" : "/");
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
      ListEmptyComponent={
        <View style={styles.empty}>
          <Image
            source={require("@/assets/images/liv.png")}
            style={styles.emptyImage}
            accessibilityLabel="LifeSize guide"
          />
          <Text style={styles.emptyTitle}>Nothing here yet</Text>
          <Text style={styles.muted}>
            Finish a conversation and your assessment will be saved here.
          </Text>
        </View>
      }
      renderItem={({ item }) => (
        <Item item={item} onPress={() => void view(item)} />
      )}
    />
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: space.xl,
    gap: space.md,
  },
  list: { padding: space.lg, gap: space.md, flexGrow: 1 },
  item: {
    flexDirection: "row",
    alignItems: "center",
    gap: space.md,
    backgroundColor: colors.card,
    borderRadius: 18,
    overflow: "hidden",
    paddingRight: space.lg,
    ...shadow,
  },
  stripe: { width: 6, alignSelf: "stretch", backgroundColor: colors.primary },
  itemText: { flex: 1, gap: 2, paddingVertical: space.lg },
  caption: {
    fontSize: 12,
    fontWeight: "700",
    color: colors.muted,
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  amount: { fontSize: 22, fontWeight: "800", color: colors.text },
  muted: { fontSize: font.small, color: colors.muted, textAlign: "left" },
  chip: {
    backgroundColor: colors.primarySoft,
    borderRadius: 999,
    paddingVertical: space.sm,
    paddingHorizontal: space.lg,
  },
  chipText: { fontSize: font.small, fontWeight: "700", color: colors.primary },
  empty: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: space.sm,
    padding: space.xl,
  },
  emptyImage: { width: 96, height: 96, borderRadius: 48 },
  emptyTitle: { fontSize: font.title, fontWeight: "700", color: colors.text },
});
