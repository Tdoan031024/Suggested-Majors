import { useState, useEffect } from 'react'
import { predictHocBa, fetchTohopByGroup, fetchTohop } from '../api/client'
import { useGroups } from '../hooks/useGroups'
import ResultsSection from '../components/ResultsSection'

const HK_NAMES = ['HK1-L10', 'HK2-L10', 'HK1-L11', 'HK2-L11', 'HK1-L12']

const emptyScores = () => Array(5).fill('')

export default function HocBaPage() {
  const { groups } = useGroups()
  const [nguyen_vong, setNguyenVong] = useState('')
  const [tohopList, setTohopList] = useState([])
  const [allTohop, setAllTohop] = useState([])
  const [to_hop, setToHop] = useState('')
  const [mode, setMode] = useState('quick')   // 'quick' | 'detail'
  const [tb, setTb] = useState({ mon1: '', mon2: '', mon3: '' })
  const [scores, setScores] = useState({ mon1: emptyScores(), mon2: emptyScores(), mon3: emptyScores() })
  const [diem_uu_tien, setDiemUuTien] = useState(0)
  const [top_n, setTopN] = useState(10)
  const [monNames, setMonNames] = useState(['Môn 1', 'Môn 2', 'Môn 3'])
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Load all to_hop on mount
  useEffect(() => {
    fetchTohop().then(r => setAllTohop(r.data.to_hop))
  }, [])

  // When nhóm changes, filter to_hop
  useEffect(() => {
    if (!nguyen_vong) {
      setTohopList(allTohop)
      return
    }
    fetchTohopByGroup(nguyen_vong)
      .then(r => setTohopList(r.data.to_hop))
      .catch(() => setTohopList(allTohop))
    setToHop('')
  }, [nguyen_vong, allTohop])

  // Update mon names when to_hop changes
  useEffect(() => {
    if (!to_hop) return
    const found = tohopList.find(t => t.ma === to_hop) || allTohop.find(t => t.ma === to_hop)
    if (found) setMonNames(found.mon)
  }, [to_hop])

  const setScore = (mon, idx, val) => {
    setScores(prev => {
      const arr = [...prev[mon]]
      arr[idx] = val
      return { ...prev, [mon]: arr }
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null); setResults(null)

    let mon1_scores, mon2_scores, mon3_scores

    if (mode === 'quick') {
      const v1 = parseFloat(tb.mon1), v2 = parseFloat(tb.mon2), v3 = parseFloat(tb.mon3)
      if (isNaN(v1) || isNaN(v2) || isNaN(v3)) {
        setError('Nhập đầy đủ điểm TB cho cả 3 môn.')
        setLoading(false); return
      }
      mon1_scores = Array(5).fill(v1)
      mon2_scores = Array(5).fill(v2)
      mon3_scores = Array(5).fill(v3)
    } else {
      mon1_scores = scores.mon1.map(Number)
      mon2_scores = scores.mon2.map(Number)
      mon3_scores = scores.mon3.map(Number)
      if ([...mon1_scores, ...mon2_scores, ...mon3_scores].some(isNaN)) {
        setError('Nhập đầy đủ điểm cho tất cả 15 ô (5 HK × 3 môn).')
        setLoading(false); return
      }
    }

    try {
      const res = await predictHocBa({
        to_hop, mon1_scores, mon2_scores, mon3_scores,
        diem_uu_tien: Number(diem_uu_tien),
        nguyen_vong: nguyen_vong || null,
        top_n: Number(top_n),
      })
      const d = res.data
      setResults({ items: d.ket_qua, diem_hb: d.diem_hb, diem_xt: d.diem_xet_tuyen, diem_tb_mon: d.diem_tb_mon })
    } catch (err) {
      setError(err.response?.data?.detail || 'Lỗi kết nối API.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-wrapper">
      <h1 className="page-title">📚 Gợi ý ngành – Học bạ THPT</h1>
      <p className="page-subtitle">Xét tuyển dựa trên điểm TB 5 học kỳ theo tổ hợp môn</p>

      <form onSubmit={handleSubmit}>
        {/* Step 1: Chọn nhóm & tổ hợp */}
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
              <label>Tổ hợp xét tuyển <span style={{ color: 'var(--danger)' }}>*</span></label>
              <select value={to_hop} onChange={e => setToHop(e.target.value)} required>
                <option value="">– Chọn tổ hợp –</option>
                {tohopList.map(t => (
                  <option key={t.ma} value={t.ma}>{t.ma} ({t.mon.join(' – ')})</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Step 2: Nhập điểm */}
        <div className="card">
          <div className="card-title">
            ② Nhập điểm 3 môn &nbsp;
            <button type="button"
              className="btn btn-outline"
              style={{ padding: '0.25rem 0.75rem', fontSize: '0.82rem' }}
              onClick={() => setMode(m => m === 'quick' ? 'detail' : 'quick')}>
              {mode === 'quick' ? '📋 Nhập chi tiết 5 HK' : '⚡ Nhập nhanh (TB)'}
            </button>
          </div>

          {mode === 'quick' ? (
            <div className="form-grid">
              {['mon1', 'mon2', 'mon3'].map((k, i) => (
                <div className="form-group" key={k}>
                  <label>TB {monNames[i] || `Môn ${i + 1}`} (thang 10)</label>
                  <input type="number" min={0} max={10} step={0.01}
                    placeholder="VD: 8.5"
                    value={tb[k]} onChange={e => setTb(p => ({ ...p, [k]: e.target.value }))} />
                  <span className="hint">Trung bình 5 học kỳ</span>
                </div>
              ))}
            </div>
          ) : (
            <div>
              <div className="hk-labels" style={{ marginLeft: '120px' }}>
                {HK_NAMES.map(s => <span key={s}>{s}</span>)}
              </div>
              {['mon1', 'mon2', 'mon3'].map((k, i) => (
                <div className="mon-section" key={k} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', marginTop: '0.5rem' }}>
                  <span className="mon-label" style={{ minWidth: '112px', paddingTop: '0.4rem' }}>
                    {monNames[i] || `Môn ${i + 1}`}
                  </span>
                  <div className="hk-grid" style={{ flex: 1 }}>
                    {scores[k].map((v, j) => (
                      <input key={j} type="number" min={0} max={10} step={0.1}
                        value={v} placeholder="–"
                        onChange={e => setScore(k, j, e.target.value)} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Step 3: Điểm ưu tiên & cài đặt */}
        <div className="card">
          <div className="card-title">③ Điểm ưu tiên & cài đặt</div>
          <div className="form-grid">
            <div className="form-group">
              <label>Điểm ưu tiên KV + ĐT (0–3.5)</label>
              <input type="number" min={0} max={3.5} step={0.25}
                value={diem_uu_tien} onChange={e => setDiemUuTien(e.target.value)} />
              <span className="hint">Cộng vào điểm học bạ cuối cùng</span>
            </div>
            <div className="form-group">
              <label>Số ngành hiển thị</label>
              <select value={top_n} onChange={e => setTopN(e.target.value)}>
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
            <div className="card-title">📊 Tóm tắt điểm</div>
            <div className="form-grid">
              <div>Điểm học bạ (thang 30): <strong>{results.diem_hb?.toFixed(2)}</strong></div>
              <div>Điểm xét tuyển: <strong>{results.diem_xt?.toFixed(2)}</strong></div>
              {results.diem_tb_mon && (
                <>
                  <div>TB Môn 1: <strong>{results.diem_tb_mon.mon1?.toFixed(2)}</strong></div>
                  <div>TB Môn 2: <strong>{results.diem_tb_mon.mon2?.toFixed(2)}</strong></div>
                  <div>TB Môn 3: <strong>{results.diem_tb_mon.mon3?.toFixed(2)}</strong></div>
                </>
              )}
            </div>
          </div>
          <ResultsSection results={results.items} />
        </>
      )}
    </div>
  )
}
