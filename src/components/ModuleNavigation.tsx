import { useEffect, useRef, useState } from "react";
import { homeSections } from "../data/modules";
export function MobileSectionNavigation({ active, onNavigate }: {
  active: string; onNavigate: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLElement>(null);
  useEffect(() => { if (open) panel.current?.querySelector<HTMLAnchorElement>("a")?.focus(); }, [open]);
  return <div className="mobile-section-nav" onKeyDown={event => {
    if (event.key === "Escape" && open) { setOpen(false); toggle.current?.focus(); }
  }}>
    <div className="mobile-nav-shortcuts">
      {homeSections.filter(item => item.id === "apps" || item.id === "workstreams").map(item => (
        <a key={item.id} href={`#${item.id}`} aria-current={active === item.id ? "location" : undefined}
          onClick={() => { onNavigate(item.id); setOpen(false); }}>{item.label}</a>
      ))}
    </div>
    <button ref={toggle} type="button" aria-expanded={open} aria-controls="mobile-sections"
      onClick={() => setOpen(value => !value)}>Quick navigation</button>
    <nav ref={panel} id="mobile-sections" aria-label="Page sections" hidden={!open}>
      {homeSections.map(item => <a key={item.id} href={`#${item.id}`}
        aria-current={active === item.id ? "location" : undefined} onClick={() => {
          onNavigate(item.id); setOpen(false); toggle.current?.focus();
        }}>{item.label}</a>)}
    </nav>
  </div>;
}
