import { FormEvent, useEffect, useRef, useState } from "react";
import {
  getRepositoryReadme,
  type ProjectSummary,
} from "./github-readme";
import { answerProjectQuestion } from "./project-guide";
import "./styles.css";

type ChatMessage = {
  id: number;
  role: "assistant" | "user";
  text: string;
  sourceUrl?: string;
  sourceLabel?: string;
};

type ProjectChatProps = {
  repositories: ProjectSummary[];
};

function ChatIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H6l-3 2v-5.2A7.5 7.5 0 1 1 20 11.5Z" />
      <path d="M8 11h.01M12 11h.01M16 11h.01" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <path d="m5 5 10 10M15 5 5 15" />
    </svg>
  );
}

const SUGGESTIONS = [
  "What does this project do?",
  "How do I run it?",
  "What tools does it use?",
];

function readmeUrl(repository: ProjectSummary): string {
  const branch = encodeURIComponent(repository.default_branch);
  return `https://github.com/${repository.full_name}/blob/${branch}/README.md`;
}

export function ProjectChat({ repositories }: ProjectChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState("");
  const [question, setQuestion] = useState("");
  const [isAnswering, setIsAnswering] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState("");
  const conversationEnd = useRef<HTMLDivElement>(null);
  const questionInput = useRef<HTMLInputElement>(null);
  const launcherButton = useRef<HTMLButtonElement>(null);
  const nextMessageId = useRef(1);

  useEffect(() => {
    if (!selectedProject && repositories.length > 0) {
      setSelectedProject(repositories[0].full_name);
    }
  }, [repositories, selectedProject]);

  useEffect(() => {
    conversationEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isAnswering]);

  useEffect(() => {
    if (!isOpen) return;

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
        launcherButton.current?.focus();
      }
    }

    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [isOpen]);

  async function askProjectQuestion(value: string) {
    const cleanQuestion = value.trim();
    const repository = repositories.find(
      (item) => item.full_name === selectedProject,
    );
    if (!cleanQuestion || !repository || isAnswering) return;

    const userMessage: ChatMessage = {
      id: nextMessageId.current++,
      role: "user",
      text: cleanQuestion,
    };
    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setError("");
    setIsAnswering(true);

    try {
      const readme = await getRepositoryReadme(repository);
      const answer = answerProjectQuestion(repository, readme, cleanQuestion);
      setMessages((current) => [
        ...current,
        {
          id: nextMessageId.current++,
          role: "assistant",
          text: answer,
          sourceUrl: readme ? readmeUrl(repository) : repository.html_url,
          sourceLabel: readme ? "Source: project README" : "Open repository",
        },
      ]);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "The project README could not be loaded.",
      );
    } finally {
      setIsAnswering(false);
      questionInput.current?.focus();
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void askProjectQuestion(question);
  }

  const hasProjects = repositories.length > 0;

  return (
    <>
      {isOpen && (
        <section
          className="project-chat"
          aria-label="Project README guide"
          aria-modal="false"
          role="dialog"
        >
          <header className="chat-header">
            <span className="chat-avatar"><ChatIcon /></span>
            <div className="chat-header-copy">
              <strong>Project guide</strong>
              <span><i /> Answers from public project READMEs</span>
            </div>
            <button
              className="chat-close"
              type="button"
              aria-label="Close project guide"
              onClick={() => setIsOpen(false)}
            >
              <CloseIcon />
            </button>
          </header>

          <div className="chat-project-select">
            <label htmlFor="chat-project">ASK ABOUT</label>
            <select
              id="chat-project"
              value={selectedProject}
              disabled={!hasProjects || isAnswering}
              onChange={(event) => {
                setSelectedProject(event.target.value);
                setMessages([]);
                setError("");
              }}
            >
              {!hasProjects && <option value="">Projects are loading…</option>}
              {repositories.map((repository) => (
                <option key={repository.id} value={repository.full_name}>
                  {repository.name}
                </option>
              ))}
            </select>
          </div>

          <div className="chat-messages" aria-live="polite" aria-relevant="additions">
            {messages.length === 0 && (
              <div className="chat-welcome">
                <span className="chat-welcome-spark">✳</span>
                <h3>Curious about a project?</h3>
                <p>
                  Ask me about its purpose, features, or how to get it running.
                  I’ll look in the project README.
                </p>
                <span className="chat-source-note">README ONLY · NO AI API YET</span>
                <div className="chat-suggestions">
                  {SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      disabled={!hasProjects || isAnswering}
                      onClick={() => void askProjectQuestion(suggestion)}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message) => (
              <article
                className={`chat-message ${message.role}`}
                key={message.id}
              >
                <p>{message.text}</p>
                {message.sourceUrl && (
                  <a href={message.sourceUrl} target="_blank" rel="noreferrer">
                    {message.sourceLabel} <span aria-hidden="true">↗</span>
                  </a>
                )}
              </article>
            ))}

            {isAnswering && (
              <div className="chat-typing" role="status">
                <span /><span /><span />
                <span className="sr-only">Reading the project README</span>
              </div>
            )}
            {error && <p className="chat-error" role="alert">{error}</p>}
            <div ref={conversationEnd} />
          </div>

          <form className="chat-form" onSubmit={handleSubmit}>
            <input
              ref={questionInput}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              disabled={!hasProjects || isAnswering}
              maxLength={500}
              placeholder={hasProjects ? "Ask about this project…" : "Loading projects…"}
              aria-label="Ask a question about the selected project"
              required
            />
            <button
              type="submit"
              disabled={!hasProjects || isAnswering || !question.trim()}
              aria-label="Send question"
            >
              <svg viewBox="0 0 20 20" aria-hidden="true">
                <path d="M3 10h13m-5-5 5 5-5 5" />
              </svg>
            </button>
          </form>
          <p className="chat-disclaimer">Replies are excerpts from the selected repository’s README.</p>
        </section>
      )}

      <button
        ref={launcherButton}
        className={isOpen ? "chat-launcher is-open" : "chat-launcher"}
        type="button"
        aria-label={isOpen ? "Close project guide" : "Ask about a project"}
        aria-expanded={isOpen}
        onClick={() => {
          if (isOpen) {
            setIsOpen(false);
          } else {
            setIsOpen(true);
            window.setTimeout(() => questionInput.current?.focus(), 0);
          }
        }}
      >
        {isOpen ? <CloseIcon /> : <ChatIcon />}
        {!isOpen && <span>Ask about a project</span>}
      </button>
    </>
  );
}
