export type GithubRepository = {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  homepage: string | null;
  language: string | null;
  stargazers_count: number;
  topics: string[];
  fork: boolean;
  archived: boolean;
  updated_at: string;
  default_branch: string;
}

const GITHUB_API = "https://api.github.com";
const GITHUB_USERNAME =
  import.meta.env.VITE_GITHUB_USERNAME?.trim() || "skc-charchit";

function isGithubRepository(value: unknown): value is GithubRepository {
  if (typeof value !== "object" || value === null) return false;
  const repository = value as Record<string, unknown>;
  return (
    typeof repository.id === "number" &&
    typeof repository.name === "string" &&
    typeof repository.full_name === "string" &&
    typeof repository.html_url === "string" &&
    typeof repository.updated_at === "string" &&
    (typeof repository.description === "string" || repository.description === null) &&
    (typeof repository.homepage === "string" || repository.homepage === null) &&
    (typeof repository.language === "string" || repository.language === null) &&
    typeof repository.stargazers_count === "number" &&
    Array.isArray(repository.topics) &&
    repository.topics.every((topic) => typeof topic === "string") &&
    typeof repository.fork === "boolean" &&
    typeof repository.archived === "boolean" &&
    typeof repository.default_branch === "string"
  );
}

const readmeCache = new Map<string, string | null>();

export async function getGithubRepositories(
  signal?: AbortSignal,
): Promise<GithubRepository[]> {
  const response = await fetch(
    `${GITHUB_API}/users/${encodeURIComponent(GITHUB_USERNAME)}/repos?type=owner&sort=updated&per_page=100`,
    {
      headers: { Accept: "application/vnd.github+json" },
      signal,
    },
  );

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`The GitHub profile @${GITHUB_USERNAME} was not found.`);
    }
    if (response.status === 403 || response.status === 429) {
      throw new Error(
        "GitHub is temporarily limiting requests. Please try again in a little while.",
      );
    }
    throw new Error(`GitHub repositories could not be loaded (${response.status}).`);
  }

  const payload: unknown = await response.json();
  if (!Array.isArray(payload) || !payload.every(isGithubRepository)) {
    throw new Error("GitHub returned repository data in an unexpected format.");
  }

  return payload
    .filter((repository) => !repository.fork && !repository.archived)
    .sort(
      (left, right) =>
        new Date(right.updated_at).getTime() -
        new Date(left.updated_at).getTime(),
    );
}

export async function getRepositoryReadme(
  repository: GithubRepository,
  signal?: AbortSignal,
): Promise<string | null> {
  const cachedReadme = readmeCache.get(repository.full_name);
  if (cachedReadme !== undefined) return cachedReadme;

  const response = await fetch(
    `${GITHUB_API}/repos/${repository.full_name
      .split("/")
      .map(encodeURIComponent)
      .join("/")}/readme`,
    {
      headers: {
        Accept: "application/vnd.github.raw+json",
      },
      signal,
    },
  );

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

export const githubUsername = GITHUB_USERNAME;
