import { useState } from 'react'
import { predictTuyenThang } from '../api/client'
import { useGroups } from '../hooks/useGroups'
import ResultsSection from '../components/ResultsSection'

export default function TuyenThangPage() {
  const { groups } = useGroups()
  const [form, setForm] = useState({ tb_tong: 26, diem_anh: 0, nguyen_vong: '', top_n: 10 })
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null); setResults(null)
    try {
      const res = await predictTuyenThang({
        tb_tong: Number(form.tb_tong),
        diem_anh: Number(form.diem_anh),
        nguyen_vong: form.nguyen_vong || null,
        top_n: Number(form.top_n),
      })
      setResults(res.data.ket_qua)
    } catch (err) {
      setError(err.response?.data?.detail || 'Lỗi kết nối API.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-wrapper">
      <h1 className="page-title">🏆 Gợi ý ngành – Tuyển thẳng</h1>
      <p className="page-subtitle">Dành cho học sinh có học lực xuất sắc (TB 3 năm ≥ 24/30)</p>

      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="card-title">📊 Nhập thông tin</div>

          <div className="form-group slider-wrap" style={{ marginBottom: '1.25rem' }}>
            <label>Tổng điểm TB 3 năm (thang 30)</label>
            <div className="slider-row">
              <input type="range" min={18} max={30} step={0.1}
                value={form.tb_tong}
                onChange={e => set('tb_tong', e.target.value)} />
              <span className="slider-val">{Number(form.tb_tong).toFixed(1)}</span>
            </div>
            <span className="hint">Tổng điểm TB 3 môn của tổ hợp × 3 năm THPT</span>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label>Điểm Tiếng Anh (0–10)</label>
              <input type="number" min={0} max={10} step={0.1}
                value={form.diem_anh} onChange={e => set('diem_anh', e.target.value)} />
              <span className="hint">≥ 9.0 sẽ được boost nhẹ (+10%)</span>
            </div>
            <div className="form-group">
              <label>Nhóm ngành ưa thích <span style={{ color: 'var(--danger)' }}>*</span></label>
              <select value={form.nguyen_vong} onChange={e => set('nguyen_vong', e.target.value)} required>
                <option value="">– Chọn nhóm ngành –</option>
                {groups.map(g => <option key={g.ten_nhom} value={g.ten_nhom}>{g.ten_nhom}</option>)}
              </select>
              <span className="hint">Chỉ hiển thị ngành trong nhóm đã chọn</span>
            </div>
            <div className="form-group">
              <label>Số ngành hiển thị</label>
              <select value={form.top_n} onChange={e => set('top_n', e.target.value)}>
                {[5,10,15,20].map(n => <option key={n} value={n}>{n} ngành</option>)}
              </select>
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <><span className="spinner" /> Đang tính...</> : '🔍 Gợi ý ngành'}
            </button>
          </div>
          {error && <div className="error-box">❌ {error}</div>}
        </div>
      </form>

      <ResultsSection results={results} />
    </div>
  )
}
