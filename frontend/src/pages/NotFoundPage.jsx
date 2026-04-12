import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-[#1a1a2e]">404</h1>
        <p className="text-gray-500 mt-3 text-lg">Page not found</p>
        <Link
          to="/dashboard"
          className="inline-block mt-6 bg-[#1a1a2e] text-white rounded-lg px-6 py-2.5 text-sm font-medium hover:bg-[#2d2d4e] transition-colors"
        >
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
