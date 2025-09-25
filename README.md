# VideoStore - Exemplo de site para vender vídeos

**O que está incluído**
- Flask app (app.py)
- SQLite database (store.db) com seeds de vendedores e produtos
- Templates Bootstrap para páginas: home, produto, vendedor, carrinho, checkout success
- Integração com Stripe Checkout (endpoint criado; você precisa fornecer suas chaves)
- Procfile e requirements.txt para deploy no Render / Heroku
- Pasta `videos/` onde você deve colocar seus arquivos .mp4
- Instruções para configuração

**Como usar (resumo)**
1. Clone ou envie este projeto para o GitHub.
2. No Render (ou outro), configure as variáveis de ambiente:
   - `FLASK_SECRET_KEY` => segredo do Flask
   - `STRIPE_SECRET_KEY` => sua chave secreta Stripe (começa com sk_live_ ou sk_test_)
3. Adicione seus arquivos .mp4 na pasta `videos/` com os nomes usados no banco (sample1.mp4, sample2.mp4, sample3.mp4) ou atualize `store.db`/`schema.sql`.
4. Deploy no Render: criar um novo Web Service apontando para o repositório. Build Command: `pip install -r requirements.txt`. Start Command: `gunicorn app:app`
5. Importante: marque os segredos no painel do Render (não os suba ao GitHub).

**Observações**
- Este é um projeto de exemplo capaz de ser usado como base. Em produção você deverá:
  - Servir vídeos por CDN ou storage (S3, Cloudflare R2) e proteger URLs.
  - Implementar webhooks Stripe para validar pagamentos e liberar downloads.
  - Implementar contas de usuário, área de compras, painéis de vendedor, upload seguro.
  - Não commit suas chaves secretas.
