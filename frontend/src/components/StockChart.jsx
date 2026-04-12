import { useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { getStockHistory } from "../services/api";

const PERIODS = [
  { label: "1W", value: "1w" },
  { label: "1M", value: "1mo" },
  { label: "3M", value: "3mo" },
  { label: "1Y", value: "1y" },
];

export default function StockChart({ ticker, initialPeriod = "1mo", onClose }) {
  const [period, setPeriod] = useState(initialPeriod);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getStockHistory(ticker, period)
      .then((res) => {
        if (!cancelled) {
          setData(res.history || res);
        }
      })
      .catch(() => {
        if (!cancelled) setData([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [ticker, period]);

  const first = data.length > 0 ? data[0].close : 0;
  const last = data.length > 0 ? data[data.length - 1].close : 0;
  const color = last >= first ? "#10b981" : "#ef4444";
  const fillColor = last >= first ? "#10b98133" : "#ef444433";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-[#1a1a2e]">{ticker}</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            &times;
          </button>
        </div>

        <div className="flex gap-2 mb-4">
          {PERIODS.map((p) => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                period === p.value
                  ? "bg-[#1a1a2e] text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="h-[200px] flex items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#1a1a2e] border-t-transparent" />
          </div>
        ) : data.length === 0 ? (
          <div className="h-[200px] flex items-center justify-center text-gray-400 text-sm">
            No data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data}>
              <defs>
                <linearGradient id={`grad-${ticker}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                width={60}
                tickFormatter={(v) => `$${v.toFixed(0)}`}
              />
              <Tooltip
                isAnimationActive={false}
                animationDuration={0}
                contentStyle={{
                  fontSize: 12,
                  borderRadius: 8,
                  border: "none",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.12)",
                }}
                formatter={(value) => [`$${Number(value).toFixed(2)}`, "Close"]}
                labelFormatter={(label) => label}
              />
              <Area
                type="monotone"
                dataKey="close"
                stroke={color}
                strokeWidth={2}
                fill={`url(#grad-${ticker})`}
                dot={false}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
