import { fetchEventSource } from "@microsoft/fetch-event-source";
import type { Briefing, ErrorEvent, HeaderData, ProgressEvent } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ResearchHandlers {
  onProgress?: (ev: ProgressEvent) => void;
  onHeader?: (ev: HeaderData) => void;
  onResult?: (ev: Briefing) => void;
  onError?: (ev: ErrorEvent) => void;
}

class ResearchFatalError extends Error {}

export function streamResearch(
  ticker: string,
  handlers: ResearchHandlers,
  signal?: AbortSignal,
): Promise<void> {
  return fetchEventSource(`${API_URL}/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ ticker }),
    signal,
    openWhenHidden: true,
    onopen: async (res) => {
      if (!res.ok) {
        throw new ResearchFatalError(`Research stream failed (${res.status})`);
      }
    },
    onmessage: (msg) => {

      console.log(msg)
      if (!msg.event || !msg.data) return;
      let parsed: unknown;
      try {
        parsed = JSON.parse(msg.data);
      } catch {
        return;
      }
      switch (msg.event) {
        case "progress":
          handlers.onProgress?.(parsed as ProgressEvent);
          return;
        case "header":
          handlers.onHeader?.(parsed as HeaderData);
          return;
        case "result":
          handlers.onResult?.(parsed as Briefing);
          return;
        case "error":
          handlers.onError?.(parsed as ErrorEvent);
          return;
      }
    },
    onclose: () => {
      throw new ResearchFatalError("stream closed");
    },
    onerror: (err) => {
      if (err instanceof ResearchFatalError) throw err;
      handlers.onError?.({
        message: "Lost connection to the research stream.",
      });
      throw err;
    },
  });
}
