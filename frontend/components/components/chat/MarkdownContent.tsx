import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from "../../lib/utils";

interface MarkdownContentProps {
  content: string;
  className?: string;
}

const markdownComponents = {
  p: ({ children }: { children: React.ReactNode }) => (
    <p className="mb-2 last:mb-0">{children}</p>
  ),
  h1: ({ children }: { children: React.ReactNode }) => (
    <h1 className="text-lg font-bold mb-2">{children}</h1>
  ),
  h2: ({ children }: { children: React.ReactNode }) => (
    <h2 className="text-base font-bold mb-2">{children}</h2>
  ),
  h3: ({ children }: { children: React.ReactNode }) => (
    <h3 className="text-sm font-bold mb-2">{children}</h3>
  ),
  ul: ({ children }: { children: React.ReactNode }) => (
    <ul className="list-disc pl-4 mb-2">{children}</ul>
  ),
  ol: ({ children }: { children: React.ReactNode }) => (
    <ol className="list-decimal pl-4 mb-2">{children}</ol>
  ),
  li: ({ children }: { children: React.ReactNode }) => (
    <li className="mb-1">{children}</li>
  ),
  code: ({ children, className, ...props }: {
    children: React.ReactNode;
    className?: string;
  } & React.HTMLAttributes<HTMLElement>) => {
    const match = /language-(\w+)/.exec(className || '');
    const isInline = !match;

    if (isInline) {
      return (
        <code className="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono" {...props}>
          {children}
        </code>
      );
    }

    return (
      <code
        className={cn("block bg-gray-100 p-2 rounded text-xs font-mono overflow-x-auto", className)}
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: ({ children }: { children: React.ReactNode }) => (
    <pre className="mb-2">{children}</pre>
  ),
  blockquote: ({ children }: { children: React.ReactNode }) => (
    <blockquote className="border-l-4 border-gray-300 pl-4 italic mb-2">
      {children}
    </blockquote>
  ),
  a: ({ children, href, ...props }: {
    children: React.ReactNode;
    href?: string;
  } & React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a
      href={href}
      className="text-blue-600 hover:underline"
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    >
      {children}
    </a>
  ),
} as const;

export function MarkdownContent({ content, className }: MarkdownContentProps) {
  return (
    <div className={cn("text-sm markdown-body", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={markdownComponents}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
