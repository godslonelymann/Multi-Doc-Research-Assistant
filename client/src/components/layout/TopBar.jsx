import { NavLink } from "react-router-dom";

function TopBar() {
  return (
    <header className="sticky top-0 z-10 border-b border-[#d2d2d7]/80 bg-white/80 backdrop-blur-xl">
      <div className="mx-auto flex h-12 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <NavLink to="/workspaces" className="min-w-0">
          <h1 className="truncate text-sm font-semibold text-[#1d1d1f]">Multi-Document Assistant</h1>
        </NavLink>
        <nav>
          <NavLink
            to="/workspaces"
            className={({ isActive }) =>
              [
                "rounded-lg px-3 py-1.5 text-sm font-medium transition",
                isActive ? "bg-[#f5f5f7] text-[#1d1d1f]" : "text-[#6e6e73] hover:text-[#1d1d1f]",
              ].join(" ")
            }
          >
            Workspaces
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

export default TopBar;
