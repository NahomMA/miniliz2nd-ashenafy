/** Small shared building blocks. */
import type { ReactNode } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
  type ViewStyle,
} from "react-native";

import { colors, font, radius, shadow, space } from "@/lib/theme";

type ButtonProps = {
  label: string;
  onPress: () => void;
  busy?: boolean;
  disabled?: boolean;
  variant?: "primary" | "quiet";
};

export function Button({
  label,
  onPress,
  busy,
  disabled,
  variant = "primary",
}: ButtonProps) {
  const quiet = variant === "quiet";
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      disabled={disabled || busy}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        quiet ? styles.buttonQuiet : styles.buttonPrimary,
        (pressed || disabled || busy) && styles.dimmed,
      ]}
    >
      {busy ? (
        <ActivityIndicator color={quiet ? colors.primary : colors.card} />
      ) : (
        <Text style={[styles.buttonLabel, quiet && { color: colors.primary }]}>
          {label}
        </Text>
      )}
    </Pressable>
  );
}

export function Card({
  title,
  children,
  style,
}: {
  title?: string;
  children: ReactNode;
  style?: ViewStyle;
}) {
  return (
    <View style={[styles.card, style]}>
      {title ? <Text style={styles.cardTitle}>{title}</Text> : null}
      {children}
    </View>
  );
}

export function ErrorNote({ message }: { message: string | null }) {
  return message ? (
    <Text accessibilityRole="alert" style={styles.error}>
      {message}
    </Text>
  ) : null;
}

export function Disclaimer() {
  return (
    <Text style={styles.disclaimer}>
      This is an educational estimate, not financial advice. It does not
      recommend any product. Talk with a licensed professional before making
      decisions.
    </Text>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 48,
    borderRadius: radius,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: space.lg,
  },
  buttonPrimary: { backgroundColor: colors.primary },
  buttonQuiet: {
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: colors.primary,
  },
  buttonLabel: { color: colors.card, fontSize: font.body, fontWeight: "600" },
  dimmed: { opacity: 0.6 },
  card: {
    backgroundColor: colors.card,
    borderRadius: 18,
    padding: space.lg,
    gap: space.sm,
    ...shadow,
  },
  cardTitle: { fontSize: font.title, fontWeight: "700", color: colors.text },
  error: { color: colors.danger, fontSize: font.small },
  disclaimer: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 18,
    textAlign: "center",
  },
});
