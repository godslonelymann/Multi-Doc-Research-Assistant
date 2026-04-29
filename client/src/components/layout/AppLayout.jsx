import { Outlet } from "react-router-dom";

import TopBar from "./TopBar.jsx";

function AppLayout() {
  return (
    <div className="min-h-screen bg-[#f5f5f7] text-[#1d1d1f]">
      <TopBar />
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <main className="min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppLayout;
