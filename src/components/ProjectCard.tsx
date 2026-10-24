import { ArrowUpRight, GitBranch, LockKeyhole } from "lucide-react";
import { External, IconBox } from "./Shared";
import type { ProjectDestination } from "../data/navigation";
export function ProjectCard({ item }: { item: ProjectDestination }) {
  return (
    <article className="project-card" aria-label={`${item.title} workspace`}>
      <External href={item.href} className="project-entry">
        <div className="card-top">
          <IconBox icon={item.icon} tone={item.tone} />
          <span className="project-kind">{item.workspaceKind}</span>
        </div>
        <h3>{item.title}</h3>
        <p>{item.description}</p>
        <span className="project-access">
          <LockKeyhole size={12} aria-hidden="true" />
          Open in Notion
          <ArrowUpRight size={14} aria-hidden="true" />
        </span>
      </External>
      <div className="project-tools">
        <p className="tool-section-label">Software &amp; tools</p>
        {item.tools.length ? (
          <ul className="tool-list">
            {item.tools.map((tool) => {
              const content = (
                <>
                  <span className="tool-title">{tool.title}</span>{" "}
                  <span className="tool-kind">{tool.kind}</span>{" "}
                  <span className="tool-tracking">
                    <GitBranch size={12} aria-hidden="true" /> Git-tracked
                  </span>{" "}
                  <span className="tool-action">
                    {tool.href ? "Open workspace" : "Access through project"}
                    <ArrowUpRight size={13} aria-hidden="true" />
                  </span>
                </>
              );
              return (
                <li key={tool.title}>
                  {tool.href ? (
                    <a href={tool.href} className="tool-link">
                      {content}
                    </a>
                  ) : (
                    <External href={item.href} className="tool-link">
                      {content}
                    </External>
                  )}
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="no-tools">No software linked yet.</p>
        )}
      </div>
    </article>
  );
}

