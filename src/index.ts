function requireName(name: string): string {
  const trimmed = name.trim();
  if (trimmed === "") throw new Error("name must not be empty");
  return trimmed;
}

export function greet(name: string): string {
  return `Hello, ${requireName(name)}!`;
}

export function farewell(name: string): string {
  return `Goodbye, ${requireName(name)}!`;
}
