# PostgreSQL fixtures

The fixture database is synthetic, deterministic, and safe to publish. Start it with:

```powershell
docker compose up -d --wait
```

Run the integration tests from the repository root:

```powershell
$env:PG_DSN='postgresql://report:report_local_only@localhost:55432/opinion_fixture'
.\.venv\Scripts\python.exe -m pytest -m integration
```

To re-import the seed files after changing them:

```powershell
docker compose down -v
docker compose up -d --wait
```
