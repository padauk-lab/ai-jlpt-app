// Wait for a request, but for at least `ms` milliseconds, so a loading
// screen isn't just a flash. On a slow network it adds no extra wait.
export async function withMinimumTime<T>(request: Promise<T>, ms = 3500): Promise<T> {
  const [result] = await Promise.all([request, new Promise((resolve) => setTimeout(resolve, ms))]);
  return result;
}
