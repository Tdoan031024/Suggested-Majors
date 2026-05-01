import { useState, useEffect } from 'react'
import { predictTHPT, fetchTohopByGroup, fetchTohop } from '../api/client'
import { useGroups } from '../hooks/useGroups'
import ResultsSection from '../components/ResultsSection'

export default function THPTPage() {
  const { groups } = useGroups()
  const [nguyen_vong, setNguyenVong] = useState('')
  const [tohopList, setTohopList] = useState([])
  const [allTohop, setAllTohop] = useState([])
  const [to_hop, setToHop] = useState('')
  const [monNames, setMonNames] = useState(['Môn 1', 'Môn 2', 'Môn 3'])
  const [form, setForm] = useState({
    mon1: '', mon2: '', mon3: '', diem_ut: 0, thu_tu_nv: 1, top_n: 10
  })
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchTohop().then(r => setAllTohop(r.data.to_hop))
  }, [])

  useEffect(() => {
    if (!nguyen_vong) { setTohopList(allTohop); return }
    fetchTohopByGroup(nguyen_vong)
      .then(r => setTohopList(r.data.to_hop))
      .catch(() => setTohopList(allTohop))
    setToHop('')
  }, [nguyen_vong, allTohop])

  useEffect(() => {
    if (!to_hop) return
    const found = tohopList.find(t => t.ma === to_hop) || allTohop.find(t => t.ma === to_hop)
    if (found) setMonNames(found.mon)
  }, [to_hop])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const tong = () => {
    const s = [form.mon1, form.mon2, form.mon3].map(Number)
    return s.every(v => !isNaN(v) && v >= 0) ? (s.reduce((a, b) => a + b, 0) + Number(form.diem_ut)).toFixed(2) : '–'
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null); setResults(null)
    try {
      const res = await predictTHPT({
        mon1: Number(form.mon1),
        mon2: Number(form.mon2),
        mon3: Number(form.mon3),
        diem_ut: Number(form.diem_ut),
        thu_tu_nv: Number(form.thu_tu_nv),
        tohop: to_hop || null,
        nguyen_vong: nguyen_vong || null,
        top_n: Number(form.top_n),
      })
      setResults({ items: res.data.ket_qua, tong: res.data.tong_diem })
    } catch (err) {
      setError(err.response?.data?.detail || 'Lỗi kết nối API.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-wrapper">
      <h1 className="page-title">📝 Gợi ý ngành – PT1 (Điểm thi THPT)</h1>
      <p className="page-subtitle">Xét tuyển theo kết quả thi THPT 2025</p>

      <form onSubmit={handleSubmit}>
        {/* Step 1: Nhóm & tổ hợp */}
        <div className="card">
          <div className="card-title">① Chọn nhóm ngành & tổ hợp môn</div>
          <div className="form-grid">
            <div className="form-group">
              <label>Nhóm ngành ưa thích (tùy chọn)</label>
              <select value={nguyen_vong} onChange={e => setNguyenVong(e.target.value)}>
                <option value="">– Tất cả nhóm –</option>
                {groups.map(g => <option key={g.ten_nhom} value={g.ten_nhom}>{g.ten_nhom}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Tổ hợp xét tuyển</label>
              <select value={to_hop} onChange={e => setToHop(e.target.value)}>
                <option value="">– Tất cả tổ hợp –</option>
                {tohopList.map(t => (
                  <option key={t.ma} value={t.ma}>{t.ma} ({t.mon.join(' – ')})</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Step 2: Điểm 3 môn */}
        <div className="card">
          <div className="card-title">② Nhập điểm thi 3 môn</div>
          <div className="form-grid">
            {['mon1', 'mon2', 'mon3'].map((k, i) => (
              <div className="form-group" key={k}>
                <label>{monNames[i] || `Môn ${i + 1}`} (0–10)</label>
                <input type="number" min={0} max={10} step={0.05}
                  placeholder="VD: 8.0"
                  value={form[k]} onChange={e => set(k, e.target.value)} required />
              </div>
            ))}
          </div>

          {/* Tổng điểm live */}
          <div style={{ marginTop: '0.75rem', padding: '0.65rem 1rem', background: 'var(--primary-light)', borderRadius: '8px', fontSize: '0.92rem' }}>
            Tổng điểm dự kiến (3 môn + ưu tiên): &nbsp;
            <strong style={{ color: 'var(--primary)', fontSize: '1.05rem' }}>{tong()}</strong>
          </div>
        </div>

        {/* Step 3: Ưu tiên & cài đặt */}
        <div className="card">
          <div className="card-title">③ Điểm ưu tiên & nguyện vọng</div>
          <div className="form-grid">
            <div className="form-group">
              <label>Điểm ưu tiên KV + ĐT (0–3.5)</label>
              <input type="number" min={0} max={3.5} step={0.25}
                value={form.diem_ut} onChange={e => set('diem_ut', e.target.value)} />
            </div>
            <div className="form-group">
              <label>Thứ tự nguyện vọng</label>
              <select value={form.thu_tu_nv} onChange={e => set('thu_tu_nv', e.target.value)}>
                {[1,2,3,4,5].map(n => <option key={n} value={n}>Nguyện vọng {n}</option>)}
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

      {results && (
        <>
          <div className="card" style={{ fontSize: '0.9rem' }}>
            Tổng điểm xét tuyển: <strong style={{ color: 'var(--primary)', fontSize: '1.1rem' }}>{results.tong?.toFixed(2)}</strong>
          </div>
          <ResultsSection results={results.items} />
        </>
      )}
    </div>
  )
}
