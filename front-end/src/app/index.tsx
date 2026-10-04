import { router, Stack } from "expo-router";
import { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Image,
  Keyboard,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import {
  SafeAreaView,
  useSafeAreaInsets,
} from "react-native-safe-area-context";

import { Button, ErrorNote } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useConversation } from "@/lib/conversation";
import { colors, font, radius, space } from "@/lib/theme";
import type { Message } from "@/lib/types";

const MAX_LENGTH = 1000;
// Navigation header height below the status bar. The keyboard offset is the status bar inset plus this.
const HEADER_HEIGHT = Platform.OS === "ios" ? 44 : 56;

function Bubble({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <View style={[styles.bubble, styles.mine]}>
        <Text style={[styles.bubbleText, { color: colors.card }]}>
          {message.text}
        </Text>
      </View>
    );
  }
  return (
    <View style={styles.assistantRow}>
      <Image
        source={require("@/assets/images/liv.png")}
        style={styles.avatar}
        accessibilityLabel="LifeSize guide"
      />
      <View style={[styles.bubble, styles.theirs]}>
        <Text style={styles.bubbleText}>{message.text}</Text>
      </View>
    </View>
  );
}

function HeaderLink({
  label,
  onPress,
}: {
  label: string;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      hitSlop={12}
      style={styles.headerLink}
    >
      <Text style={styles.headerLinkText}>{label}</Text>
    </Pressable>
  );
}

export default function ChatScreen() {
  const { id, messages, assessment, busy, error, start, send, reset } =
    useConversation();
  const logout = useAuth((state) => state.logout);
  const [draft, setDraft] = useState("");
  const list = useRef<FlatList<Message>>(null);
  const insets = useSafeAreaInsets();

  useEffect(() => {
    if (id === null) void start();
  }, [id, start]);

  // When the result arrives, lower the keyboard so the answer and the results button are in view.
  useEffect(() => {
    if (assessment) Keyboard.dismiss();
  }, [assessment]);

  const submit = () => {
    const text = draft.trim();
    if (!text || busy) return;
    setDraft("");
    void send(text);
  };

  // In a browser, Enter sends and Shift+Enter adds a line (phones use the keyboard's send key).
  const sendOnEnter = (event: {
    nativeEvent: { key: string; shiftKey?: boolean };
    preventDefault?: () => void;
  }) => {
    const pressed = event.nativeEvent;
    if (Platform.OS === "web" && pressed.key === "Enter" && !pressed.shiftKey) {
      event.preventDefault?.();
      submit();
    }
  };

  const signOut = () => {
    reset();
    void logout();
  };

  return (
    <SafeAreaView style={styles.screen} edges={["bottom"]}>
      <Stack.Screen
        options={{
          headerRight: () => (
            <View style={styles.headerLinks}>
              <HeaderLink
                label="History"
                onPress={() => router.push("/history")}
              />
              <HeaderLink label="Sign out" onPress={signOut} />
            </View>
          ),
        }}
      />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior="padding"
        keyboardVerticalOffset={insets.top + HEADER_HEIGHT}
      >
        <FlatList
          ref={list}
          data={messages}
          keyExtractor={(_, index) => String(index)}
          renderItem={({ item }) => <Bubble message={item} />}
          contentContainerStyle={styles.messages}
          onContentSizeChange={() =>
            list.current?.scrollToEnd({ animated: true })
          }
          ListFooterComponent={
            <View style={styles.footer}>
              {busy ? (
                <View style={styles.working}>
                  <ActivityIndicator color={colors.primary} />
                  <Text style={styles.typing}>
                    {messages.length > 8
                      ? "Working out your numbers…"
                      : "Thinking…"}
                  </Text>
                </View>
              ) : null}
              <ErrorNote message={error} />
              {error && id === null ? (
                <Button
                  label="Try again"
                  variant="quiet"
                  onPress={() => void start()}
                />
              ) : null}
              {assessment ? (
                <Button
                  label="Start a new assessment"
                  variant="quiet"
                  onPress={() => void start()}
                />
              ) : null}
            </View>
          }
        />
        {assessment ? (
          <View style={styles.resultsBar}>
            <Button
              label="See your results"
              onPress={() => router.push("/results")}
            />
          </View>
        ) : null}
        <View style={styles.composer}>
          <TextInput
            style={styles.input}
            placeholder="Type your answer"
            placeholderTextColor={colors.muted}
            accessibilityLabel="Your answer"
            value={draft}
            onChangeText={setDraft}
            maxLength={MAX_LENGTH}
            multiline
            submitBehavior="submit"
            returnKeyType="send"
            onSubmitEditing={submit}
            onKeyPress={sendOnEnter}
            editable={id !== null}
          />
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Send"
            onPress={submit}
            disabled={busy || !draft.trim()}
            style={[styles.send, (busy || !draft.trim()) && styles.sendOff]}
          >
            <Text
              style={[
                styles.sendText,
                (busy || !draft.trim()) && { color: colors.muted },
              ]}
            >
              Send
            </Text>
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  flex: { flex: 1 },
  working: { flexDirection: "row", alignItems: "center", gap: space.sm },
  resultsBar: {
    paddingHorizontal: space.md,
    paddingTop: space.md,
    backgroundColor: colors.card,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  // The web header has no side padding of its own, so the links would touch the edge.
  headerLinks: {
    flexDirection: "row",
    gap: space.lg,
    paddingRight: Platform.OS === "web" ? space.lg : 0,
  },
  headerLink: { minHeight: 44, justifyContent: "center" },
  headerLinkText: {
    color: colors.card,
    fontSize: font.small,
    fontWeight: "600",
  },
  messages: { padding: space.lg, gap: space.sm },
  bubble: {
    maxWidth: "85%",
    borderRadius: radius,
    paddingVertical: space.md,
    paddingHorizontal: space.lg,
  },
  mine: {
    alignSelf: "flex-end",
    backgroundColor: colors.primary,
    borderBottomRightRadius: 4,
  },
  theirs: {
    flexShrink: 1,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderBottomLeftRadius: 4,
  },
  bubbleText: { fontSize: font.body, lineHeight: 23, color: colors.text },
  assistantRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: space.sm,
    paddingRight: space.xl,
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
  },
  footer: { gap: space.md, paddingTop: space.sm },
  typing: { color: colors.muted, fontSize: font.small, fontStyle: "italic" },
  composer: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: space.sm,
    padding: space.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.card,
  },
  input: {
    flex: 1,
    minHeight: 48,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius,
    paddingHorizontal: space.lg,
    paddingVertical: space.md,
    fontSize: font.body,
    color: colors.text,
    backgroundColor: colors.bg,
  },
  send: {
    minHeight: 48,
    minWidth: 64,
    borderRadius: radius,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: space.lg,
  },
  sendOff: { backgroundColor: colors.border },
  sendText: { color: colors.card, fontSize: font.body, fontWeight: "700" },
});
