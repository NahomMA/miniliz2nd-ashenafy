import { StatusBar } from 'expo-status-bar';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, ErrorNote } from '@/components/ui';
import { errorMessage } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { colors, font, radius, space } from '@/lib/theme';

const DEMO = { email: 'demo@codelinc.app', password: 'Demo2026!' };

export default function LoginScreen() {
  const { login, register } = useAuth();
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await (creating ? register(name.trim(), email.trim(), password) : login(email.trim(), password));
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  };

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="dark" />
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Text style={styles.brand}>RightSize</Text>
          <Text style={styles.tagline}>A calm, clear way to find the life insurance coverage that fits your family.</Text>

          {creating ? (
            <TextInput
              style={styles.input}
              placeholder="First name"
              placeholderTextColor={colors.muted}
              accessibilityLabel="First name"
              value={name}
              onChangeText={setName}
              autoCapitalize="words"
            />
          ) : null}
          <TextInput
            style={styles.input}
            placeholder="Email"
            placeholderTextColor={colors.muted}
            accessibilityLabel="Email"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="email-address"
          />
          <TextInput
            style={styles.input}
            placeholder="Password"
            placeholderTextColor={colors.muted}
            accessibilityLabel="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            onSubmitEditing={submit}
          />
          <ErrorNote message={error} />
          <Button label={creating ? 'Create account' : 'Sign in'} onPress={submit} busy={busy} />

          <Pressable accessibilityRole="button" onPress={() => setCreating(!creating)} style={styles.link}>
            <Text style={styles.linkText}>{creating ? 'I already have an account' : 'Create an account'}</Text>
          </Pressable>
          {creating ? null : (
            <Pressable
              accessibilityRole="button"
              onPress={() => {
                setEmail(DEMO.email);
                setPassword(DEMO.password);
              }}
              style={styles.link}>
              <Text style={styles.linkText}>Use the demo account</Text>
            </Pressable>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  flex: { flex: 1 },
  content: { flexGrow: 1, justifyContent: 'center', padding: space.xl, gap: space.md },
  brand: { fontSize: 40, fontWeight: '800', color: colors.primary, textAlign: 'center' },
  tagline: { fontSize: font.body, color: colors.muted, textAlign: 'center', marginBottom: space.lg, lineHeight: 22 },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius,
    backgroundColor: colors.card,
    paddingHorizontal: space.lg,
    fontSize: font.body,
    color: colors.text,
  },
  link: { minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  linkText: { color: colors.primary, fontSize: font.body, fontWeight: '600' },
});
