import { Link } from "react-router-dom";

function NotFoundPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="text-center">
        <h1 className="text-3xl font-semibold text-slate-950">Page not found</h1>
        <p className="mt-2 text-sm text-slate-600">The requested route does not exist.</p>
        <Link className="mt-5 inline-flex rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white" to="/">
          Back to dashboard
        </Link>
      </div>
    </main>
  );
}

export default NotFoundPage;
