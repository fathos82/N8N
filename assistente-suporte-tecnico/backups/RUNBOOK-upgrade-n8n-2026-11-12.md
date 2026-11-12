# Upgrade n8n — 2026-11-12

## O que foi feito
- n8n `2.4.7` → `2.47.5` (imagem fixada em `n8nio/n8n:2.47.5`)
- `N8N_SECURE_COOKIE=true`
- Removida a publicação da porta `5678` no host (acesso só via Traefik/HTTPS)
- Backup do banco e do volume criados e verificados antes do deploy

## Backups
| Item | Local | Quando | Tamanho |
|---|---|---|---|
| Dump Postgres `n8n_db` | GCS `practium-n8ndb-ug7hmq/backups_n8n/2026-11-12T19-17-06-003Z.sql.gz` | 2026-11-12 19:17 | 81 MB |
| Volume `n8n_data` | GCS `practium-n8n-oylwyy_n8n/backups_n8n_volume/practium-n8n-oylwyy_n8n_data-2026-11-12T19-17-54-170Z.tar` | 2026-11-12 19:17 | 63 MB |

- Backup automático do banco: diário às 00:00 (já existia).
- Backup automático do volume: diário às 01:00, retenção 7 (criado neste upgrade).

## Rollback (se necessário)
1. No Dokploy → serviço `n8n` (compose `R_u-1prKe-_bqaal25oth`), trocar a imagem para `n8nio/n8n:2.4.7`.
2. **Restaurar o banco** pelo Dokploy (UI → Postgres `n8n_db` → Backups → Restore) usando o dump de `2026-11-12T19-17-06-003Z`.
   - Necessário porque as migrações de schema do n8n 2.47.5 não são reversíveis.
3. Se preciso, restaurar o volume `n8n_data` a partir do `.tar` no GCS.
4. Redeploy do compose.

## Observações
- `n8nio/n8n:2.47.5` foi publicado em 2026-11-12 08:29 UTC.
- Avisos de depreciação no boot (não bloqueantes): task runner interno e renomeação de `binaryData` → `storage` no n8n v3.
