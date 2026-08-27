"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/citizen", label: "Citizen" },
  { href: "/ops", label: "Planning desk" },
  { href: "/national", label: "National shelf" },
];

export function Nav() {
  const path = usePathname();
  return (
    <header className="topbar">
      <div className="brand">
        NirmanGrid<span>TRACK 1 · DPG</span>
      </div>
      <nav className="nav">
        {LINKS.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={path === l.href ? "active" : ""}
          >
            {l.label}
          </Link>
        ))}
      </nav>
      <div className="sample-pill">SAMPLE EVENTS ON MAP</div>
    </header>
  );
}
