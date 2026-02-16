# Snowflake Connection Guide — Improvado Project

## 1. Overview

This document details how the Snowflake CLI (`snow`) connection was established for this project, including installation, configuration, troubleshooting, and verified connection details.

---

## 2. Snowflake CLI Installation

**Tool:** Snowflake CLI (not the older SnowSQL)
**Version installed:** v3.15.0
**Command used:**

```bash
brew install snowflake-cli
```

This installs the `snow` command (not `snowsql`). Verify installation:

```bash
snow --version
# Output: Snowflake CLI v3.15.0

snow --help
# Lists all available subcommands: app, auth, connection, sql, stage, etc.
```

### Key Difference: `snow` vs `snowsql`

| Feature | `snow` (Snowflake CLI) | `snowsql` (SnowSQL) |
|---|---|---|
| Install | `brew install snowflake-cli` | `brew install --cask snowflake-snowsql` |
| Command | `snow` | `snowsql` |
| Config format | `config.toml` | `~/.snowsql/config` (INI format) |
| Run SQL files | `snow sql -f file.sql` | `snowsql -f file.sql` |
| Config flag | `--config-file` (global, before subcommand) | `-c` connection name |

---

## 3. Configuration File

### 3.1 Default Config Location

The default config path (found via `snow --info`):

```
/Users/rachanasamboju/Library/Application Support/snowflake/config.toml
```

### 3.2 Project-Local Config (Used in This Project)

We chose to keep the config inside the project repo instead of the default location:

```
/Users/rachanasamboju/Documents/Improvado_project/config.toml
```

### 3.3 Config File Contents

```toml
[connections.improvado]
account = "HXCASFX-GZ76381"
user = "SAMBOJURACHANA"
password = "<PAT_TOKEN>"
warehouse = "COMPUTE_WH"
database = "IMPROVADO_ADS"
schema = "RAW"
role = "ACCOUNTADMIN"
```

### 3.4 Connection Parameters Explained

| Parameter | Value | Description |
|---|---|---|
| `account` | `HXCASFX-GZ76381` | Snowflake account identifier (org-account format) |
| `user` | `SAMBOJURACHANA` | Snowflake username |
| `password` | *(PAT token)* | Programmatic Access Token used in place of password |
| `warehouse` | `COMPUTE_WH` | Compute warehouse for running queries |
| `database` | `IMPROVADO_ADS` | Target database (created by setup script) |
| `schema` | `RAW` | Default schema for raw source tables |
| `role` | `ACCOUNTADMIN` | Role with full privileges |

### 3.5 Authentication Method — PAT (Programmatic Access Token)

- The PAT token is stored in: `/Users/rachanasamboju/Documents/Improvado_project/snow_pat.txt`
- PAT is used in place of a regular password in the `password` field
- **No special `authenticator` field is needed** — the default authenticator works with PAT
- Setting `authenticator = "SNOWFLAKE_JWT"` does NOT work with PAT (that expects an RSA private key)

### 3.6 File Permissions Requirement

Snowflake CLI requires the config file to have restricted permissions:

```bash
chmod 0600 /Users/rachanasamboju/Documents/Improvado_project/config.toml
```

Without this, you get:
```
UserWarning: Bad owner or permissions on config.toml.
```

---

## 4. How to Use the Project-Local Config

Since the config is not in the default location, you must pass `--config-file` as a **global option** (before the subcommand):

```bash
# Correct — global flag BEFORE subcommand
snow --config-file /Users/rachanasamboju/Documents/Improvado_project/config.toml sql -q "SELECT 1;" -c improvado

# Wrong — flag AFTER subcommand (will error)
snow sql --config-file /Users/rachanasamboju/Documents/Improvado_project/config.toml -q "SELECT 1;" -c improvado
```

The `-c improvado` flag references the `[connections.improvado]` section in the config.

---

## 5. Connection Test

### 5.1 Test Command

```bash
snow --config-file /Users/rachanasamboju/Documents/Improvado_project/config.toml connection test -c improvado
```

### 5.2 Simple Query Test

Since `IMPROVADO_ADS` database doesn't exist before running setup, test with overridden empty database/schema:

```bash
snow --config-file /Users/rachanasamboju/Documents/Improvado_project/config.toml \
  sql -q "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE();" \
  -c improvado --database "" --schema ""
```

### 5.3 Verified Output

