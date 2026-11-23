import { pathToFileURL } from "node:url";
import { farewell, greet } from "./index.js";

interface Result {
  code: number;
  stdout: string;
  stderr: string;
}

const commands: Readonly<Record<string, (name: string) => string>> = { greet, farewell };
const usage: Result = { code: 2, stdout: "", stderr: "usage: cli <greet|farewell> <name>\n" };

export function run(args: readonly string[]): Result {
  if (args.length !== 2) return usage;
  const [command = "", name = ""] = args;
  const say = Object.hasOwn(commands, command) ? commands[command] : undefined;
  if (say === undefined) return usage;
  try {
    return { code: 0, stdout: `${say(name)}\n`, stderr: "" };
  } catch (error) {
    if (error instanceof Error && error.message === "name must not be empty") return usage;
    throw error;
  }
}

const entry = process.argv[1];
if (entry !== undefined && import.meta.url === pathToFileURL(entry).href) {
  const { code, stdout, stderr } = run(process.argv.slice(2));
  process.stdout.write(stdout);
  process.stderr.write(stderr);
  process.exitCode = code;
}
