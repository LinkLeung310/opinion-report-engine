# PostgreSQL fixtures

The fixture database is synthetic, deterministic, and safe to publish. Start it with:

The seed contains a 12-record `bilibili-dislike` report cohort and a separate
8-record `legacy-feed-controls` historical cohort used only for deterministic
benchmark integration tests. Neither cohort represents production or real historical data.

```powershell
docker compose -f fixtures\docker-compose.yml up -d --wait
```

Run the integration tests from the repository root:

```powershell
$env:PG_DSN='postgresql://report:report_local_only@localhost:55432/opinion_fixture'
.\.venv\Scripts\python.exe -m pytest -m integration
```

To re-import the seed files after changing them:

```powershell
docker compose -f fixtures\docker-compose.yml down -v
docker compose -f fixtures\docker-compose.yml up -d --wait
```
