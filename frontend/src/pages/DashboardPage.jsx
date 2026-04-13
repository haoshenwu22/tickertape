import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import {
  getSubscriptions,
  createSubscription,
  deleteSubscription,
  sendNow,
  getStockPrices,
  getStockHistory,
  getAlerts,
  createAlert,
  deleteAlert,
  getRecommendation,
} from "../services/api";
import toast from "react-hot-toast";
import SparklineChart from "../components/SparklineChart";
import StockChart from "../components/StockChart";

// --------------- helpers ---------------

function recLabel(rec) {
  if (!rec) return null;
  const lower = rec.toLowerCase();
  if (lower.includes("buy") || lower.includes("strong_buy"))
    return { text: rec.replace(/_/g, " "), cls: "bg-emerald-100 text-emerald-700" };
  if (lower.includes("sell"))
    return { text: rec.replace(/_/g, " "), cls: "bg-red-100 text-red-700" };
  return { text: rec.replace(/_/g, " "), cls: "bg-amber-100 text-amber-700" };
}

function SkeletonRow({ cols }) {
  return (
    <tr>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
        </td>
      ))}
    </tr>
  );
}

// --------------- main component ---------------

export default function DashboardPage() {
  const { user, logout } = useAuth();

  // tab state
  const [tab, setTab] = useState("subscriptions");

  // subscription state
  const [subs, setSubs] = useState([]);
  const [prices, setPrices] = useState({});
  const [sparklines, setSparklines] = useState({});
  const [subsLoading, setSubsLoading] = useState(true);
  const [newTicker, setNewTicker] = useState("");
  const [newEmail, setNewEmail] = useState(user?.email || "");
  const [addingSub, setAddingSub] = useState(false);
  const [recommendations, setRecommendations] = useState({});
  const [recLoading, setRecLoading] = useState(new Set());

  // alert state
  const [alerts, setAlerts] = useState([]);
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [alertTicker, setAlertTicker] = useState("");
  const [alertPrice, setAlertPrice] = useState("");
  const [alertCondition, setAlertCondition] = useState("above");
  const [addingAlert, setAddingAlert] = useState(false);

  // chart modal
  const [chartTicker, setChartTicker] = useState(null);

  // sending state tracker
  const [sendingIds, setSendingIds] = useState(new Set());

  // --------------- data fetching ---------------

  const fetchSubscriptions = useCallback(async () => {
    setSubsLoading(true);
    try {
      const data = await getSubscriptions();
      const list = Array.isArray(data) ? data : data.results || [];
      setSubs(list);

      // fetch prices for all unique tickers
      const tickers = [...new Set(list.map((s) => s.ticker))];
      if (tickers.length > 0) {
        try {
          const priceData = await getStockPrices(tickers);
          setPrices(priceData);
        } catch {
          // prices are optional
        }

        // fetch sparkline data for each ticker
        const sparkObj = {};
        await Promise.allSettled(
          tickers.map(async (t) => {
            try {
              const res = await getStockHistory(t, "1w");
              sparkObj[t] = res.history || res;
            } catch {
              sparkObj[t] = [];
            }
          })
        );
        setSparklines(sparkObj);
      }
    } catch (err) {
      toast.error("Failed to load subscriptions");
    } finally {
      setSubsLoading(false);
    }
  }, []);

  const fetchAlerts = useCallback(async () => {
    setAlertsLoading(true);
    try {
      const data = await getAlerts();
      setAlerts(Array.isArray(data) ? data : data.results || []);
    } catch {
      toast.error("Failed to load alerts");
    } finally {
      setAlertsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSubscriptions();
    fetchAlerts();

    // Auto-refresh alerts every 30 seconds to pick up triggered status
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, [fetchSubscriptions, fetchAlerts]);

  // pre-fill email when user loads
  useEffect(() => {
    if (user?.email && !newEmail) {
      setNewEmail(user.email);
    }
  }, [user]);

  // --------------- handlers ---------------

  const handleGetRec = async (ticker) => {
    setRecLoading((prev) => new Set(prev).add(ticker));
    try {
      const rec = await getRecommendation(ticker);
      setRecommendations((prev) => ({ ...prev, [ticker]: rec }));
    } catch {
      toast.error("Failed to get recommendation");
    } finally {
      setRecLoading((prev) => {
        const next = new Set(prev);
        next.delete(ticker);
        return next;
      });
    }
  };

  const handleAddSub = async (e) => {
    e.preventDefault();
    if (!newTicker.trim()) return;
    setAddingSub(true);
    try {
      const result = await createSubscription(newTicker.toUpperCase().trim(), newEmail.trim());
      if (result.verification_required) {
        toast.success(`Verification email sent to ${newEmail.trim()}. Check your inbox.`);
      } else {
        toast.success("Subscription added");
      }
      setNewTicker("");
      fetchSubscriptions();
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        (typeof err.response?.data === "object"
          ? Object.values(err.response.data).flat().join(" ")
          : "Failed to add subscription");
      toast.error(msg);
    } finally {
      setAddingSub(false);
    }
  };

  const handleDeleteSub = async (id) => {
    try {
      await deleteSubscription(id);
      toast.success("Subscription removed");
      setSubs((prev) => prev.filter((s) => s.id !== id));
    } catch {
      toast.error("Failed to delete subscription");
    }
  };

  const handleSendNow = async (id) => {
    setSendingIds((prev) => new Set(prev).add(id));
    try {
      await sendNow(id);
      toast.success("Report sent!");
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to send report");
    } finally {
      setSendingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleAddAlert = async (e) => {
    e.preventDefault();
    if (!alertTicker.trim() || !alertPrice) return;
    setAddingAlert(true);
    try {
      await createAlert(
        alertTicker.toUpperCase().trim(),
        parseFloat(alertPrice),
        alertCondition
      );
      toast.success("Alert created");
      setAlertTicker("");
      setAlertPrice("");
      setAlertCondition("above");
      fetchAlerts();
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        (typeof err.response?.data === "object"
          ? Object.values(err.response.data).flat().join(" ")
          : "Failed to create alert");
      toast.error(msg);
    } finally {
      setAddingAlert(false);
    }
  };

  const handleDeleteAlert = async (id) => {
    try {
      await deleteAlert(id);
      toast.success("Alert deleted");
      setAlerts((prev) => prev.filter((a) => a.id !== id));
    } catch {
      toast.error("Failed to delete alert");
    }
  };

  // --------------- merged row data ---------------

  const rows = subs.map((sub) => {
    const p = prices[sub.ticker] || {};
    return {
      ...sub,
      company: p.name || sub.ticker,
      price: p.price ?? null,
      change: p.change_pct ?? null,
      recommendation: recommendations[sub.ticker]?.action || null,
      recReason: recommendations[sub.ticker]?.reason || null,
      spark: sparklines[sub.ticker] || [],
    };
  });

  // --------------- render ---------------

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-[#1a1a2e] text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">TickerTape</h1>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-300">{user?.username}</span>
            {user?.is_admin && (
              <span className="text-[10px] font-semibold uppercase tracking-wider bg-amber-500 text-white px-2 py-0.5 rounded">
                Admin
              </span>
            )}
            <button
              onClick={logout}
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-gray-200">
          <button
            onClick={() => setTab("subscriptions")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
              tab === "subscriptions"
                ? "border-[#1a1a2e] text-[#1a1a2e]"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Subscriptions
          </button>
          <button
            onClick={() => setTab("alerts")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
              tab === "alerts"
                ? "border-[#1a1a2e] text-[#1a1a2e]"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Price Alerts
          </button>
        </div>

        {/* ============= Subscriptions Tab ============= */}
        {tab === "subscriptions" && (
          <>
            {/* Add form */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 mb-6">
              <h2 className="text-sm font-semibold text-gray-700 mb-3">
                Add Subscription
              </h2>
              <form
                onSubmit={handleAddSub}
                className="flex flex-col sm:flex-row gap-3"
              >
                <input
                  type="text"
                  placeholder="Ticker (e.g. AAPL)"
                  value={newTicker}
                  onChange={(e) => setNewTicker(e.target.value)}
                  required
                  className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a1a2e] focus:border-transparent"
                />
                <input
                  type="email"
                  placeholder="Email address"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  required
                  className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a1a2e] focus:border-transparent"
                />
                <button
                  type="submit"
                  disabled={addingSub}
                  className="bg-[#1a1a2e] text-white rounded-lg px-5 py-2 text-sm font-medium hover:bg-[#2d2d4e] transition-colors disabled:opacity-50"
                >
                  {addingSub ? "Adding..." : "Add"}
                </button>
              </form>
            </div>

            {/* Admin badge */}
            {user?.is_admin && (
              <div className="mb-4 flex items-center gap-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 w-fit">
                <span className="inline-block w-2 h-2 bg-amber-500 rounded-full" />
                Viewing all subscriptions
              </div>
            )}

            {/* Table */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-gray-100 text-gray-500 text-xs uppercase tracking-wider">
                    <th className="px-4 py-3 font-medium">Ticker</th>
                    <th className="px-4 py-3 font-medium">Company</th>
                    <th className="px-4 py-3 font-medium text-right">Price</th>
                    <th className="px-4 py-3 font-medium text-right">Change%</th>
                    <th className="px-4 py-3 font-medium">Chart</th>
                    <th className="px-4 py-3 font-medium">Rec.</th>
                    <th className="px-4 py-3 font-medium">Email</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {subsLoading ? (
                    <>
                      <SkeletonRow cols={9} />
                      <SkeletonRow cols={9} />
                      <SkeletonRow cols={9} />
                    </>
                  ) : rows.length === 0 ? (
                    <tr>
                      <td
                        colSpan={9}
                        className="px-4 py-10 text-center text-gray-400"
                      >
                        No subscriptions yet. Add one above.
                      </td>
                    </tr>
                  ) : (
                    rows.map((row) => {
                      const rec = recLabel(row.recommendation);
                      const changePositive =
                        row.change !== null && row.change >= 0;

                      return (
                        <tr
                          key={row.id}
                          className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors"
                        >
                          <td className="px-4 py-3 font-semibold text-[#1a1a2e]">
                            {row.ticker}
                          </td>
                          <td className="px-4 py-3 text-gray-600">
                            {row.company}
                          </td>
                          <td className="px-4 py-3 text-right font-medium">
                            {row.price !== null
                              ? `$${Number(row.price).toFixed(2)}`
                              : "--"}
                          </td>
                          <td
                            className={`px-4 py-3 text-right font-medium ${
                              row.change === null
                                ? "text-gray-400"
                                : changePositive
                                ? "text-emerald-600"
                                : "text-red-600"
                            }`}
                          >
                            {row.change !== null
                              ? `${changePositive ? "+" : ""}${Number(
                                  row.change
                                ).toFixed(2)}%`
                              : "--"}
                          </td>
                          <td className="px-4 py-3">
                            <SparklineChart
                              data={row.spark}
                              onClick={() => setChartTicker(row.ticker)}
                            />
                          </td>
                          <td className="px-4 py-3">
                            {rec ? (
                              <div>
                                <span
                                  className={`text-[11px] font-semibold uppercase px-2 py-0.5 rounded ${rec.cls}`}
                                >
                                  {rec.text}
                                </span>
                                {row.recReason && (
                                  <div className="text-[10px] text-gray-400 mt-1 max-w-[200px] leading-tight">
                                    {row.recReason}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <button
                                onClick={() => handleGetRec(row.ticker)}
                                disabled={recLoading.has(row.ticker)}
                                className="text-xs text-indigo-600 border border-indigo-300 rounded px-2 py-0.5 hover:bg-indigo-600 hover:text-white transition-colors disabled:opacity-50"
                              >
                                {recLoading.has(row.ticker) ? "..." : "Get Rec."}
                              </button>
                            )}
                          </td>
                          <td className="px-4 py-3 text-gray-500 text-xs">
                            {row.email || user?.email || "--"}
                          </td>
                          <td className="px-4 py-3">
                            {row.is_active ? (
                              <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded bg-emerald-100 text-emerald-700">
                                Active
                              </span>
                            ) : (
                              <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded bg-amber-100 text-amber-700">
                                Pending verification
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => handleSendNow(row.id)}
                                disabled={sendingIds.has(row.id) || !row.is_active}
                                title={!row.is_active ? "Verify email first" : ""}
                                className="text-xs text-[#1a1a2e] border border-[#1a1a2e] rounded px-2.5 py-1 hover:bg-[#1a1a2e] hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                {sendingIds.has(row.id) ? "Sending..." : "Send Now"}
                              </button>
                              <button
                                onClick={() => handleDeleteSub(row.id)}
                                className="text-xs text-red-600 border border-red-300 rounded px-2.5 py-1 hover:bg-red-600 hover:text-white transition-colors"
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}

        {/* ============= Price Alerts Tab ============= */}
        {tab === "alerts" && (
          <>
            {/* Add alert form */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 mb-6">
              <h2 className="text-sm font-semibold text-gray-700 mb-3">
                Add Price Alert
              </h2>
              <form
                onSubmit={handleAddAlert}
                className="flex flex-col sm:flex-row gap-3"
              >
                <input
                  type="text"
                  placeholder="Ticker (e.g. TSLA)"
                  value={alertTicker}
                  onChange={(e) => setAlertTicker(e.target.value)}
                  required
                  className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a1a2e] focus:border-transparent"
                />
                <input
                  type="number"
                  step="0.01"
                  placeholder="Target price"
                  value={alertPrice}
                  onChange={(e) => setAlertPrice(e.target.value)}
                  required
                  className="w-full sm:w-36 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a1a2e] focus:border-transparent"
                />
                <select
                  value={alertCondition}
                  onChange={(e) => setAlertCondition(e.target.value)}
                  className="w-full sm:w-32 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#1a1a2e] focus:border-transparent bg-white"
                >
                  <option value="above">Above</option>
                  <option value="below">Below</option>
                </select>
                <button
                  type="submit"
                  disabled={addingAlert}
                  className="bg-[#1a1a2e] text-white rounded-lg px-5 py-2 text-sm font-medium hover:bg-[#2d2d4e] transition-colors disabled:opacity-50"
                >
                  {addingAlert ? "Creating..." : "Add Alert"}
                </button>
              </form>
            </div>

            {/* Alert table */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-gray-100 text-gray-500 text-xs uppercase tracking-wider">
                    <th className="px-4 py-3 font-medium">Ticker</th>
                    <th className="px-4 py-3 font-medium text-right">
                      Target Price
                    </th>
                    <th className="px-4 py-3 font-medium">Condition</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Created</th>
                    <th className="px-4 py-3 font-medium text-right">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {alertsLoading ? (
                    <>
                      <SkeletonRow cols={6} />
                      <SkeletonRow cols={6} />
                    </>
                  ) : alerts.length === 0 ? (
                    <tr>
                      <td
                        colSpan={6}
                        className="px-4 py-10 text-center text-gray-400"
                      >
                        No price alerts yet. Add one above.
                      </td>
                    </tr>
                  ) : (
                    alerts.map((a) => (
                      <tr
                        key={a.id}
                        className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors"
                      >
                        <td className="px-4 py-3 font-semibold text-[#1a1a2e]">
                          {a.ticker}
                        </td>
                        <td className="px-4 py-3 text-right font-medium">
                          ${Number(a.target_price).toFixed(2)}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`text-[11px] font-semibold uppercase px-2 py-0.5 rounded ${
                              a.condition === "above"
                                ? "bg-emerald-100 text-emerald-700"
                                : "bg-red-100 text-red-700"
                            }`}
                          >
                            {a.condition}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`text-[11px] font-semibold uppercase px-2 py-0.5 rounded ${
                              a.is_triggered
                                ? "bg-amber-100 text-amber-700"
                                : "bg-emerald-100 text-emerald-700"
                            }`}
                          >
                            {a.is_triggered
                              ? "Triggered"
                              : "Active"}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-500 text-xs">
                          {a.created_at
                            ? new Date(a.created_at).toLocaleDateString()
                            : "--"}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => handleDeleteAlert(a.id)}
                            className="text-xs text-red-600 border border-red-300 rounded px-2.5 py-1 hover:bg-red-600 hover:text-white transition-colors"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>

      {/* Chart modal */}
      {chartTicker && (
        <StockChart
          ticker={chartTicker}
          onClose={() => setChartTicker(null)}
        />
      )}
    </div>
  );
}
