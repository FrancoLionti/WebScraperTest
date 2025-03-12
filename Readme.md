WebScraperTest 

Medidas de seguridad tomadas:

### 1. Ejecutar en una Máquina Virtual

1. **Instalar un hipervisor**:
   - VirtualBox (gratuito): https://www.virtualbox.org/
   - VMware Workstation Player (gratuito para uso personal)

2. **Crear una VM con Linux**:
   - Ubuntu o Kali Linux son buenas opciones
   - Configura la VM con recursos limitados (no necesitas mucho)
   - **Importante**: Configura la red en modo "NAT" o "Host-only" para mayor seguridad

3. **Instalar Python y dependencias**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   pip3 install selenium beautifulsoup4 requests
   ```

4. **Instalar Chrome/Chromium y Chromedriver**:
   ```bash
   sudo apt install chromium-browser
   sudo apt install chromium-chromedriver
   ```

5. **Copiar el script** a la máquina virtual y ejecútalo:
   ```bash
   python3 crypto_scam_scraper.py
   ```


### Medidas adicionales de seguridad

Para maximizar la protección contra sitios hostiles:

1. Máquina virtual dedicada
2. Red configurada en modo aislado o NAT
3. VPN dentro de la VM
4. Ejecutar el código desde ahí