```
+-------------------------------------------------------+
| CURRENT_USER() | CURRENT_ROLE() | CURRENT_WAREHOUSE() |
|----------------+----------------+---------------------|
| SAMBOJURACHANA | ACCOUNTADMIN   | COMPUTE_WH          |
+-------------------------------------------------------+
```

---

## 6. Troubleshooting Log

### Issue 1: `--config-file` placement

**Error:**
```
No such option: --config-file
```

**Cause:** `--config-file` is a global option and must appear before the subcommand.
**Fix:** `snow --config-file <path> <subcommand>` not `snow <subcommand> --config-file <path>`

### Issue 2: File permissions

**Error:**
```
UserWarning: Bad owner or permissions on config.toml
```

**Fix:**
```bash
chmod 0600 config.toml
```

### Issue 3: Wrong authenticator for PAT

**Error:**
```
Expected bytes or RSAPrivateKey, got <class 'NoneType'>
```

**Cause:** Used `authenticator = "SNOWFLAKE_JWT"` which expects an RSA private key file, not a PAT token.
**Fix:** Remove the `authenticator` line entirely. PAT works with the default password authenticator.

### Issue 4: Network policy

**Error:**
```
Failed to connect to DB: HXCASFX-GZ76381.snowflakecomputing.com:443. Network policy is required.
```

**Cause:** Snowflake account has a network policy restricting allowed IP addresses.
**Fix:** Add your current IP to the allowed list in Snowflake UI: Admin > Security > Network Policies.

### Issue 5: Database does not exist

**Error:**
```
Could not use database "IMPROVADO_ADS". Object does not exist.
```

**Cause:** The database hasn't been created yet — this is expected before running `01_setup.sql`.
**Fix:** Not an error. Connection itself is valid. Database will be created by the setup script.

---

## 7. Running SQL Scripts

Use the `snow sql` command with `-f` flag to execute SQL files:

```bash
# Setup — create database, schemas, tables
snow --config-file /Users/rachanasamboju/Documents/Improvado_project/config.toml \
  sql -f /Users/rachanasamboju/Documents/Improvado_project/01_setup.sql \
  -c improvado --database "" --schema ""

# Load data — PUT + COPY INTO
snow --config-file /Users/rachanasamboju/Documents/Improvado_project/config.toml \
  sql -f /Users/rachanasamboju/Documents/Improvado_project/02_load_data.sql \
  -c improvado

# Unified model — create analytics table
snow --config-file /Users/rachanasamboju/Documents/Improvado_project/config.toml \
  sql -f /Users/rachanasamboju/Documents/Improvado_project/03_unified_model.sql \
  -c improvado
```

### Running Ad-hoc Queries

```bash
# Inline query
snow --config-file /Users/rachanasamboju/Documents/Improvado_project/config.toml \
  sql -q "SELECT COUNT(*) FROM RAW.FACEBOOK_ADS;" -c improvado

# Interactive mode
snow --config-file /Users/rachanasamboju/Documents/Improvado_project/config.toml \
  sql -c improvado
# Opens a REPL — type SQL, end with semicolon, type 'exit' to quit
```

---

## 8. Quick Reference

| Action | Command |
|---|---|
| Check CLI version | `snow --version` |
| Check CLI info & config path | `snow --info` |
| List connections | `snow --config-file config.toml connection list` |
| Test connection | `snow --config-file config.toml connection test -c improvado` |
| Run SQL query | `snow --config-file config.toml sql -q "SELECT 1;" -c improvado` |
| Run SQL file | `snow --config-file config.toml sql -f script.sql -c improvado` |
| Run multiple files | `snow --config-file config.toml sql -f a.sql -f b.sql -c improvado` |
| Interactive mode | `snow --config-file config.toml sql -c improvado` |
| Debug mode | Add `--debug` after `snow` for verbose logging |

---

## 9. Project Files Summary

| File | Purpose |
|---|---|
| `config.toml` | Snowflake CLI connection config (PAT auth) |
| `snow_pat.txt` | Programmatic Access Token (keep secret) |
| `01_setup.sql` | Creates database, schemas, staging tables, file format |
| `02_load_data.sql` | Loads CSV data into Snowflake via PUT + COPY INTO |
| `03_unified_model.sql` | Creates unified cross-platform analytics table |
| `snowflake_connection_guide.md` | This file |

---

*Last verified: 2026-02-13 | CLI version: v3.15.0 | Connection: SAMBOJURACHANA@HXCASFX-GZ76381*
