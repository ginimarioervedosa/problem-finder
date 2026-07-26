import { createRootRoute, Link, Outlet } from "@tanstack/react-router";

export const Route = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <header className="border-b border-neutral-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-baseline gap-6 px-6 py-4">
          <span className="text-lg font-semibold tracking-tight">problem-finder</span>
          <nav className="flex gap-4 text-sm text-neutral-600">
            <Link to="/signals" className="hover:text-neutral-900 [&.active]:font-medium [&.active]:text-neutral-900">
              Signals
            </Link>
            <Link to="/themes" className="hover:text-neutral-900 [&.active]:font-medium [&.active]:text-neutral-900">
              Themes
            </Link>
            <Link to="/suggestions" className="hover:text-neutral-900 [&.active]:font-medium [&.active]:text-neutral-900">
              Suggestions
            </Link>
            <Link to="/trends" className="hover:text-neutral-900 [&.active]:font-medium [&.active]:text-neutral-900">
              Trends
            </Link>
            <Link to="/runs" className="hover:text-neutral-900 [&.active]:font-medium [&.active]:text-neutral-900">
              Runs
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-6">
        <Outlet />
      </main>
    </div>
  );
}
