# fastbio
## 🚀 Instalación Rápida

### 1. Clonar Repositorio
```bash
git clone https://github.com/MiltonDanielhch/fastbio.git
cd fastbio

2. Configurar Entorno Virtual (Windows)
cmd
python -m venv venv
.\venv\Scripts\activate

3. Instalar Dependencias
cmd
pip install --upgrade pip
pip install -r requirements.txt

4. Configurar Variables de Entorno
Crear archivo .env:

env
API_KEY=tu_api_key_secreta
KNOWN_DEVICES=192.168.1.100,192.168.1.101
MAX_WORKERS=10
DEVICE_TIMEOUT=5

5. Iniciar Servidor
cmd
python run.py
o iniciar con 
uvicorn app.main:app --reload

Endpoints Clave
Endpoint	Método	Descripción
/devices/{ip}/attendance	GET	Obtiene registros de asistencia