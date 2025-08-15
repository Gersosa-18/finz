import styles from './Alertas.module.css';

function Alertas() {
  return (
    <div className={styles.alertas}>
        <h1>Alertas financieras</h1>
        <button className={styles.newAlertBtn}>+ Nueva alerta</button>
        
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Tipo</th>
            <th>Descripción</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>TSLA</td>
            <td>Simple</td>
            <td>precio &gt; 800</td>
            <td>
              <button>✏️</button>
              <button>🗑️</button>
            </td>
          </tr>
          <tr>
            <td>BTC</td>
            <td>Rango</td>
            <td>precio entre 30 k y 40 k</td>
            <td>
              <button>✏️</button>
              <button>🗑️</button>
            </td>
          </tr>
          <tr>
            <td>AAPL</td>
            <td>Porcentaje</td>
            <td>cambio &gt; 7 % en 1d</td>
            <td>
              <button>✏️</button>
              <button>🗑️</button>
            </td>
          </tr>
          <tr>
            <td>TSLA</td>
            <td>Compuesta</td>
            <td>(precio &gt; 700 AND volumen &gt; 10M)</td>
            <td>
              <button>✏️</button>
              <button>🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

export default Alertas;