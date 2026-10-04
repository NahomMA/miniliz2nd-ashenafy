import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { useAuth } from '@/lib/auth';
import { colors } from '@/lib/theme';

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
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.primary },
          headerTintColor: colors.card,
          headerTitleStyle: { fontWeight: '700' },
          contentStyle: { backgroundColor: colors.bg },
        }}>
        <Stack.Protected guard={token !== null}>
          <Stack.Screen name="index" options={{ title: 'Your coverage guide' }} />
          <Stack.Screen name="results" options={{ title: 'Your results' }} />
          <Stack.Screen name="history" options={{ title: 'Past assessments' }} />
        </Stack.Protected>
        <Stack.Protected guard={token === null}>
          <Stack.Screen name="login" options={{ headerShown: false }} />
        </Stack.Protected>
      </Stack>
    </>
  );
}

const styles = StyleSheet.create({
  loading: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg },
});
