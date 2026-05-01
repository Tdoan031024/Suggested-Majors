import { useState } from 'react'
import { predictDGNL } from '../api/client'
import { useGroups } from '../hooks/useGroups'
import ResultsSection from '../components/ResultsSection'

export default function DGNLPage() {
  const { groups } = useGroups()
  const [form, setForm] = useState({
    diem_dgnl: 800, diem_dt: 0, diem_kv: 0,
    thu_tu_nv: 1, nguyen_vong: '', top_n: 10,
  })
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null); setResults(null)
    try {
      const payload = {
        ...form,
        diem_dgnl: Number(form.diem_dgnl),
        diem_dt: Number(form.diem_dt),
        diem_kv: Number(form.diem_kv),
        thu_tu_nv: Number(form.thu_tu_nv),
        top_n: Number(form.top_n),
        nguyen_vong: form.nguyen_vong || null,
      }
      const res = await predictDGNL(payload)
      setResults(res.data.ket_qua)
    } catch (err) {
      setError(err.response?.data?.detail || 'Lỗi kết nối API. Kiểm tra backend đang chạy.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-wrapper">
      <h1 className="page-title">🧠 Gợi ý ngành – Phương thức DGNL</h1>
      <p className="page-subtitle">Đánh giá năng lực (tổng điểm 600–1200)</p>

      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="card-title">📊 Nhập điểm DGNL</div>

          <div className="form-group slider-wrap" style={{ marginBottom: '1.25rem' }}>
            <label>Tổng điểm DGNL</label>
            <div className="slider-row">
              <input type="range" min={600} max={1200} step={5}
                value={form.diem_dgnl} onChange={e => set('diem_dgnl', e.target.value)} />
              <span className="slider-val">{form.diem_dgnl}</span>
            </div>
            <span className="hint">Thang điểm 600 – 1200</span>
          </div>

          <div className="form-grid">
            <div className="form-group">
              <label>Điểm ưu tiên đối tượng (ĐT)</label>
              <select value={form.diem_dt} onChange={e => set('diem_dt', e.target.value)}>
                <option value={0}>0 – Không có</option>
                <option value={1}>1 – Nhóm 1 (UT01)</option>
                <option value={0.5}>0.5 – Nhóm 2 (UT02)</option>
              </select>
            </div>
            <div className="form-group">
              <label>Điểm ưu tiên khu vực (KV)</label>
              <select value={form.diem_kv} onChange={e => set('diem_kv', e.target.value)}>
                <option value={0}>0 – KV1 (không ưu tiên)</option>
                <option value={0.25}>0.25 – KV2</option>
                <option value={0.5}>0.5 – KV2-NT</option>
                <option value={0.75}>0.75 – KV3</option>
              </select>
            </div>
            <div className="form-group">
              <label>Thứ tự nguyện vọng</label>
              <select value={form.thu_tu_nv} onChange={e => set('thu_tu_nv', e.target.value)}>
                {[1,2,3,4,5].map(n => <option key={n} value={n}>NV{n}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Nhóm ngành ưa thích (tùy chọn)</label>
              <select value={form.nguyen_vong} onChange={e => set('nguyen_vong', e.target.value)}>
                <option value="">– Tất cả nhóm –</option>
                {groups.map(g => <option key={g.ten_nhom} value={g.ten_nhom}>{g.ten_nhom}</option>)}
              </select>
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
