import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useEffect, type ReactNode } from "react";
import { ActivityIndicator, Platform, StyleSheet, View } from "react-native";

import { useAuth } from "@/lib/auth";
import { colors, shadow } from "@/lib/theme";

const PHONE_WIDTH = 430;

/** On a wide browser window, show the app as a centred phone-width column instead of stretching it. */
function Frame({ children }: { children: ReactNode }) {
  if (Platform.OS !== "web") return <>{children}</>;
  return (
    <View style={styles.backdrop}>
      <View style={styles.phone}>{children}</View>
    </View>
  );
}

export default function RootLayout() {
  const { ready, token, restore } = useAuth();

  useEffect(() => {
    void restore();
  }, [restore]);

  if (!ready) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <Frame>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.primary },
          headerTintColor: colors.card,
          headerTitleStyle: { fontWeight: "700" },
          contentStyle: { backgroundColor: colors.bg },
        }}
      >
        <Stack.Protected guard={token !== null}>
          <Stack.Screen
            name="index"
            options={{ title: "Your coverage guide" }}
          />
          <Stack.Screen name="results" options={{ title: "Your results" }} />
          <Stack.Screen
            name="history"
            options={{ title: "Past assessments" }}
          />
        </Stack.Protected>
        <Stack.Protected guard={token === null}>
          <Stack.Screen name="login" options={{ headerShown: false }} />
        </Stack.Protected>
      </Stack>
    </Frame>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.bg,
  },
  backdrop: {
    flex: 1,
    alignItems: "center",
    backgroundColor: colors.primaryDark,
  },
  phone: {
    flex: 1,
    width: "100%",
    maxWidth: PHONE_WIDTH,
    backgroundColor: colors.bg,
    overflow: "hidden",
    ...shadow,
  },
});
