export type ProjectSummary = {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  language: string | null;
  default_branch: string;
};

const GITHUB_API = "https://api.github.com";
const readmeCache = new Map<string, string | null>();

export async function getRepositoryReadme(
  repository: ProjectSummary,
  signal?: AbortSignal,
): Promise<string | null> {
  const cachedReadme = readmeCache.get(repository.full_name);
  if (cachedReadme !== undefined) return cachedReadme;

  const repositoryPath = repository.full_name
    .split("/")
    .map(encodeURIComponent)
    .join("/");
  const response = await fetch(`${GITHUB_API}/repos/${repositoryPath}/readme`, {
    headers: { Accept: "application/vnd.github.raw+json" },
    signal,
  });

  if (response.status === 404) {
    readmeCache.set(repository.full_name, null);
    return null;
  }
  if (response.status === 403 || response.status === 429) {
    throw new Error(
      "GitHub is temporarily limiting requests. Please try again in a little while.",
    );
  }
  if (!response.ok) {
    throw new Error(`The README could not be loaded (${response.status}).`);
  }

  const readme = await response.text();
  if (!readme.trim()) {
    readmeCache.set(repository.full_name, null);
    return null;
  }
  readmeCache.set(repository.full_name, readme);
  return readme;
}
