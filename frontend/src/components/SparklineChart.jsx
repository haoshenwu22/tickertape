import { LineChart, Line } from "recharts";

export default function SparklineChart({ data, onClick }) {
  if (!data || data.length < 2) {
    return <div className="w-[100px] h-[30px] bg-gray-100 rounded" />;
  }

  const first = data[0].close;
  const last = data[data.length - 1].close;
  const color = last >= first ? "#10b981" : "#ef4444";

  return (
    <div
      className="cursor-pointer inline-block"
      onClick={onClick}
      title="Click to expand chart"
    >
      <LineChart width={100} height={30} data={data}>
        <Line
          type="monotone"
          dataKey="close"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </div>
  );
}
