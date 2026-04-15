const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const VALIDATE_TIMEOUT_MS = 90_000;

export type ValidateResponse =
  | { valid: true; company_name: string }
  | { valid: false; error: string };

export async function validateTicker(ticker: string): Promise<ValidateResponse> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), VALIDATE_TIMEOUT_MS);
  try {
    const res = await fetch(`${API_URL}/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker }),
      signal: controller.signal,
    });
    if (!res.ok) {
      return { valid: false, error: "Something went wrong. Try again in a moment." };
    }
    return await res.json();
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      return {
        valid: false,
        error: "Market data is slow to respond right now. Try again in a moment.",
      };
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}
