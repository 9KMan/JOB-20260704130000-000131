// Synthetic API route: NO auth check, returns DB rows directly.
export async function GET() {
  const data = await fetch("https://example.com/api").then((r) => r.json());
  return Response.json(data);
}
