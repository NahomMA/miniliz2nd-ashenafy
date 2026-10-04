import { StatusBar } from "expo-status-bar";
import { useState } from "react";
import {
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Button, ErrorNote } from "@/components/ui";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { colors, font, radius, shadow, space } from "@/lib/theme";

const DEMO = { email: "demo@codelinc.app", password: "Demo2026!" };

export default function LoginScreen() {
  const { login, register } = useAuth();
  const insets = useSafeAreaInsets();
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await (creating
        ? register(name.trim(), email.trim(), password)
        : login(email.trim(), password));
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  };

  return (
    <View style={styles.screen}>
      <StatusBar style="light" />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
          bounces={false}
        >
          <View style={[styles.hero, { paddingTop: insets.top + space.xl }]}>
            <View style={styles.mascotRing}>
              <Image
                source={require("@/assets/images/liv.png")}
                style={styles.mascot}
                accessibilityLabel="LifeSize guide"
              />
            </View>
            <Text style={styles.brand}>LifeSize</Text>
            <Text style={styles.tagline}>
              A calm, clear way to find the life insurance coverage that fits
              your family.
            </Text>
          </View>

          <View style={styles.form}>
            <Text style={styles.formTitle}>
              {creating ? "Create your account" : "Welcome back"}
            </Text>
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
              returnKeyType="go"
              onSubmitEditing={submit}
            />
            <TextInput
              style={styles.input}
              placeholder="Password"
              placeholderTextColor={colors.muted}
              accessibilityLabel="Password"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              returnKeyType="go"
              onSubmitEditing={submit}
            />
            <ErrorNote message={error} />
            <Button
              label={creating ? "Create account" : "Sign in"}
              onPress={submit}
              busy={busy}
            />
          </View>

          <Pressable
            accessibilityRole="button"
            onPress={() => setCreating(!creating)}
            style={styles.link}
          >
            <Text style={styles.linkText}>
              {creating ? "I already have an account" : "Create an account"}
            </Text>
          </Pressable>
          {creating ? null : (
            <Pressable
              accessibilityRole="button"
              onPress={() => {
                setEmail(DEMO.email);
                setPassword(DEMO.password);
              }}
              style={styles.link}
            >
              <Text style={styles.linkText}>Use the demo account</Text>
            </Pressable>
          )}
          <Text
            style={[
              styles.footnote,
              { paddingBottom: insets.bottom + space.lg },
            ]}
          >
            Educational estimates only. Your password is stored hashed and your
            session stays encrypted on this device.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  flex: { flex: 1 },
  scroll: { flexGrow: 1 },
  hero: {
    backgroundColor: colors.primary,
    alignItems: "center",
    paddingHorizontal: space.xl,
    paddingBottom: 64,
    borderBottomLeftRadius: 32,
    borderBottomRightRadius: 32,
    gap: space.sm,
  },
  mascotRing: { padding: 4, borderRadius: 64, backgroundColor: colors.gold },
  mascot: {
    width: 112,
    height: 112,
    borderRadius: 56,
    backgroundColor: colors.card,
  },
  brand: {
    fontSize: 40,
    fontWeight: "800",
    color: colors.card,
    letterSpacing: -0.5,
  },
  tagline: {
    fontSize: font.body,
    color: colors.rose,
    textAlign: "center",
    lineHeight: 23,
  },
  form: {
    marginTop: -40,
    marginHorizontal: space.lg,
    padding: space.xl,
    gap: space.md,
    backgroundColor: colors.card,
    borderRadius: 20,
    ...shadow,
  },
  formTitle: { fontSize: font.title, fontWeight: "700", color: colors.text },
  input: {
    minHeight: 50,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius,
    backgroundColor: colors.bg,
    paddingHorizontal: space.lg,
    fontSize: font.body,
    color: colors.text,
  },
  link: {
    minHeight: 44,
    alignItems: "center",
    justifyContent: "center",
    marginTop: space.xs,
  },
  linkText: { color: colors.primary, fontSize: font.body, fontWeight: "600" },
  footnote: {
    marginTop: "auto",
    paddingTop: space.lg,
    paddingHorizontal: space.xl,
    fontSize: 12,
    lineHeight: 17,
    color: colors.muted,
    textAlign: "center",
  },
});
