import { useState } from 'react';
import { Bell, Sun, Moon } from 'lucide-react';
import styles from './Header.module.css';

function Header() {
  const [isDarkMode, setIsDarkMode] = useState(false);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    // Aquí después podés agregar la lógica para cambiar el tema global
  };

  return (
    <header className={styles.header}>
      <div className={styles.rightSection}>
        <button className={styles.iconButton}>
          <Bell size={20} color="#333" />
        </button>
        <button className={styles.iconButton} onClick={toggleDarkMode}>
          {isDarkMode ? <Sun size={20} color="#333" /> : <Moon size={20} color="#333" />}
        </button>
        <div className={styles.profile}>
          <div className={styles.avatar}>G</div>
          <span className={styles.userName}>German</span>
        </div>
      </div>
    </header>
  );
}

export default Header;