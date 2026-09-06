import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Activity, Boxes, GitCompare, LayoutDashboard, Settings2, UploadCloud } from "lucide-react";
import { LogoLockup, LogoMark } from "@/components/brand/Logo";
import { useAnalysisStore } from "@/store/analysisStore";
import { formatDate } from "@/utils/formatters";

const NAV = [
  { to: "/overview", label: "Overview", icon: LayoutDashboard },
  { to: "/analysis", label: "Analysis", icon: UploadCloud },
  { to: "/components", label: "Components", icon: Boxes },
  { to: "/lots", label: "Lot Comparison", icon: GitCompare },
  { to: "/settings", label: "Settings", icon: Settings2 },
] as const;

export function AppShell() {
  const { datasetName, loaded, loadSample, summary } = useAnalysisStore();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    if (!loaded) loadSample();
  }, [loaded, loadSample]);

  useEffect(() => {
    setNow(new Date());
  }, []);

  return (
    <div className="flex min-h-screen w-full bg-background">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
        <div className="border-b border-sidebar-border px-4 py-4">
          <Link to="/" aria-label="BurnIn-AI home">
            <LogoLockup />
          </Link>
        </div>

        <nav className="flex-1 space-y-1 p-3" aria-label="Main">
          {NAV.map(({ to, label, icon: Icon }) => {
            const active = pathname === to || pathname.startsWith(`${to}/`);
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                  active
                    ? "bg-sidebar-accent text-foreground shadow-[inset_2px_0_0_0_var(--primary)]"
                    : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" aria-hidden />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-sidebar-border px-4 py-4 font-mono text-[10px] leading-relaxed tracking-[0.16em] text-muted-foreground">
          <div>ANALYSIS ENGINE</div>
          <div>v1.0</div>
          <div className="mt-1 flex items-center gap-1.5 text-safe">
            <span className="h-1.5 w-1.5 rounded-full bg-safe" aria-hidden />
            SYSTEM OPERATIONAL
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex flex-wrap items-center gap-x-8 gap-y-2 border-b border-border bg-background/85 px-5 py-3 backdrop-blur">
          <Link to="/" className="flex items-center gap-2 lg:hidden">
            <LogoMark className="h-7 w-7" />
            <span className="text-sm font-semibold">BurnIn-AI</span>
          </Link>
          <Meta label="DATASET" value={datasetName} mono />
          <Meta label="COMPONENTS" value={String(summary.total)} mono />
          <div className="hidden sm:block">
            <div className="label-xs">SYSTEM</div>
            <div className="flex items-center gap-1.5 font-mono text-xs text-safe">
              <span className="h-1.5 w-1.5 rounded-full bg-safe" aria-hidden />
              OPERATIONAL
            </div>
          </div>
          <div className="ml-auto font-mono text-xs text-muted-foreground">
            {now ? formatDate(now) : ""}
          </div>
        </header>

        <main className="min-w-0 flex-1 p-5 lg:p-7">
          <div className="mx-auto max-w-[1600px]">
            <Outlet />
          </div>
        </main>

        <nav
          className="flex overflow-x-auto border-t border-border bg-sidebar lg:hidden"
          aria-label="Main mobile"
        >
          {NAV.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className="flex flex-1 flex-col items-center gap-1 px-3 py-2 text-[10px] text-muted-foreground"
              activeProps={{ className: "text-foreground" }}
            >
              <Icon className="h-4 w-4" aria-hidden />
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );
}

function Meta({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="label-xs">{label}</div>
      <div className={`text-xs text-foreground ${mono ? "font-mono" : ""}`}>{value}</div>
    </div>
  );
}
