import { describe, expect, it } from "vitest";
import { run } from "./cli.js";

const usage = { code: 2, stdout: "", stderr: "usage: cli <greet|farewell> <name>\n" };

describe("run", () => {
  it("greets", () => expect(run(["greet", "Ada"])).toEqual({ code: 0, stdout: "Hello, Ada!\n", stderr: "" }));
  it("says farewell", () =>
    expect(run(["farewell", "Ada"])).toEqual({ code: 0, stdout: "Goodbye, Ada!\n", stderr: "" }));

  it.each<[string, readonly string[]]>([
    ["an unknown command", ["wave", "Ada"]],
    ["an inherited property as command", ["toString", "Ada"]],
    ["no command", []],
    ["a missing name", ["greet"]],
    ["a blank name", ["greet", "  "]],
    ["an empty name", ["farewell", ""]],
    ["extra arguments", ["greet", "Ada", "Lovelace"]],
  ])("prints usage for %s", (_case, args) => expect(run(args)).toEqual(usage));
});
