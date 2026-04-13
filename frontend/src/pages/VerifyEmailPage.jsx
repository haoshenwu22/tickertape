import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { verifyEmail } from "../services/api";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState("ready"); // ready | loading | success | error
  const [errorMsg, setErrorMsg] = useState("");

  const handleVerify = async () => {
    if (!token) {
      setErrorMsg("No verification token found in the URL.");
      setStatus("error");
      return;
    }

    setStatus("loading");
    try {
      await verifyEmail(token);
      setStatus("success");
    } catch (err) {
      const msg = err.response?.data?.error || "";
      if (msg.includes("already been used")) {
        // Token was already used — verification succeeded previously
        setStatus("success");
      } else {
        setErrorMsg(
          msg ||
            err.response?.data?.detail ||
            "Verification failed. The link may be expired or already used."
        );
        setStatus("error");
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-[#1a1a2e]">TickerTape</h1>
          <p className="text-gray-500 mt-1">Email Verification</p>
        </div>

        <div className="bg-white rounded-xl shadow-md p-8 text-center space-y-4">
          {status === "ready" && (
            <>
              <div className="flex justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-16 w-16 text-indigo-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
                  />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-gray-800">
                Verify your email address
              </h2>
              <p className="text-sm text-gray-500">
                Click the button below to confirm your email and activate your
                account.
              </p>
              <button
                onClick={handleVerify}
                className="inline-block bg-[#1a1a2e] text-white rounded-lg px-6 py-2.5 text-sm font-medium hover:bg-[#2d2d4e] transition-colors"
              >
                Verify Email
              </button>
            </>
          )}

          {status === "loading" && (
            <>
              <div className="flex justify-center">
                <div className="h-10 w-10 border-4 border-gray-200 border-t-[#1a1a2e] rounded-full animate-spin" />
              </div>
              <p className="text-sm text-gray-500">Verifying your email...</p>
            </>
          )}

          {status === "success" && (
            <>
              <div className="flex justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-16 w-16 text-emerald-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-gray-800">
                Email verified!
              </h2>
              <p className="text-sm text-gray-500">
                You can now log in to your account.
              </p>
              <Link
                to="/login"
                className="inline-block bg-[#1a1a2e] text-white rounded-lg px-6 py-2.5 text-sm font-medium hover:bg-[#2d2d4e] transition-colors"
              >
                Go to login
              </Link>
            </>
          )}

          {status === "error" && (
            <>
              <div className="flex justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-16 w-16 text-red-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                  />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-gray-800">
                Verification failed
              </h2>
              <p className="text-sm text-gray-500">
                {errorMsg || "The link may be expired or already used."}
              </p>
              <Link
                to="/login"
                className="text-sm text-[#1a1a2e] font-medium hover:underline"
              >
                Back to login
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
