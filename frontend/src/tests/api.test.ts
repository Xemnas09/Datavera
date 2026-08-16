import { describe, it, expect, beforeEach } from "vitest";
import { getSessionId } from "../lib/api";

describe("Frontend API utilities", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("generates and stores a unique session ID in localStorage", () => {
    const sid1 = getSessionId();
    expect(sid1).toBeTruthy();
    expect(typeof sid1).toBe("string");

    const sid2 = getSessionId();
    expect(sid2).toBe(sid1);
  });
});
