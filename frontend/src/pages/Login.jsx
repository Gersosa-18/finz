// frontend/src/pages/Login.jsx
import {useContext, useState} from 'react';
import {AuthContext} from '../context/AuthContext';
import {useNavigate} from 'react-router-dom';
import {api} from '../services/api';
import styles from './Login.module.css';

function Login() {
    const {login} = useContext(AuthContext);
    const [correo, setCorreo] = useState('');
    const [contrasena, setContrasena] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
          const data = await api.post('/login', {
             correo, contrasena
             });
          if (data.access_token) {
            login(data.access_token);
            navigate('/dashboard');
          } else {
            alert('Credenciales incorrectas');
          }
        } catch (error) {
          alert('Error de conexión')
        }
    };

    return (
    <div className={styles.loginPage}>
      <h2>Iniciar sesión</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={correo}
          onChange={e => setCorreo(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Contraseña"
          value={contrasena}
          onChange={e => setContrasena(e.target.value)}
          required
        />
        <button type="submit">Ingresar</button>
      </form>
    </div>
    );
}

export default Login