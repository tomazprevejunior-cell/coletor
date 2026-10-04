# Coletor de Acesso

Flask minimalista pra registrar cliques no link do PDF.

- `GET /track?id=REL-XXX` → registra IP, UA, idioma, GeoIP, e exibe página que pede geolocalização do navegador
- `POST /geo` → recebe lat/lon enviada pelo JS
- `GET /log` → mostra tudo que foi registrado

## Subir no Render.com (sem cartão)

1. Sobe este dir pro GitHub (git init, add, commit, push)
2. render.com → Sign up with GitHub → New Web Service → conecta o repo
3. Render detecta Python, instala requirements, roda Procfile
4. URL fica tipo `https://coletor-acesso.onrender.com`

## Subir no Fly.io (precisa cartão)

```
fly launch --no-deploy
fly deploy
```

## Testar local

```
pip install -r requirements.txt
python app.py
# abre http://localhost:8080/track?id=teste
```