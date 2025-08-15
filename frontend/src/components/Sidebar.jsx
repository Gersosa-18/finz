import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Bell,
  Heart
  // Calendar,
  // FileText,
  // MessageCircle,
  // Settings
} from 'lucide-react';
import styles from './Sidebar.module.css';

function Sidebar() {
  const menuItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/alertas', icon: Bell, label: 'Alertas' },
    { path: '/analisis', icon: Heart, label: 'Análisis de Sentimiento' }
    // { path: '/eventos-macro', icon: Calendar, label: 'Eventos macro' },
    // { path: '/reportes', icon: FileText, label: 'Reportes' },
    // { path: '/chatbot', icon: MessageCircle, label: 'Chatbot' },
    // { path: '/configuracion', icon: Settings, label: 'Configuración' }
  ];

  return (
    <aside className={styles.sidebar}>
      <div className={styles.logoSection}>
        <img src="/logo.png" alt="Finz Logo" className={styles.logo} />
        <span className={styles.brandName}>Finz</span>
      </div>
      
      <nav className={styles.nav}>
        {menuItems.map((item, index) => (
          <NavLink
            key={index}
            to={item.path}
            className={({ isActive }) => 
              `${styles.navItem} ${isActive ? styles.active : ''}`
            }
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;