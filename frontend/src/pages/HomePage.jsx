import { Link } from 'react-router-dom'
import { useGroups } from '../hooks/useGroups'

const METHODS = [
  { to: '/dgnl',       icon: '🧠', title: 'DGNL',        desc: 'Đánh giá năng lực – nhập điểm 600–1200' },
  { to: '/hocba',      icon: '📚', title: 'Học bạ',       desc: 'Điểm TB 5 học kỳ THPT theo tổ hợp' },
  { to: '/tuyenthang', icon: '🏆', title: 'Tuyển thẳng',  desc: 'Dành cho học sinh xuất sắc (TB ≥ 24/30)' },
  { to: '/thpt',       icon: '📝', title: 'PT1 – THPT',   desc: 'Điểm thi tốt nghiệp THPT 2025' },
]

export default function HomePage() {
  const { groups, loading, error } = useGroups()

  return (
    <div className="page-wrapper">
      <div className="hero">
        <h1>Hệ thống Gợi ý Hướng nghiệp HUIT</h1>
        <p>
          Sử dụng Machine Learning (Random Forest + Naive Bayes) để tư vấn ngành học
          phù hợp theo 4 phương thức xét tuyển của trường HUIT.
        </p>

        <div className="method-grid">
          {METHODS.map(m => (
            <Link key={m.to} to={m.to} className="method-card">
              <div className="mc-icon">{m.icon}</div>
              <h3>{m.title}</h3>
              <p>{m.desc}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* 9 nhóm ngành */}
      <div className="card">
        <div className="card-title">🗂️ 9 Nhóm ngành đào tạo HUIT</div>
        {loading && <p style={{ color: 'var(--text-muted)' }}>Đang tải...</p>}
        {error && <p className="error-box">{error}</p>}
        {!loading && !error && (
          <div className="group-chips">
            {groups.map(g => (
              <span key={g.ten_nhom} className="group-chip" title={g.nganh.join(', ')}>
                {g.ten_nhom}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="card" style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: 1.8 }}>
        <div className="card-title">⚙️ Về mô hình</div>
        <p>Ensemble: <strong>70% Random Forest + 30% Naive Bayes</strong></p>
        <p>Boost nhóm ưa thích: ×1.8 &nbsp;|&nbsp; Penalty ngoài nhóm: ×0.6</p>
        <p>Boost tổ hợp phù hợp: ×1.15 &nbsp;|&nbsp; Penalty không mở tổ hợp: ×0.35</p>
        <p>Xác suất luôn trong khoảng <strong>[5%, 90%]</strong></p>
      </div>
    </div>
  )
}
