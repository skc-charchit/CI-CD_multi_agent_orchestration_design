import { useEffect, useMemo, useRef, useState } from "react";
import {
  getGithubRepositories,
  githubUsername,
  type GithubRepository,
} from "./api";

type LoadState = "loading" | "ready" | "error";

function ArrowIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <path d="M4.5 10h10m-4-4 4 4-4 4" />
    </svg>
  );
}

function GithubIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 .9a11.1 11.1 0 0 0-3.51 21.63c.55.1.76-.24.76-.53v-2.07c-3.1.67-3.76-1.32-3.76-1.32-.5-1.28-1.24-1.62-1.24-1.62-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 1.72 2.6 1.22 3.23.93.1-.73.39-1.22.7-1.5-2.48-.28-5.09-1.24-5.09-5.52 0-1.22.44-2.22 1.16-3-.12-.28-.5-1.42.11-2.96 0 0 .95-.3 3.05 1.15a10.6 10.6 0 0 1 5.55 0c2.11-1.43 3.05-1.15 3.05-1.15.61 1.54.23 2.68.11 2.96.72.78 1.16 1.78 1.16 3.01 0 4.29-2.61 5.23-5.1 5.51.4.35.75 1.03.75 2.08V22c0 .29.2.63.77.52A11.1 11.1 0 0 0 12 .9Z" />
    </svg>
  );
}

function SparkIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m12 2 1.85 7.15L21 11l-7.15 1.85L12 20l-1.85-7.15L3 11l7.15-1.85L12 2Z" />
      <path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z" />
    </svg>
  );
}

function formatUpdatedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Recently updated";
  return `Updated ${new Intl.DateTimeFormat("en", {
    month: "short",
    year: "numeric",
  }).format(date)}`;
}

function getProjectUrl(project: GithubRepository): string {
  const homepage = project.homepage?.trim();
  if (!homepage) return project.html_url;

  try {
    const parsedHomepage = new URL(homepage);
    return parsedHomepage.protocol === "https:" || parsedHomepage.protocol === "http:"
      ? parsedHomepage.href
      : project.html_url;
  } catch {
    return project.html_url;
  }
}

function ProjectCard({ project, index }: { project: GithubRepository; index: number }) {
  const projectUrl = getProjectUrl(project);
  const hasLiveSite = projectUrl !== project.html_url;
  const topics = project.topics.slice(0, 3);

  return (
    <article
      className="project-card"
      style={{ animationDelay: `${Math.min(index, 8) * 65}ms` }}
    >
      <div className="project-card-top">
        <span className="project-index">{String(index + 1).padStart(2, "0")}</span>
        {project.stargazers_count > 0 && (
          <span className="stars" aria-label={`${project.stargazers_count} stars`}>
            <span aria-hidden="true">✳</span> {project.stargazers_count}
          </span>
        )}
      </div>
      <h3>
        <a className="project-title-link" href={projectUrl} target="_blank" rel="noreferrer">
          {project.name.replace(/[-_]+/g, " ")}
        </a>
      </h3>
      <p className="project-description">
        {project.description || "An open-source project built and maintained on GitHub."}
      </p>
      <div className="project-tags" aria-label="Project technologies">
        {project.language && <span className="language-tag">{project.language}</span>}
        {topics.map((topic) => (
          <span className="topic-tag" key={topic}>{topic}</span>
        ))}
      </div>
      <div className="project-card-bottom">
        <span className="updated-date">{formatUpdatedAt(project.updated_at)}</span>
        <div className="project-links">
          <a href={project.html_url} target="_blank" rel="noreferrer">
            <GithubIcon />
            <span>Code</span>
          </a>
          <a
            className="project-primary-link"
            href={projectUrl}
            target="_blank"
            rel="noreferrer"
          >
            <span>{hasLiveSite ? "View project" : "Repository"}</span>
            <ArrowIcon />
          </a>
        </div>
      </div>
    </article>
  );
}

function ProjectSkeleton() {
  return (
    <div className="project-grid" aria-label="Loading projects" aria-busy="true">
      {Array.from({ length: 6 }, (_, index) => (
        <div className="project-skeleton" key={index}>
          <span className="skeleton-line skeleton-short" />
          <span className="skeleton-line skeleton-title" />
          <span className="skeleton-line" />
          <span className="skeleton-line skeleton-medium" />
          <span className="skeleton-line skeleton-bottom" />
        </div>
      ))}
    </div>
  );
}

