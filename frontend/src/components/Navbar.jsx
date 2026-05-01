import { NavLink } from 'react-router-dom'

export default function Navbar() {
  const cls = ({ isActive }) => 'nav-link' + (isActive ? ' active' : '')
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="navbar-brand">
          <span>🎓</span> HUIT Advisor
        </NavLink>
        <NavLink to="/dgnl" className={cls}>DGNL</NavLink>
        <NavLink to="/hocba" className={cls}>Học bạ</NavLink>
        <NavLink to="/tuyenthang" className={cls}>Tuyển thẳng</NavLink>
        <NavLink to="/thpt" className={cls}>PT1 – THPT</NavLink>
      </div>
    </nav>
  )
}
