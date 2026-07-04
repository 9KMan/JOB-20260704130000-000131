"use client";

// Mock WhatsApp-style AI conversation component.
//
// IMPORTANT: this is a *demo skeleton*. The conversation uses a deterministic
// local "fake LLM" provider that lives in /api/chat. NO real LLM call is made
// and NO network traffic leaves the demo. Replace with a real provider after
// kickoff, gated by an env flag and rate-limited.

import { useEffect, useRef, useState } from "react";

type Msg = { role: "user" | "assistant"; text: string; ts: number };

const SUGGESTIONS = [
  "What does this audit check?",
  "How long does a typical sprint 1 take?",
  "Can you help with Supabase RLS?",
];

export default function WhatsappDemoPage() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      text:
        "Hi 👋 I'm a *demo* assistant running entirely in the browser via /api/chat. " +
        "I'm here to show what a WhatsApp-style conversation over your SaaS audit might look like. " +
        "Try one of the suggestions below.",
      ts: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: 1e9, behavior: "smooth" });
  }, [messages]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setMessages((m) => [...m, { role: "user", text: trimmed, ts: Date.now() }]);
    setInput("");
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ message: trimmed }),
      });
      const data = await res.json();
      setMessages((m) => [
        ...m,
        { role: "assistant", text: data.reply ?? "(no reply)", ts: Date.now() },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Network error — please retry.", ts: Date.now() },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col bg-[#ECE5DD]">
      <header className="sticky top-0 z-10 flex items-center gap-3 border-b border-emerald-700 bg-emerald-600 px-4 py-3 text-white">
        <div className="h-9 w-9 rounded-full bg-white/20" aria-hidden />
        <div>
          <div className="text-sm font-semibold">Audit Bot (demo)</div>
          <div className="text-xs opacity-80">mocked provider · no LLM call</div>
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 space-y-2 overflow-y-auto px-3 py-4">
        {messages.map((m, i) => (
          <Bubble key={i} msg={m} />
        ))}
        {busy && (
          <div className="max-w-[70%] rounded-lg bg-white px-3 py-2 text-sm text-slate-500 shadow">
            typing…
          </div>
        )}
      </div>

      <div className="border-t border-slate-300 bg-white px-3 py-2">
        <div className="mb-2 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              disabled={busy}
              className="rounded-full border border-emerald-600 px-3 py-1 text-xs text-emerald-700 hover:bg-emerald-50 disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>
        <form
          className="flex items-center gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={busy}
            placeholder="Type a message"
            className="flex-1 rounded-full border border-slate-300 bg-white px-4 py-2 text-sm focus:border-emerald-600 focus:outline-none"
          />
          <button
            type="submit"
            disabled={busy || !input.trim()}
            className="rounded-full bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>
    </main>
  );
}

function Bubble({ msg }: { msg: Msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[75%] rounded-lg px-3 py-2 text-sm shadow ${
          isUser ? "bg-emerald-200" : "bg-white"
        }`}
      >
        {msg.text}
      </div>
    </div>
  );
}
