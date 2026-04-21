"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Nav() {
  const pathname = usePathname();

  const linkClass = (href: string) =>
    `px-4 py-2 rounded text-sm font-medium transition-colors ${
      pathname === href
        ? "bg-blue-600 text-white"
        : "text-gray-600 hover:bg-gray-100"
    }`;

  return (
    <nav className="border-b bg-white px-6 py-3 flex gap-2">
      <Link href="/" className={linkClass("/")}>
        Upload
      </Link>
      <Link href="/logs" className={linkClass("/logs")}>
        Activity Logs
      </Link>
    </nav>
  );
}
