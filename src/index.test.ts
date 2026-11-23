import { describe, expect, it } from "vitest";
import * as lib from "./index.js";
import { farewell, greet } from "./index.js";

describe("greet", () => {
  it("greets by name", () => expect(greet(" Ada ")).toBe("Hello, Ada!"));
  it("rejects an empty name", () => expect(() => greet("")).toThrow("name must not be empty"));
  it("rejects a blank name", () => expect(() => greet("  ")).toThrow("name must not be empty"));
});

describe("farewell", () => {
  it("says goodbye by trimmed name", () => expect(farewell(" Ada ")).toBe("Goodbye, Ada!"));
  it("rejects an empty name", () => expect(() => farewell("")).toThrow("name must not be empty"));
  it("rejects a blank name", () => expect(() => farewell(" \t\n ")).toThrow("name must not be empty"));
});

describe("public API", () => {
  it("exports exactly greet and farewell", () => expect(Object.keys(lib).sort()).toEqual(["farewell", "greet"]));
});
