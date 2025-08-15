import styles from './Dashboard.module.css';

function Dashboard() {
  return (
    <div className={styles.dashboard}>
      <h1>Bienvenido, German</h1>
      
      <div className={styles.summary}>
        <h2>Resumen general</h2>
        <p>Activos seguidos: 5</p>
        <p>Alertas activas: 3</p>
        <p>Última alerta: TSLA cayó 7%</p>
        <p>Último análisis de sentimiento: AAPL positivo (0,78)</p>
      </div>

      <div className={styles.widgets}>
        <div className={styles.card}>Sentimiento actual por activo</div>
        <div className={styles.card}>Alertas configuradas</div>
        <div className={styles.card}>Calendario eventos macro</div>
      </div>
    </div>
  );
}

export default Dashboard;