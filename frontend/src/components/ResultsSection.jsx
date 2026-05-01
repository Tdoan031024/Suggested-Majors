import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts'

function getIcon(item) {
  let s = ''
  if (item.to_hop_phu_hop === true)  s += '✅ '
  else if (item.to_hop_phu_hop === false) s += '⚠️ '
  if (item.thuoc_nhom_mong_muon === true)  s += '🎯'
  else if (item.thuoc_nhom_mong_muon === false) s += '📊'
  return s || '–'
}

const COLORS = ['#1a56db', '#1a56db', '#1a56db', '#3b82f6', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe', '#eff6ff']

export default function ResultsSection({ results, extra }) {
  if (!results || results.length === 0) return null

  const chartData = results.map(r => ({
    name: r.ten_nganh.length > 24 ? r.ten_nganh.slice(0, 23) + '…' : r.ten_nganh,
    pct: Math.round(r.xac_suat * 10) / 10,
  }))

  return (
    <div className="card">
      <div className="results-header">
        <h3>🎯 Kết quả gợi ý ngành</h3>
        <span className="badge badge-blue">{results.length} ngành</span>
      </div>

      {extra && (
        <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          {extra}
        </div>
      )}

      {/* Horizontal bar chart */}
      <ResponsiveContainer width="100%" height={Math.max(160, results.length * 34)}>
        <BarChart data={chartData} layout="vertical"
          margin={{ left: 8, right: 50, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="name" width={170} tick={{ fontSize: 11 }} />
          <Tooltip formatter={v => [`${v}%`, 'Xác suất phù hợp']} />
          <Bar dataKey="pct" radius={4}>
            {chartData.map((_, i) => <Cell key={i} fill={COLORS[i] || '#e0e7ff'} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Detail table */}
      <table className="result-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Ngành học</th>
            <th>Mã ngành</th>
            <th>Xác suất</th>
            <th>Ghi chú</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r, i) => (
            <tr key={r.ma_nganh}>
              <td><strong>{i + 1}</strong></td>
              <td>{r.ten_nganh}</td>
              <td style={{ fontFamily: 'monospace', fontSize: '0.83rem', color: 'var(--text-muted)' }}>
                {r.ma_nganh}
              </td>
              <td>
                <div className="prob-bar-wrap">
                  <div className="prob-bar-bg">
                    <div className="prob-bar-fill" style={{ width: `${r.xac_suat}%` }} />
                  </div>
                  <span className="prob-val">{r.xac_suat.toFixed(1)}%</span>
                </div>
              </td>
              <td style={{ fontSize: '1rem' }}>{getIcon(r)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="legend">
        ✅ Phù hợp tổ hợp &nbsp;|&nbsp; ⚠️ Không mở tổ hợp &nbsp;|&nbsp; 🎯 Thuộc nhóm ưa thích &nbsp;|&nbsp; 📊 Ngoài nhóm
      </p>
    </div>
  )
}