function App() {
  const [projects, setProjects] = useState<GithubRepository[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [activeLanguage, setActiveLanguage] = useState("All");
  const searchInput = useRef<HTMLInputElement>(null);

  async function loadProjects(signal?: AbortSignal) {
    setLoadState("loading");
    setError("");
    try {
      setProjects(await getGithubRepositories(signal));
      setLoadState("ready");
    } catch (loadError) {
      if (signal?.aborted) return;
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Projects could not be loaded. Please try again.",
      );
      setLoadState("error");
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    void loadProjects(controller.signal);
    return () => controller.abort();
  }, []);

  useEffect(() => {
    function focusSearch(event: KeyboardEvent) {
      if (
        event.key === "/" &&
        !(event.target instanceof HTMLInputElement) &&
        !(event.target instanceof HTMLTextAreaElement)
      ) {
        event.preventDefault();
        searchInput.current?.focus();
      }
    }
    document.addEventListener("keydown", focusSearch);
    return () => document.removeEventListener("keydown", focusSearch);
  }, []);

  const languages = useMemo(
    () => ["All", ...new Set(projects.flatMap((project) => project.language ? [project.language] : []))],
    [projects],
  );

  const filteredProjects = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return projects.filter((project) => {
      const matchesLanguage =
        activeLanguage === "All" || project.language === activeLanguage;
      const searchable = [
        project.name,
        project.description ?? "",
        project.language ?? "",
        ...project.topics,
      ].join(" ").toLowerCase();
      return matchesLanguage && (!normalizedQuery || searchable.includes(normalizedQuery));
    });
  }, [activeLanguage, projects, query]);

  return (
    <main className="site-shell">
      <header className="site-header">
        <a className="wordmark" href="#" aria-label="Charchit — home">
          <span className="wordmark-symbol">C</span>
          <span>charchit<span className="wordmark-dot">.</span></span>
        </a>
        <nav className="header-nav" aria-label="Main navigation">
          <a href="#projects">Projects</a>
          <a
            className="github-profile-link"
            href={`https://github.com/${githubUsername}`}
            target="_blank"
            rel="noreferrer"
          >
            <GithubIcon />
            <span>GitHub profile</span>
            <ArrowIcon />
          </a>
        </nav>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow"><span className="eyebrow-line" /> PORTFOLIO · OPEN SOURCE</p>
          <h1>
            Building things<br />
            <span>for the real world.</span>
          </h1>
          <p className="hero-description">
            A collection of projects, experiments, and ideas made tangible.
            Pick something that catches your eye and take a closer look.
          </p>
          <a className="hero-cta" href="#projects">
            Explore selected work <ArrowIcon />
          </a>
        </div>
        <div className="hero-aside" aria-label="GitHub profile">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="hero-monogram">C<span>.</span></div>
          <div className="aside-card">
            <span className="aside-card-icon"><SparkIcon /></span>
            <div>
              <strong>Made with curiosity</strong>
              <span>Ideas become software</span>
            </div>
            <span className="aside-live-dot" />
          </div>
          <span className="hero-aside-caption">A LITTLE BIT OF WHAT I DO</span>
        </div>
        <div className="hero-bottom">
          <span>SCROLL TO EXPLORE</span>
          <span className="scroll-line" />
          <span className="hero-bottom-note">Selected work from GitHub</span>
        </div>
      </section>

      <section className="projects-section" id="projects">
        <div className="section-topline">
          <div>
            <p className="eyebrow"><span className="eyebrow-line" /> THE WORK</p>
            <h2>Projects<span className="heading-period">.</span></h2>
          </div>
          <a
            className="all-repos-link"
            href={`https://github.com/${githubUsername}?tab=repositories`}
            target="_blank"
            rel="noreferrer"
          >
            Browse all on GitHub <ArrowIcon />
          </a>
        </div>

        <div className="project-toolbar">
          <div className="language-filters" aria-label="Filter projects by language">
            {languages.map((language) => (
              <button
                className={activeLanguage === language ? "filter-chip active" : "filter-chip"}
                key={language}
                onClick={() => setActiveLanguage(language)}
                type="button"
              >
                {language}
              </button>
            ))}
          </div>
          <label className="search-box">
            <svg viewBox="0 0 20 20" aria-hidden="true">
              <circle cx="8.8" cy="8.8" r="5.8" />
              <path d="m13.2 13.2 4 4" />
            </svg>
            <span className="sr-only">Search projects</span>
            <input
              ref={searchInput}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Find a project"
              type="search"
            />
            <kbd>/</kbd>
          </label>
        </div>

        {loadState === "loading" && <ProjectSkeleton />}

        {loadState === "error" && (
          <div className="state-panel" role="alert">
            <span className="state-icon">!</span>
            <h3>Couldn’t load the projects</h3>
            <p>{error}</p>
            <button className="retry-button" onClick={() => void loadProjects()} type="button">
              Try again <ArrowIcon />
            </button>
          </div>
        )}

        {loadState === "ready" && projects.length === 0 && (
          <div className="state-panel">
            <span className="state-icon"><GithubIcon /></span>
            <h3>No public projects to show yet</h3>
            <p>Public, non-forked repositories from this profile will appear here.</p>
            <a
              className="retry-button"
              href={`https://github.com/${githubUsername}`}
              target="_blank"
              rel="noreferrer"
            >
              Visit GitHub <ArrowIcon />
            </a>
          </div>
        )}

        {loadState === "ready" && projects.length > 0 && filteredProjects.length === 0 && (
          <div className="empty-filter-state">
            <p>No projects match “{query || activeLanguage}”.</p>
            <button
              onClick={() => {
                setQuery("");
                setActiveLanguage("All");
              }}
              type="button"
            >
              Clear filters
            </button>
          </div>
        )}

        {loadState === "ready" && filteredProjects.length > 0 && (
          <div className="project-grid">
            {filteredProjects.map((project, index) => (
              <ProjectCard index={index} key={project.id} project={project} />
            ))}
          </div>
        )}

        {loadState === "ready" && projects.length > 0 && (
          <p className="project-count">
            Showing <strong>{filteredProjects.length}</strong> of{" "}
            <strong>{projects.length}</strong> projects
          </p>
        )}
      </section>

      <footer className="site-footer">
        <a className="wordmark footer-wordmark" href="#" aria-label="Back to top">
          <span className="wordmark-symbol">C</span>
          <span>charchit<span className="wordmark-dot">.</span></span>
        </a>
        <span>Thoughtfully built, one commit at a time.</span>
        <a href={`https://github.com/${githubUsername}`} target="_blank" rel="noreferrer">
          <GithubIcon /> @{githubUsername}
        </a>
      </footer>
    </main>
  );
}

export default App;
