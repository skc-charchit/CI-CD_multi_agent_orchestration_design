import type { ProjectSummary } from "./github-readme";

type ReadmeBlock = {
  heading: string;
  text: string;
};

const STOP_WORDS = new Set([
  "about", "and", "are", "can", "could", "does", "for", "from", "give",
  "have", "how", "into", "its", "know", "me", "more", "please", "project",
  "show", "tell", "that", "the", "this", "what", "with", "would", "you",
  "your",
]);

function cleanMarkdown(text: string): string {
  return text
    .replace(/<!--[\s\S]*?-->/g, " ")
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]+)\]\((?:[^()]|\([^()]*\))*\)/g, "$1")
    .replace(/<https?:\/\/[^>]+>/g, "")
    .replace(/<\/?[a-z][^>]*>/gi, " ")
    .replace(/[`*_~]/g, "")
    .replace(/^\s{0,3}(?:>\s?|[-*+]\s+|\d+[.)]\s+)/gm, "")
    .replace(/\s+/g, " ")
    .trim();
}

function extractReadmeBlocks(markdown: string): ReadmeBlock[] {
  const blocks: ReadmeBlock[] = [];
  let heading = "Overview";
  let paragraph: string[] = [];
  let code: string[] = [];
  let inCodeBlock = false;

  const addParagraph = () => {
    const text = cleanMarkdown(paragraph.join(" "));
    if (text.length >= 20) blocks.push({ heading, text });
    paragraph = [];
  };

  for (const line of markdown.split(/\r?\n/)) {
    if (/^\s*```/.test(line)) {
      addParagraph();
      if (inCodeBlock) {
        const text = code.join("\n").trim();
        if (text) blocks.push({ heading: `${heading} example`, text });
        code = [];
      }
      inCodeBlock = !inCodeBlock;
      continue;
    }
    if (inCodeBlock) {
      code.push(line);
      continue;
    }

    const headingMatch = line.match(/^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$/);
    if (headingMatch) {
      addParagraph();
      heading = cleanMarkdown(headingMatch[1]) || "README";
    } else if (!line.trim()) {
      addParagraph();
    } else if (!/^\s*\|?[\s:|-]+\|?\s*$/.test(line)) {
      paragraph.push(line.trim());
    }
  }

  addParagraph();
  if (inCodeBlock && code.length) {
    blocks.push({ heading: `${heading} example`, text: code.join("\n").trim() });
  }
  return blocks;
}

function tokenize(value: string): string[] {
  return value
    .toLowerCase()
    .match(/[a-z0-9+#.-]{2,}/g)
    ?.map((word) => word.replace(/[+#.-]+$/, ""))
    .filter((word) => word.length > 1 && !STOP_WORDS.has(word)) ?? [];
}

function getQuestionCategory(question: string): "overview" | "setup" | "details" {
  if (/\b(about|overview|purpose|problem|goal|what is|what does|summary)\b/i.test(question)) {
    return "overview";
  }
  if (/\b(run|install|setup|set up|start|usage|use it|execute|launch|deploy|requirements|prerequisites)\b/i.test(question)) {
    return "setup";
  }
  return "details";
}

function shorten(text: string, limit = 460): string {
  if (text.length <= limit) return text;
  const boundary = text.lastIndexOf(" ", limit);
  return `${text.slice(0, boundary > limit * 0.65 ? boundary : limit).trim()}…`;
}

export function answerProjectQuestion(
  repository: ProjectSummary,
  readme: string | null,
  question: string,
): string {
  const description = repository.description?.trim();
  const blocks = readme ? extractReadmeBlocks(readme) : [];
  const category = getQuestionCategory(question);

  if (!readme || blocks.length === 0) {
    if (description) {
      return `I couldn't find a README for this repository. GitHub describes it as: "${description}"${repository.language ? ` It is primarily written in ${repository.language}.` : ""}`;
    }
    return "I couldn't find a README or project description to answer from. You can open the repository directly for more information.";
  }

  const tokens = [...new Set(tokenize(question))];
  const ranked = blocks
    .map((block, index) => {
      const heading = block.heading.toLowerCase();
      const text = block.text.toLowerCase();
      const headingMatches = tokens.filter((token) => heading.includes(token)).length;
      const textMatches = tokens.filter((token) => text.includes(token)).length;
      let score = headingMatches * 4 + textMatches;

      if (
        category === "overview" &&
        /overview|about|introduction|description|features|what is/i.test(block.heading)
      ) score += 8;
      if (
        category === "setup" &&
        /install|setup|getting started|quick.?start|usage|run|deploy|prerequisite/i.test(block.heading)
      ) score += 10;
      if (category === "overview" && block.heading === "Overview") score += 5;
      if (category === "overview" && index === 0) score += 2;

      return { block, score, index };
    })
    .filter((entry) => entry.score > 0)
    .sort((left, right) => right.score - left.score || left.index - right.index)
    .slice(0, 3);

  const usefulSections = ranked.length > 0
    ? ranked
    : category === "overview"
      ? blocks.slice(0, 2).map((block, index) => ({ block, index, score: 0 }))
      : [];

  if (usefulSections.length === 0) {
    return "I couldn't find that detail in this repository's README. Try asking about the project overview, features, setup, or tools it uses.";
  }

  const intro = category === "overview" && description
    ? `GitHub describes this project as: "${description}"\n\n`
    : "";
  const excerpts = usefulSections
    .map(({ block }) => `${block.heading}: ${shorten(block.text)}`)
    .join("\n\n");

  return `${intro}From the project README:\n\n${excerpts}`;
}
